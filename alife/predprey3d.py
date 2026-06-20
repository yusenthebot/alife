"""Continuous predator-prey ecology in 3D — a self-sustaining living world.

R5's continuous lifecycle (energy · feeding · reproduction · death · Type-II
handling time) on the 3D substrate of R8/R9. Two species live in a volume: prey
graze drifting food and breed, predators hunt prey and breed, both die of
starvation or age. Seeded with the R9-evolved 3D hunt/flee brains so behavior is
competent from the first tick — then it runs on its own, the populations rising
and falling, generation after generation, in three dimensions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from scipy.spatial import cKDTree

from . import brain
from .coevo3d import _act, _body_frame, spec
from .world3d import World3D


def _sense_kd(pos, right, up, fwd, targets, sense_range):
    """Body-frame sensing of the nearest target via KD-tree -> (P,4) = [bx,by,bz]*prox, prox.

    Identical result to the dense coevo3d._sense (same nearest target) but O(P log M) memory instead
    of the O(P*M*3) array. SCALE-HARDENING: the dense form is only ~30 MB at the default caps
    (1500x850x3x8) — fine — but grows to GB-scale past a few thousand agents and is catastrophic at
    megascale, so use this KD-tree path before scaling up (see ~/.claude/rules/common/performance.md)."""
    p = pos.shape[0]
    if targets.shape[0] == 0:
        return np.zeros((p, 4))
    dist, idx = cKDTree(targets).query(pos, k=1)
    nearest = targets[idx] - pos
    unit = nearest / np.maximum(np.linalg.norm(nearest, axis=1, keepdims=True), 1e-9)
    prox = np.where(dist < sense_range, 1.0 - dist / sense_range, 0.0)
    return np.stack([(unit * right).sum(1) * prox, (unit * up).sum(1) * prox,
                     (unit * fwd).sum(1) * prox, prox], axis=1)


@dataclass(frozen=True)
class PredPrey3DConfig:
    world: World3D = field(default_factory=lambda: World3D(size=100.0))
    # food (drifting motes) — abundant so prey recover fast (stabilizes)
    food_cap: int = 850
    food_regrow: int = 24
    food_value: float = 26.0
    eat_radius: float = 3.2
    # prey (breeds fast, hardy)
    n_prey0: int = 280
    prey_cap: int = 1500
    prey_e_start: float = 50.0
    prey_e_repro: float = 66.0
    prey_e_max: float = 105.0
    prey_base_cost: float = 0.05
    prey_move_cost: float = 0.03
    prey_speed: float = 2.4
    prey_force: float = 0.5
    max_age_prey: int = 1500
    # predator (weak conversion + slow digestion + fast starvation -> self-limiting)
    n_pred0: int = 22
    pred_cap: int = 320              # capped well below prey so it can't wipe them out
    pred_e_start: float = 140.0
    pred_e_repro: float = 200.0
    pred_e_max: float = 250.0
    pred_base_cost: float = 0.50     # starves without prey, but not faster than it can hunt
    pred_move_cost: float = 0.05
    pred_speed: float = 2.7
    pred_force: float = 0.34
    catch_radius: float = 3.6
    prey_energy_value: float = 40.0  # max intake (value/handling ~1.05/step) must exceed upkeep
    pred_handling: int = 38          # digestion cooldown (Type-II stabilizer)
    max_age_pred: int = 2400
    min_speed: float = 0.6
    sense_range: float = 36.0
    mut_rate: float = 0.12
    mut_sigma: float = 0.18


class PredPrey3DEcosystem:
    def __init__(self, cfg, prey_brains=None, pred_brains=None, seed=0):
        self.cfg = cfg
        self.rng = np.random.default_rng(seed)
        self.spec = spec()
        w = cfg.world
        self.food = self.rng.uniform(0, w.size, size=(cfg.food_cap, 3))
        self.prey = self._init(cfg.n_prey0, cfg.prey_e_start, cfg.prey_speed, prey_brains)
        self.pred = self._init(cfg.n_pred0, cfg.pred_e_start, cfg.pred_speed, pred_brains)

    def _init(self, n, e_start, speed, brains):
        w, rng = self.cfg.world, self.rng
        b = brain.random_brains(n, self.spec, rng) if brains is None else brains[rng.integers(0, brains.shape[0], n)].copy()
        d = rng.normal(size=(n, 3))
        return {"pos": rng.uniform(0, w.size, size=(n, 3)),
                "vel": d / np.linalg.norm(d, axis=1, keepdims=True) * speed,
                "energy": np.full(n, float(e_start)),
                "brains": b, "age": np.zeros(n, dtype=int), "cooldown": np.zeros(n, dtype=int)}

    def step(self):
        cfg, w = self.cfg, self.cfg.world
        prey, pred = self.prey, self.pred
        # prey move (sense food + predators)
        if prey["pos"].shape[0]:
            r, u, f = _body_frame(prey["vel"])
            fs = _sense_kd(prey["pos"], r, u, f, self.food, cfg.sense_range)
            ps = _sense_kd(prey["pos"], r, u, f, pred["pos"], cfg.sense_range)
            prey["vel"] = _act(brain.forward(prey["brains"], self.spec, np.concatenate([fs, ps], 1)),
                               r, u, f, prey["vel"], cfg.prey_force, cfg.min_speed, cfg.prey_speed)
            prey["pos"] = w.clamp(prey["pos"] + prey["vel"])
        # predators move (sense prey)
        if pred["pos"].shape[0]:
            r, u, f = _body_frame(pred["vel"])
            qs = _sense_kd(pred["pos"], r, u, f, prey["pos"], cfg.sense_range)
            z = np.zeros((pred["pos"].shape[0], 4))
            pred["vel"] = _act(brain.forward(pred["brains"], self.spec, np.concatenate([qs, z], 1)),
                               r, u, f, pred["vel"], cfg.pred_force, cfg.min_speed, cfg.pred_speed)
            pred["pos"] = w.clamp(pred["pos"] + pred["vel"])

        self._graze()
        pred["cooldown"] = np.maximum(pred["cooldown"] - 1, 0)
        self._catch()
        prey["energy"] = np.minimum(prey["energy"] - (cfg.prey_base_cost + cfg.prey_move_cost * np.linalg.norm(prey["vel"], axis=1)), cfg.prey_e_max)
        pred["energy"] = np.minimum(pred["energy"] - (cfg.pred_base_cost + cfg.pred_move_cost * np.linalg.norm(pred["vel"], axis=1)), cfg.pred_e_max)
        prey["age"] += 1
        pred["age"] += 1
        self._mask(prey, (prey["energy"] > 0) & (prey["age"] < cfg.max_age_prey))
        self._mask(pred, (pred["energy"] > 0) & (pred["age"] < cfg.max_age_pred))
        self._reproduce(prey, cfg.prey_e_repro, cfg.prey_cap)
        self._reproduce(pred, cfg.pred_e_repro, cfg.pred_cap)
        need = min(cfg.food_regrow, cfg.food_cap - self.food.shape[0])
        if need > 0:
            self.food = np.vstack([self.food, self.rng.uniform(0, w.size, size=(need, 3))])

    def _graze(self):
        # KD-tree (food -> nearest prey, multi-eat) — identical to the old dense
        # `food[None]-prey[:,None]` argmin but O(F log P) memory not O(P*F*3) (scale-hardening).
        cfg, prey = self.cfg, self.prey
        if not (prey["pos"].shape[0] and self.food.shape[0]):
            return
        dist, idx = cKDTree(prey["pos"]).query(self.food, k=1)   # each food -> its nearest prey
        eaten = dist < cfg.eat_radius
        if eaten.any():
            np.add.at(prey["energy"], idx[eaten], cfg.food_value)
            self.food = self.food[~eaten]

    def _catch(self):
        cfg, prey, pred = self.cfg, self.prey, self.pred
        if not (pred["pos"].shape[0] and prey["pos"].shape[0]):
            return
        rel = prey["pos"][None] - pred["pos"][:, None, :]
        pd2 = np.einsum("pmk,pmk->pm", rel, rel)
        alive = np.ones(prey["pos"].shape[0], dtype=bool)
        nearest = pd2.argmin(1)
        can = (pd2[np.arange(pred["pos"].shape[0]), nearest] < cfg.catch_radius ** 2) & (pred["cooldown"] == 0)
        for p in np.where(can)[0]:
            t = nearest[p]
            if alive[t]:
                alive[t] = False
                pred["energy"][p] += cfg.prey_energy_value
                pred["cooldown"][p] = cfg.pred_handling
        if not alive.all():
            self._mask(prey, alive)

    def _mask(self, sp, keep):
        if keep.all():
            return
        for k in ("pos", "vel", "energy", "brains", "age", "cooldown"):
            sp[k] = sp[k][keep]

    def _reproduce(self, sp, e_repro, cap):
        idx = np.where(sp["energy"] >= e_repro)[0]
        room = cap - sp["pos"].shape[0]
        if idx.size == 0 or room <= 0:
            return
        if idx.size > room:
            idx = self.rng.choice(idx, size=room, replace=False)
        sp["energy"][idx] *= 0.5
        w = self.cfg.world
        kids = brain.mutate_brains(sp["brains"][idx], self.rng, self.cfg.mut_rate, self.cfg.mut_sigma)
        d = self.rng.normal(size=(idx.size, 3))
        sp["pos"] = np.vstack([sp["pos"], w.clamp(sp["pos"][idx] + self.rng.normal(0, 1.5, (idx.size, 3)))])
        sp["vel"] = np.vstack([sp["vel"], d / np.linalg.norm(d, axis=1, keepdims=True) * self.cfg.min_speed])
        sp["energy"] = np.concatenate([sp["energy"], sp["energy"][idx].copy()])
        sp["brains"] = np.vstack([sp["brains"], kids])
        sp["age"] = np.concatenate([sp["age"], np.zeros(idx.size, dtype=int)])
        sp["cooldown"] = np.concatenate([sp["cooldown"], np.zeros(idx.size, dtype=int)])

    def snapshot(self):
        return {"prey": float(self.prey["pos"].shape[0]), "pred": float(self.pred["pos"].shape[0]),
                "food": float(self.food.shape[0])}
