"""GenesisWorld — the persistent in-situ 3D living world.

Every step: each living agent senses (body-frame nearest food + nearest neighbour + own energy),
runs its evolved brain forward, accelerates and moves, pays metabolism, eats food it reaches,
dies of starvation or old age, and — if rich enough — reproduces by splitting its energy and
spawning a MUTATED-brain child in a free slot ADJACENT to itself (kin structure, pre-installed for
later signalling stages). Food regrows on a cap. There is no GA, no fitness function, no scripted
movement: selection is purely in-situ via food scarcity, so competence is *evolved*.

`evolve=False` freezes the genome (children are exact copies, no mutation) — the red-team control:
foraging skill should rise under evolution and stay near the random baseline when frozen.

The world is checkpointable (save/load_checkpoint) and resumable, so it runs unattended for >=1e5
steps. Body parameters are fixed and identical for all agents (the neuro.py discipline), so any gain
is attributable to the brain. Stage 2 (R144) activates an emergent SIGNALLING channel — with
`signalling=True` each prey emits an evolved scalar utterance and hears its nearest neighbour's, so
predator-alarm communication can evolve from scratch (see signal_causal_test + metrics.signal_world_mi).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import numpy as np
from scipy.spatial import cKDTree

from .. import brain
from ..brain import BrainSpec
from ..bigworld3d import _resolve, _sense_kd
from ..coevo3d import _act
from ..evolve3d import _body_frame
from ..world3d import World3D
from . import metrics
from .agents import PopConfig, Population

N_IN = 9   # food body-dir(3)*prox + prox, neighbour body-dir(3)*prox + prox, own energy
N_OUT = 3  # 3D acceleration in the body frame


@dataclass(frozen=True)
class GenesisConfig:
    world: World3D = field(default_factory=lambda: World3D(size=140.0))
    capacity: int = 6000           # hard memory bound (food, not this, limits the population)
    n0: int = 1500
    # food economy — scarce so foraging skill matters (strong in-situ selection)
    food_cap: int = 900
    food_regrow: int = 22
    food_value: float = 26.0
    eat_radius: float = 3.0
    # life
    e_start: float = 60.0
    e_repro: float = 90.0
    e_max: float = 105.0           # can't hoard -> must keep foraging
    base_cost: float = 0.11        # existence costs -> idlers starve
    move_cost: float = 0.05
    max_age: int = 1600            # turnover -> continual selection
    birth_jitter: float = 2.0      # child spawns this close to the parent (kin adjacency)
    # fixed body (identical for all -> any gain is the brain)
    speed: float = 3.0
    force: float = 0.5
    min_speed: float = 0.6
    sense_range: float = 32.0
    # genetics
    mut_rate: float = 0.2
    mut_sigma: float = 0.35
    n_hidden: int = 10
    # food spatial structure: "uniform" (R141 baseline) or "patches" (R142 — clumped food at fixed
    # centers regrowing locally; with kin-adjacent reproduction this makes semi-isolated demes so
    # distinct lineages hold distinct patches -> a spatial mosaic instead of a monoculture sweep)
    food_mode: str = "uniform"
    n_patches: int = 10
    patch_radius: float = 8.0
    # resource partitioning (R142 — break the monoculture): n_food_types>1 splits food into types;
    # each agent has a heritable diet preference and eats/senses only its own type (the trade-off),
    # so distinct food types support distinct specialist lineages = coexisting niches (Gause). n=1
    # is the exact R141 single-resource world (no diet, no extra RNG draws).
    n_food_types: int = 1
    diet_mut_sigma: float = 0.12
    # co-evolutionary predator (R143 — arms race): n_predators0>0 adds a SECOND evolved-neural species
    # that hunts prey. Prey then gain a predator-sense channel (brain n_in 9->13) so they can evolve
    # EVASION; predators sense nearest prey and pursue. n_predators0=0 is the exact R141/R142 prey-only
    # world (prey n_in stays 9, no predator code path, byte-identical).
    n_predators0: int = 0
    pred_capacity: int = 550           # ~0.2x prey (predprey3d's coexistence ratio): low enough not to
                                       # overexploit, high enough to persist as prey evolve evasion
    pred_e_start: float = 140.0
    pred_e_repro: float = 200.0
    pred_e_max: float = 250.0
    pred_base_cost: float = 0.48       # starves without prey, but not faster than it can hunt
    pred_move_cost: float = 0.05
    pred_speed: float = 3.35           # faster than prey (3.0) so the chase is real (predprey3d ratio)
    pred_force: float = 0.34           # ...but less agile -> prey can juke (evasion can pay)
    pred_max_age: int = 2400
    catch_radius: float = 3.5
    prey_energy_value: float = 42.0    # a catch's energy: enough to persist, low conversion = Type-II
    pred_handling: int = 38            # digestion cooldown (Type-II stabilizer)
    # emergent signalling (R144 — Stage 2): signalling=True activates a communication channel — each
    # prey emits a scalar UTTERANCE (an evolved extra brain output) and senses its nearest neighbour's
    # previous-step utterance as a NEW input. Over the existing kin-adjacency this can evolve into
    # honest predator-alarm signalling (Floreano/Mitri kin-selection route). signalling=False keeps the
    # prey brain at its R143 shape, no utterance state, byte-identical.
    signalling: bool = False
    prey_pred_range: float = 0.0       # if >0, prey DIRECT predator-sense range, SHORTER than sense_range
                                       # -> a neighbour closer to the predator can warn earlier (the
                                       # sentinel value that makes an alarm call pay). 0 = full sense_range
                                       # (R143 behaviour, byte-identical).
    signal_bins: int = 4               # quantile bins for the signal-MI read-out
    deaf: bool = False                 # functional control: channel present in the brain but heard is
                                       # forced silent. Compared against signalling=True (intact), this
                                       # is the ARTIFACT-IMMUNE test — does HEARING causally help, holding
                                       # brain shape fixed? (MI alone is fooled by sensory-reaction mimicry.)
    # metric
    persist_steps: int = 200


class GenesisWorld:
    def __init__(self, cfg: GenesisConfig | None = None, seed: int = 0, evolve: bool = True):
        self.cfg = cfg or GenesisConfig()
        self.rng = np.random.default_rng(seed)
        self.evolve = evolve
        self.has_predators = self.cfg.n_predators0 > 0
        self.signalling = self.cfg.signalling
        prey_in = (N_IN + (4 if self.has_predators else 0)   # +nearest-predator sense channel (R143)
                   + (1 if self.signalling else 0))          # +heard-neighbour-utterance channel (R144)
        prey_out = N_OUT + (1 if self.signalling else 0)     # +utterance output (R144); _act ignores it
        self.spec = BrainSpec(n_in=prey_in, n_hidden=self.cfg.n_hidden, n_out=prey_out)
        self.pop = Population(PopConfig(self.cfg.capacity, self.spec.n_weights))
        self.step_count = 0
        self.lineage_first_step: dict[int, int] = {}
        self._seed_population()
        w = self.cfg.world
        self.patch_centers = None
        if self.cfg.food_mode == "patches":            # fixed clumps; drawn only in patch mode
            self.patch_centers = self.rng.uniform(w.size * 0.12, w.size * 0.88,
                                                  size=(self.cfg.n_patches, 3))
        self.food = self._spawn_food(self.cfg.food_cap)
        self.food_type = self._food_types(self.cfg.food_cap)
        # predators (R143) — a second evolved-neural species; absent unless n_predators0>0
        self.pred_spec = BrainSpec(n_in=5, n_hidden=self.cfg.n_hidden, n_out=N_OUT)  # nearest prey(4)+energy(1)
        self.pred = None
        if self.has_predators:
            self.pred = Population(PopConfig(self.cfg.pred_capacity, self.pred_spec.n_weights))
            self._seed_predators()

    # --- setup ---
    def _seed_population(self) -> None:
        cfg, w, p = self.cfg, self.cfg.world, self.pop
        n0 = cfg.n0
        slots = p.alloc(n0)
        p.pos[slots] = self.rng.uniform(0, w.size, size=(n0, 3))
        d = self.rng.normal(size=(n0, 3))
        p.vel[slots] = d / np.linalg.norm(d, axis=1, keepdims=True) * cfg.speed
        p.energy[slots] = cfg.e_start
        p.brains[slots] = brain.random_brains(n0, self.spec, self.rng)
        p.lineage[slots] = np.arange(n0, dtype=np.int32)        # each founder a distinct bloodline
        p.generation[slots] = 0
        p.color[slots] = self.rng.uniform(0.25, 1.0, size=(n0, 3))
        if cfg.n_food_types > 1:                          # founders spread across diet niches
            p.diet[slots] = self.rng.uniform(0, cfg.n_food_types, size=n0)
        self.lineage_first_step = {int(i): 0 for i in range(n0)}

    def _seed_predators(self) -> None:
        cfg, w, pr = self.cfg, self.cfg.world, self.pred
        n = cfg.n_predators0
        slots = pr.alloc(n)
        pr.pos[slots] = self.rng.uniform(0, w.size, size=(n, 3))
        d = self.rng.normal(size=(n, 3))
        pr.vel[slots] = d / np.linalg.norm(d, axis=1, keepdims=True) * cfg.pred_speed
        pr.energy[slots] = cfg.pred_e_start
        pr.brains[slots] = brain.random_brains(n, self.pred_spec, self.rng)
        pr.lineage[slots] = np.arange(n, dtype=np.int32)
        pr.color[slots] = np.array([0.95, 0.15, 0.15])     # red hunters (render)

    def _food_types(self, n: int) -> np.ndarray:
        """Type label per food mote. Single type (R142 off, no RNG draw) keeps R141 determinism."""
        if self.cfg.n_food_types <= 1:
            return np.zeros(n, dtype=np.int64)
        return self.rng.integers(0, self.cfg.n_food_types, size=n)

    # --- sensing ---
    def _sense_neighbours(self, pos, right, up, fwd, sense_range):
        """Body-frame sense of the nearest neighbour -> (sense(P,4), neighbour-idx, proximity).

        The neighbour index + proximity are returned so the signalling channel (R144) can read that
        same nearest neighbour's utterance for free (no second KD-tree). idx indexes the active subset."""
        n = pos.shape[0]
        if n < 2:
            return np.zeros((n, 4)), None, np.zeros(n)
        dist, idx = cKDTree(pos).query(pos, k=2)        # k=2: self (col 0) + nearest other (col 1)
        nd, ni = dist[:, 1], idx[:, 1]
        nearest = pos[ni] - pos
        unit = nearest / np.maximum(np.linalg.norm(nearest, axis=1, keepdims=True), 1e-9)
        prox = np.where(nd < sense_range, 1.0 - nd / sense_range, 0.0)
        sense = np.stack([(unit * right).sum(1) * prox, (unit * up).sum(1) * prox,
                          (unit * fwd).sum(1) * prox, prox], axis=1)
        return sense, ni, prox

    def _agent_types(self, act):
        return np.clip(np.round(self.pop.diet[act]).astype(int), 0, self.cfg.n_food_types - 1)

    def _heard(self, act, ni, nprox):
        """The signal each prey hears: its nearest neighbour's previous-step utterance, gated to 0 when
        no neighbour is in range (R144). Returns (P,1). ni indexes the active subset (from _sense_neighbours)."""
        if ni is None or self.cfg.deaf:               # deaf control: brain has the input, hears only silence
            return np.zeros((act.size, 1))
        return (self.pop.utterance[act][ni] * (nprox > 0)).reshape(-1, 1)

    def _sense_food(self, pos, r, u, f, act):
        """Nearest food in the body frame. With resource types each agent senses only its own type."""
        cfg = self.cfg
        if cfg.n_food_types <= 1:
            return _sense_kd(pos, r, u, f, self.food, cfg.sense_range)
        out = np.zeros((pos.shape[0], 4))
        types = self._agent_types(act)
        for t in range(cfg.n_food_types):
            am = types == t
            food_t = self.food[self.food_type == t]
            if am.any() and food_t.shape[0]:
                out[am] = _sense_kd(pos[am], r[am], u[am], f[am], food_t, cfg.sense_range)
        return out

    def _pred_detect_range(self) -> float:
        """Prey direct predator-sense range. Shortened (prey_pred_range>0) in the signalling scenario so
        a neighbour closer to the predator can warn earlier; 0 -> full sense_range (R143 byte-identical)."""
        return self.cfg.prey_pred_range if self.cfg.prey_pred_range > 0 else self.cfg.sense_range

    def _sense_predators(self, pos, r, u, f):
        """Prey body-frame sense of the nearest predator (R143) -> (P,4). Drives evolved evasion."""
        if self.pred is None:
            return np.zeros((pos.shape[0], 4))
        pred_pos = self.pred.pos[self.pred.active()]
        return _sense_kd(pos, r, u, f, pred_pos, self._pred_detect_range())

    # --- the step ---
    def step(self) -> None:
        cfg, w, p = self.cfg, self.cfg.world, self.pop
        act = p.active()
        if act.size:
            pos, vel = p.pos[act], p.vel[act]
            r, u, f = _body_frame(vel)
            fs = self._sense_food(pos, r, u, f, act)
            ns, ni, nprox = self._sense_neighbours(pos, r, u, f, cfg.sense_range)
            e = (p.energy[act] / cfg.e_repro).reshape(-1, 1)
            parts = [fs, ns]
            if self.has_predators:                          # +predator-sense channel (R143)
                parts.append(self._sense_predators(pos, r, u, f))
            if self.signalling:                             # +heard-neighbour-utterance channel (R144)
                parts.append(self._heard(act, ni, nprox))
            parts.append(e)
            out = brain.forward(p.brains[act], self.spec, np.concatenate(parts, axis=1))
            newvel = _act(out, r, u, f, vel, cfg.force, cfg.min_speed, cfg.speed)  # _act reads out[:,:3]
            p.vel[act] = newvel
            p.pos[act] = w.clamp(pos + newvel)
            if self.signalling:                             # the evolved extra output IS the utterance
                p.utterance[act] = np.tanh(out[:, N_OUT])   # bounded [-1,1]; heard by neighbours next step
            speed = np.linalg.norm(newvel, axis=1)
            p.energy[act] = np.minimum(p.energy[act] - (cfg.base_cost + cfg.move_cost * speed), cfg.e_max)
            p.age[act] += 1
        self._eat()
        if self.has_predators:
            self._step_predators()
        self._die()
        self._reproduce()
        self._regrow()
        self.step_count += 1

    def _eat(self) -> None:
        cfg, p = self.cfg, self.pop
        act = p.active()
        if act.size == 0 or self.food.shape[0] == 0:
            return
        if cfg.n_food_types <= 1:
            dist, idx = cKDTree(self.food).query(p.pos[act], k=1)
            winners, eaten = _resolve(dist, idx, cfg.eat_radius)   # winners index into `act`
            if winners.size:
                p.energy[act[winners]] += cfg.food_value
                keep = np.ones(self.food.shape[0], dtype=bool)
                keep[eaten] = False
                self.food, self.food_type = self.food[keep], self.food_type[keep]
            return
        # typed: each agent eats only food of its own diet type (the resource-partitioning trade-off)
        types = self._agent_types(act)
        keep = np.ones(self.food.shape[0], dtype=bool)
        for t in range(cfg.n_food_types):
            am = np.where(types == t)[0]                # rows in act
            fm = np.where(self.food_type == t)[0]       # rows in food
            if am.size == 0 or fm.size == 0:
                continue
            dist, idx = cKDTree(self.food[fm]).query(p.pos[act[am]], k=1)
            winners, eaten = _resolve(dist, idx, cfg.eat_radius)
            if winners.size:
                p.energy[act[am[winners]]] += cfg.food_value
                keep[fm[eaten]] = False
        if not keep.all():
            self.food, self.food_type = self.food[keep], self.food_type[keep]

    def _die(self) -> None:
        cfg, p = self.cfg, self.pop
        act = p.active()
        if act.size == 0:
            return
        dead = act[(p.energy[act] <= 0.0) | (p.age[act] >= cfg.max_age)]
        if dead.size:
            p.kill(dead)

    # --- predators (R143) ---
    def _step_predators(self) -> None:
        cfg, w, pr = self.cfg, self.cfg.world, self.pred
        act = pr.active()
        if act.size:
            pos, vel = pr.pos[act], pr.vel[act]
            r, u, f = _body_frame(vel)
            prey_pos = self.pop.pos[self.pop.active()]
            qs = _sense_kd(pos, r, u, f, prey_pos, cfg.sense_range)         # nearest prey (4)
            e = (pr.energy[act] / cfg.pred_e_repro).reshape(-1, 1)
            out = brain.forward(pr.brains[act], self.pred_spec, np.concatenate([qs, e], axis=1))
            newvel = _act(out, r, u, f, vel, cfg.pred_force, cfg.min_speed, cfg.pred_speed)
            pr.vel[act] = newvel
            pr.pos[act] = w.clamp(pos + newvel)
            speed = np.linalg.norm(newvel, axis=1)
            pr.energy[act] = np.minimum(pr.energy[act] - (cfg.pred_base_cost + cfg.pred_move_cost * speed),
                                        cfg.pred_e_max)
            pr.age[act] += 1
            pr.cooldown[act] = np.maximum(pr.cooldown[act] - 1, 0)
        self._pred_catch()
        act = pr.active()
        if act.size:
            dead = act[(pr.energy[act] <= 0.0) | (pr.age[act] >= cfg.pred_max_age)]
            if dead.size:
                pr.kill(dead)
        self._pred_reproduce()

    def _pred_catch(self) -> None:
        cfg, pr, prey = self.cfg, self.pred, self.pop
        pa, qa = pr.active(), prey.active()
        if pa.size == 0 or qa.size == 0:
            return
        dist, idx = cKDTree(prey.pos[qa]).query(pr.pos[pa], k=1)            # nearest prey per predator
        ready = np.where(pr.cooldown[pa] == 0, dist, np.inf)               # only non-digesting predators
        hunters, caught = _resolve(ready, idx, cfg.catch_radius)           # one prey per closest hunter
        if hunters.size:
            pr.energy[pa[hunters]] += cfg.prey_energy_value
            pr.cooldown[pa[hunters]] = cfg.pred_handling
            prey.kill(qa[caught])

    def _pred_reproduce(self) -> None:
        cfg, w, pr = self.cfg, self.cfg.world, self.pred
        act = pr.active()
        if act.size == 0:
            return
        parents = act[pr.energy[act] >= cfg.pred_e_repro]
        if parents.size == 0:
            return
        slots = pr.alloc(parents.size)
        if slots.size == 0:
            return
        if slots.size < parents.size:
            parents = self.rng.choice(parents, size=slots.size, replace=False)
        pr.energy[parents] *= 0.5
        pr.energy[slots] = pr.energy[parents]
        pr.brains[slots] = (brain.mutate_brains(pr.brains[parents], self.rng, cfg.mut_rate, cfg.mut_sigma)
                            if self.evolve else pr.brains[parents])
        offset = self.rng.normal(0, cfg.birth_jitter, size=(parents.size, 3))
        pr.pos[slots] = w.clamp(pr.pos[parents] + offset)
        d = self.rng.normal(size=(parents.size, 3))
        pr.vel[slots] = d / np.linalg.norm(d, axis=1, keepdims=True) * cfg.min_speed
        pr.lineage[slots] = pr.lineage[parents]
        pr.generation[slots] = pr.generation[parents] + 1
        pr.color[slots] = pr.color[parents]

    def _reproduce(self) -> None:
        cfg, w, p = self.cfg, self.cfg.world, self.pop
        act = p.active()
        if act.size == 0:
            return
        parents = act[p.energy[act] >= cfg.e_repro]
        if parents.size == 0:
            return
        slots = p.alloc(parents.size)
        if slots.size == 0:
            return
        if slots.size < parents.size:                 # capacity-limited: pick which parents breed
            parents = self.rng.choice(parents, size=slots.size, replace=False)
        p.energy[parents] *= 0.5                        # 50/50 energy split
        p.energy[slots] = p.energy[parents]
        if self.evolve:
            p.brains[slots] = brain.mutate_brains(p.brains[parents], self.rng, cfg.mut_rate, cfg.mut_sigma)
            p.color[slots] = np.clip(p.color[parents] + self.rng.normal(0, 0.02, (parents.size, 3)), 0, 1)
        else:                                           # frozen control: exact copies, no innovation
            p.brains[slots] = p.brains[parents]
            p.color[slots] = p.color[parents]
        offset = self.rng.normal(0, cfg.birth_jitter, size=(parents.size, 3))
        p.pos[slots] = w.clamp(p.pos[parents] + offset)
        d = self.rng.normal(size=(parents.size, 3))
        p.vel[slots] = d / np.linalg.norm(d, axis=1, keepdims=True) * cfg.min_speed
        p.lineage[slots] = p.lineage[parents]
        p.generation[slots] = p.generation[parents] + 1
        if self.signalling:
            p.utterance[slots] = 0.0                      # newborns start mute (don't inherit a stale slot's signal)
        if cfg.n_food_types > 1:                          # diet is heritable + mutable -> niches evolve
            p.diet[slots] = np.clip(p.diet[parents] + self.rng.normal(0, cfg.diet_mut_sigma, parents.size),
                                    0.0, cfg.n_food_types - 1e-6)

    def _spawn_food(self, n: int) -> np.ndarray:
        """Place n food motes. Uniform (R141) or clumped in fixed patches (R142 niches)."""
        cfg, w = self.cfg, self.cfg.world
        if cfg.food_mode == "patches" and self.patch_centers is not None:
            which = self.rng.integers(0, cfg.n_patches, size=n)
            pts = self.patch_centers[which] + self.rng.normal(0, cfg.patch_radius, size=(n, 3))
            return np.clip(pts, 0.0, w.size)
        return self.rng.uniform(0, w.size, size=(n, 3))   # uniform: identical RNG call to R141

    def _regrow(self) -> None:
        cfg = self.cfg
        need = min(cfg.food_regrow, cfg.food_cap - self.food.shape[0])
        if need > 0:
            self.food = np.vstack([self.food, self._spawn_food(need)])
            self.food_type = np.concatenate([self.food_type, self._food_types(need)])

    # --- read-outs (in situ, never feed selection) ---
    def snapshot(self) -> dict:
        cfg, p = self.cfg, self.pop
        act = p.active()
        return {
            "step": self.step_count,
            "population": float(act.size),
            "food": float(self.food.shape[0]),
            "mean_energy": float(p.energy[act].mean()) if act.size else 0.0,
            "max_gen": float(p.generation[act].max()) if act.size else 0.0,
            "directedness": metrics.food_directedness(p.pos[act], p.vel[act], self.food, cfg.sense_range),
            "diversity": metrics.effective_lineages(p.lineage[act], self.lineage_first_step,
                                                    self.step_count, cfg.persist_steps),
            "diet_diversity": metrics.diet_diversity(p.diet[act], cfg.n_food_types),
            "predators": float(self.pred.n_alive) if self.pred is not None else 0.0,
            "flee": (metrics.flee_directedness(p.pos[act], p.vel[act],
                     self.pred.pos[self.pred.active()], cfg.sense_range)
                     if self.pred is not None else 0.0),
            "signal_mi": self._signal_mi(act),
        }

    def _danger(self, act):
        """Binary per-prey world-state: a predator within the prey's DIRECT detect range (R144)."""
        if self.pred is None:
            return np.zeros(act.size, dtype=int)
        return metrics.danger_state(self.pop.pos[act], self.pred.pos[self.pred.active()],
                                    self._pred_detect_range())

    def _signal_mi(self, act) -> float:
        """In-situ I(utterance ; danger-state) in bits — the live signal-informativeness read-out (R144)."""
        if not (self.signalling and self.has_predators) or act.size == 0:
            return 0.0
        return metrics.signal_world_mi(self.pop.utterance[act], self._danger(act), self.cfg.signal_bins)

    def signal_causal_test(self, rng: np.random.Generator | None = None) -> dict:
        """Causal LISTENING test: recompute every prey's action with the heard channel intact vs lesioned
        (silenced to 0), on the SAME brains and state. If receivers actually USE the signal, lesioning
        changes behaviour. The adaptive read-out: among prey hearing a loud alarm from a neighbour that is
        itself near a predator, do they accelerate AWAY from that (alarming) neighbour MORE when they can
        hear it than when deaf? +delta = the signal causally drives evasion. In situ; never feeds selection.
        """
        if not (self.signalling and self.has_predators):
            return {}
        p, cfg = self.pop, self.cfg
        act = p.active()
        if act.size < 2:
            return {}
        pos, vel = p.pos[act], p.vel[act]
        r, u, f = _body_frame(vel)
        fs = self._sense_food(pos, r, u, f, act)
        ns, ni, nprox = self._sense_neighbours(pos, r, u, f, cfg.sense_range)
        ps = self._sense_predators(pos, r, u, f)
        e = (p.energy[act] / cfg.e_repro).reshape(-1, 1)
        heard = self._heard(act, ni, nprox)

        def action(h):
            out = brain.forward(p.brains[act], self.spec, np.concatenate([fs, ns, ps, h, e], axis=1))
            return _act(out, r, u, f, vel, cfg.force, cfg.min_speed, cfg.speed)

        v_intact = action(heard)
        v_deaf = action(np.zeros_like(heard))
        daccel = float(np.linalg.norm(v_intact - v_deaf, axis=1).mean())
        if ni is None:
            return {"daccel": daccel, "flee_intact": 0.0, "flee_deaf": 0.0, "n_alarmed": 0}
        # subset: neighbour is near a predator (honest alarm) AND prey hears it loudly
        ndist = np.full(act.size, np.inf)
        if self.pred.n_alive:
            ndist, _ = cKDTree(self.pred.pos[self.pred.active()]).query(pos, k=1)
        neigh_danger = ndist[ni] < self._pred_detect_range()
        loud = (np.abs(heard[:, 0]) > 0.3) & (nprox > 0) & neigh_danger
        # flee AWAY from the alarming neighbour = move opposite the neighbour bearing
        ndir = pos[ni] - pos
        ndir = ndir / np.maximum(np.linalg.norm(ndir, axis=1, keepdims=True), 1e-9)
        def flee_away(v):
            sp = np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)
            return -((v / sp) * ndir).sum(1)              # +1 = straight away from neighbour
        if loud.sum() < 5:
            return {"daccel": daccel, "flee_intact": 0.0, "flee_deaf": 0.0, "n_alarmed": int(loud.sum())}
        return {
            "daccel": daccel,
            "flee_intact": float(flee_away(v_intact)[loud].mean()),
            "flee_deaf": float(flee_away(v_deaf)[loud].mean()),
            "n_alarmed": int(loud.sum()),
        }

    def render_arrays(self):
        """(pos, vel, color, food) of the living agents — prey + predators — for render3d.Renderer3D."""
        p, act = self.pop, self.pop.active()
        pos, vel, col = p.pos[act], p.vel[act], p.color[act]
        if self.pred is not None:
            pa = self.pred.active()
            pos = np.vstack([pos, self.pred.pos[pa]])
            vel = np.vstack([vel, self.pred.vel[pa]])
            col = np.vstack([col, self.pred.color[pa]])
        return pos, vel, col, self.food

    # --- persistence ---
    def save_checkpoint(self, path: str) -> None:
        st = self.pop.state()
        np.savez_compressed(
            path,
            step=np.int64(self.step_count),
            food=self.food,
            food_type=self.food_type,
            evolve=np.bool_(self.evolve),
            rng=np.array(json.dumps(self.rng.bit_generator.state)),
            lin_keys=np.array(list(self.lineage_first_step.keys()), dtype=np.int64),
            lin_vals=np.array(list(self.lineage_first_step.values()), dtype=np.int64),
            **{f"pop__{k}": v for k, v in st.items()},
        )

    def load_checkpoint(self, path: str) -> None:
        d = np.load(path, allow_pickle=False)
        self.step_count = int(d["step"])
        self.food = d["food"]
        self.food_type = d["food_type"]
        self.evolve = bool(d["evolve"])
        self.rng.bit_generator.state = json.loads(str(d["rng"]))
        st = {k[len("pop__"):]: d[k] for k in d.files if k.startswith("pop__")}
        self.pop.load(st)
        self.lineage_first_step = {int(k): int(v) for k, v in zip(d["lin_keys"], d["lin_vals"])}
