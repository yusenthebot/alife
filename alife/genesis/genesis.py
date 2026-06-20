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
is attributable to the brain. Reserved hooks (an utterance output, a terraform action) are inert in
R141 so Stages 2-4 activate a slot rather than rewrite the substrate.
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
    # metric
    persist_steps: int = 200


class GenesisWorld:
    def __init__(self, cfg: GenesisConfig | None = None, seed: int = 0, evolve: bool = True):
        self.cfg = cfg or GenesisConfig()
        self.rng = np.random.default_rng(seed)
        self.evolve = evolve
        self.spec = BrainSpec(n_in=N_IN, n_hidden=self.cfg.n_hidden, n_out=N_OUT)
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

    def _food_types(self, n: int) -> np.ndarray:
        """Type label per food mote. Single type (R142 off, no RNG draw) keeps R141 determinism."""
        if self.cfg.n_food_types <= 1:
            return np.zeros(n, dtype=np.int64)
        return self.rng.integers(0, self.cfg.n_food_types, size=n)

    # --- sensing ---
    def _sense_neighbours(self, pos, right, up, fwd, sense_range):
        n = pos.shape[0]
        if n < 2:
            return np.zeros((n, 4))
        dist, idx = cKDTree(pos).query(pos, k=2)        # k=2: self (col 0) + nearest other (col 1)
        nd, ni = dist[:, 1], idx[:, 1]
        nearest = pos[ni] - pos
        unit = nearest / np.maximum(np.linalg.norm(nearest, axis=1, keepdims=True), 1e-9)
        prox = np.where(nd < sense_range, 1.0 - nd / sense_range, 0.0)
        return np.stack([(unit * right).sum(1) * prox, (unit * up).sum(1) * prox,
                         (unit * fwd).sum(1) * prox, prox], axis=1)

    def _agent_types(self, act):
        return np.clip(np.round(self.pop.diet[act]).astype(int), 0, self.cfg.n_food_types - 1)

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

    # --- the step ---
    def step(self) -> None:
        cfg, w, p = self.cfg, self.cfg.world, self.pop
        act = p.active()
        if act.size:
            pos, vel = p.pos[act], p.vel[act]
            r, u, f = _body_frame(vel)
            fs = self._sense_food(pos, r, u, f, act)
            ns = self._sense_neighbours(pos, r, u, f, cfg.sense_range)
            e = (p.energy[act] / cfg.e_repro).reshape(-1, 1)
            x = np.concatenate([fs, ns, e], axis=1)
            out = brain.forward(p.brains[act], self.spec, x)
            newvel = _act(out, r, u, f, vel, cfg.force, cfg.min_speed, cfg.speed)
            p.vel[act] = newvel
            p.pos[act] = w.clamp(pos + newvel)
            speed = np.linalg.norm(newvel, axis=1)
            p.energy[act] = np.minimum(p.energy[act] - (cfg.base_cost + cfg.move_cost * speed), cfg.e_max)
            p.age[act] += 1
        self._eat()
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
        }

    def render_arrays(self):
        """(pos, vel, color, food) of the living agents — fed straight to render3d.Renderer3D."""
        p, act = self.pop, self.pop.active()
        return p.pos[act], p.vel[act], p.color[act], self.food

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
