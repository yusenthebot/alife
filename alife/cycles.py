"""Sustained predator-prey population cycles (the recurring honest gap).

R5 and R10 reached stable COEXISTENCE, never the textbook Lotka-Volterra
oscillation — because uncapping predators tipped them into trough-extinction.
The classic resolution (Huffaker's mite experiments) is a PREY REFUGE: a small
seed population that predators can't reach, so prey always rebound from the
trough. Here that's a refuge floor — when prey fall below it, a few re-emerge
from the refuge. With predators uncapped (numerical response) + a Type-II
handling time + enrichment, the system settles into a genuine limit cycle.

Movement is simple hand-coded chase/flee — cycles are a population-rate
phenomenon, and isolating the rates (not evolving behavior, done in R4/R9) is
what makes the dynamics clear and tunable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.spatial import cKDTree

from .world import World


@dataclass(frozen=True)
class CyclesConfig:
    world: World = field(default_factory=lambda: World(300.0, 300.0, toroidal=True))
    # food — moderate (prey are food-limited BELOW the cap so predation can move them)
    food_cap: int = 750
    food_regrow: int = 14
    food_value: float = 22.0
    eat_radius: float = 3.0
    # prey
    n_prey0: int = 350
    prey_refuge: int = 40          # refuge seed — prey never fall below this
    prey_cap: int = 9000           # high => food + predation set prey level, not the cap
    prey_speed: float = 2.6
    prey_e_start: float = 40.0
    prey_e_repro: float = 60.0
    prey_e_max: float = 90.0
    prey_base_cost: float = 0.05
    flee_range: float = 26.0
    # predator (uncapped numerical response + Type-II)
    n_pred0: int = 30
    pred_cap: int = 3000           # high — ecology, not the cap, limits them
    pred_speed: float = 3.0
    pred_e_start: float = 70.0
    pred_e_repro: float = 150.0    # slow numerical response => lag => oscillation
    pred_e_max: float = 200.0
    pred_base_cost: float = 0.55   # starves fast when prey scarce
    catch_radius: float = 3.2
    prey_energy_value: float = 70.0
    pred_handling: int = 22        # Type-II saturation
    max_age_pred: int = 4000


def _flee_chase(world, pos, targets, away: bool, speed, rng):
    """Steer toward (chase) or from (flee) the nearest target; wander if none."""
    n = pos.shape[0]
    if targets.shape[0] == 0:
        d = rng.normal(size=(n, 2))
        return d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9) * speed
    _, idx = cKDTree(targets).query(pos, k=1)
    delta = targets[idx] - pos
    if world.toroidal:
        delta -= world.size * np.round(delta / world.size)
    v = -delta if away else delta
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9) * speed


class CyclesEcosystem:
    def __init__(self, cfg: CyclesConfig, seed=0):
        self.cfg = cfg
        self.rng = np.random.default_rng(seed)
        w = cfg.world
        self.food = self.rng.uniform([0, 0], w.size, size=(cfg.food_cap, 2))
        self.prey = self._init(cfg.n_prey0, cfg.prey_e_start)
        self.pred = self._init(cfg.n_pred0, cfg.pred_e_start)

    def _init(self, n, e):
        w = self.cfg.world
        return {"pos": self.rng.uniform([0, 0], w.size, size=(n, 2)),
                "energy": np.full(n, float(e)), "age": np.zeros(n, int),
                "cooldown": np.zeros(n, int)}

    def step(self):
        cfg, w, rng = self.cfg, self.cfg.world, self.rng
        prey, pred = self.prey, self.pred
        # prey flee predators if any near, else move toward food
        if prey["pos"].shape[0]:
            if pred["pos"].shape[0]:
                _, idx = cKDTree(pred["pos"]).query(prey["pos"], k=1)
                dpred = pred["pos"][idx] - prey["pos"]
                if w.toroidal:
                    dpred -= w.size * np.round(dpred / w.size)
                threatened = np.linalg.norm(dpred, axis=1) < cfg.flee_range
            else:
                threatened = np.zeros(prey["pos"].shape[0], bool)
            v_food = _flee_chase(w, prey["pos"], self.food, False, cfg.prey_speed, rng)
            v_flee = _flee_chase(w, prey["pos"], pred["pos"], True, cfg.prey_speed, rng)
            vel = np.where(threatened[:, None], v_flee, v_food)
            prey["pos"] = w.wrap(prey["pos"] + vel)
        if pred["pos"].shape[0]:
            vel = _flee_chase(w, pred["pos"], prey["pos"], False, cfg.pred_speed, rng)
            pred["pos"] = w.wrap(pred["pos"] + vel)

        self._graze()
        pred["cooldown"] = np.maximum(pred["cooldown"] - 1, 0)
        self._catch()
        prey["energy"] -= cfg.prey_base_cost
        pred["energy"] -= cfg.pred_base_cost
        np.minimum(prey["energy"], cfg.prey_e_max, out=prey["energy"])
        np.minimum(pred["energy"], cfg.pred_e_max, out=pred["energy"])
        prey["age"] += 1; pred["age"] += 1
        self._mask(prey, prey["energy"] > 0)
        self._mask(pred, (pred["energy"] > 0) & (pred["age"] < cfg.max_age_pred))
        self._reproduce(prey, cfg.prey_e_repro, cfg.prey_cap)
        self._reproduce(pred, cfg.pred_e_repro, cfg.pred_cap)
        self._refuge()
        need = min(cfg.food_regrow, cfg.food_cap - self.food.shape[0])
        if need > 0:
            self.food = np.vstack([self.food, rng.uniform([0, 0], w.size, size=(need, 2))])

    def _graze(self):
        cfg, prey = self.cfg, self.prey
        if not (prey["pos"].shape[0] and self.food.shape[0]):
            return
        dist, idx = cKDTree(self.food).query(prey["pos"], k=1)
        hit = dist < cfg.eat_radius
        if not hit.any():
            return
        order = np.argsort(dist[hit]); fi = idx[hit][order]; pi = np.where(hit)[0][order]
        _, first = np.unique(fi, return_index=True)
        prey["energy"][pi[first]] += cfg.food_value
        keep = np.ones(self.food.shape[0], bool); keep[fi[first]] = False
        self.food = self.food[keep]

    def _catch(self):
        cfg, prey, pred = self.cfg, self.prey, self.pred
        if not (pred["pos"].shape[0] and prey["pos"].shape[0]):
            return
        dist, idx = cKDTree(prey["pos"]).query(pred["pos"], k=1)
        ready = (dist < cfg.catch_radius) & (pred["cooldown"] == 0)
        if not ready.any():
            return
        order = np.argsort(np.where(ready, dist, np.inf))
        ti = idx[order]; hi = order
        ready_sorted = ready[order]
        ti, hi = ti[ready_sorted], hi[ready_sorted]
        _, first = np.unique(ti, return_index=True)
        winners, caught = hi[first], ti[first]
        pred["energy"][winners] += cfg.prey_energy_value
        pred["cooldown"][winners] = cfg.pred_handling
        keep = np.ones(prey["pos"].shape[0], bool); keep[caught] = False
        self._mask(prey, keep)

    def _mask(self, sp, keep):
        if keep.all():
            return
        for k in ("pos", "energy", "age", "cooldown"):
            sp[k] = sp[k][keep]

    def _reproduce(self, sp, e_repro, cap):
        idx = np.where(sp["energy"] >= e_repro)[0]
        room = cap - sp["pos"].shape[0]
        if idx.size == 0 or room <= 0:
            return
        if idx.size > room:
            idx = self.rng.choice(idx, size=room, replace=False)
        sp["energy"][idx] *= 0.5
        off = self.rng.normal(0, 2.0, size=(idx.size, 2))
        sp["pos"] = np.vstack([sp["pos"], self.cfg.world.wrap(sp["pos"][idx] + off)])
        sp["energy"] = np.concatenate([sp["energy"], sp["energy"][idx].copy()])
        sp["age"] = np.concatenate([sp["age"], np.zeros(idx.size, int)])
        sp["cooldown"] = np.concatenate([sp["cooldown"], np.zeros(idx.size, int)])

    def _refuge(self):
        """Huffaker refuge: keep a minimum prey seed so they rebound from the trough."""
        cfg, prey = self.cfg, self.prey
        deficit = cfg.prey_refuge - prey["pos"].shape[0]
        if deficit <= 0:
            return
        w = self.cfg.world
        prey["pos"] = np.vstack([prey["pos"], self.rng.uniform([0, 0], w.size, size=(deficit, 2))])
        prey["energy"] = np.concatenate([prey["energy"], np.full(deficit, cfg.prey_e_start)])
        prey["age"] = np.concatenate([prey["age"], np.zeros(deficit, int)])
        prey["cooldown"] = np.concatenate([prey["cooldown"], np.zeros(deficit, int)])

    def snapshot(self):
        return {"prey": float(self.prey["pos"].shape[0]), "pred": float(self.pred["pos"].shape[0]),
                "food": float(self.food.shape[0])}
