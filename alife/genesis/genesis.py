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
        self.food = self.rng.uniform(0, w.size, size=(self.cfg.food_cap, 3))

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
        self.lineage_first_step = {int(i): 0 for i in range(n0)}

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

    # --- the step ---
    def step(self) -> None:
        cfg, w, p = self.cfg, self.cfg.world, self.pop
        act = p.active()
        if act.size:
            pos, vel = p.pos[act], p.vel[act]
            r, u, f = _body_frame(vel)
            fs = _sense_kd(pos, r, u, f, self.food, cfg.sense_range)
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
        dist, idx = cKDTree(self.food).query(p.pos[act], k=1)
        winners, eaten = _resolve(dist, idx, cfg.eat_radius)   # winners index into `act`
        if winners.size:
            p.energy[act[winners]] += cfg.food_value
            keep = np.ones(self.food.shape[0], dtype=bool)
            keep[eaten] = False
            self.food = self.food[keep]

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

    def _regrow(self) -> None:
        cfg = self.cfg
        need = min(cfg.food_regrow, cfg.food_cap - self.food.shape[0])
        if need > 0:
            self.food = np.vstack([self.food, self.rng.uniform(0, cfg.world.size, size=(need, 3))])

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
        self.evolve = bool(d["evolve"])
        self.rng.bit_generator.state = json.loads(str(d["rng"]))
        st = {k[len("pop__"):]: d[k] for k in d.files if k.startswith("pop__")}
        self.pop.load(st)
        self.lineage_first_step = {int(k): int(v) for k, v in zip(d["lin_keys"], d["lin_vals"])}
