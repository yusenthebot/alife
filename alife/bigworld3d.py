"""Large-scale continuous 3D ecosystem — the living world at full scale.

R10's continuous predator-prey ecology is O(P·M) in its sensing, grazing and
catching, which caps it at ~1500 creatures. Here every nearest-neighbour query
goes through a KD-tree, so thousands of evolved-brain prey and predators live,
hunt, flee, graze, breed and die in one 3D volume — the definitive watchable
artifact, combining the ecology (R10), the atmosphere (R11) and the scale (R13).
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
from scipy.spatial import cKDTree

from . import brain
from .coevo3d import _act, _body_frame
from .predprey3d import PredPrey3DConfig, PredPrey3DEcosystem


def big_config() -> PredPrey3DConfig:
    """R10's balanced economy, scaled to a big world + populations."""
    from .world3d import World3D
    return replace(PredPrey3DConfig(),
                   world=World3D(size=170.0),
                   food_cap=4500, food_regrow=130, n_prey0=2200, prey_cap=9000,
                   n_pred0=120, pred_cap=1600)


def _sense_kd(pos, right, up, fwd, targets, sense_range):
    """Body-frame sensing of the nearest target via KD-tree -> (P,4)."""
    p = pos.shape[0]
    if targets.shape[0] == 0:
        return np.zeros((p, 4))
    dist, idx = cKDTree(targets).query(pos, k=1)
    nearest = targets[idx] - pos
    unit = nearest / np.maximum(np.linalg.norm(nearest, axis=1, keepdims=True), 1e-9)
    prox = np.where(dist < sense_range, 1.0 - dist / sense_range, 0.0)
    return np.stack([(unit * right).sum(1) * prox, (unit * up).sum(1) * prox,
                     (unit * fwd).sum(1) * prox, prox], axis=1)


def _resolve(dist, idx, radius):
    """Assign each target to its single closest hunter within radius. Returns
    (hunter_indices, target_indices) — one row per consumed target."""
    hit = dist < radius
    if not hit.any():
        return np.empty(0, int), np.empty(0, int)
    hi = np.where(hit)[0]
    ti = idx[hit]
    order = np.argsort(dist[hit])               # closest first
    ti_s, hi_s = ti[order], hi[order]
    _, first = np.unique(ti_s, return_index=True)   # first (closest) hunter per target
    return hi_s[first], ti_s[first]


class BigWorld3D(PredPrey3DEcosystem):
    def __init__(self, prey_brains=None, pred_brains=None, seed=0):
        super().__init__(big_config(), prey_brains=prey_brains, pred_brains=pred_brains, seed=seed)

    def step(self):
        cfg, w = self.cfg, self.cfg.world
        prey, pred = self.prey, self.pred
        if prey["pos"].shape[0]:
            r, u, f = _body_frame(prey["vel"])
            fs = _sense_kd(prey["pos"], r, u, f, self.food, cfg.sense_range)
            ps = _sense_kd(prey["pos"], r, u, f, pred["pos"], cfg.sense_range)
            prey["vel"] = _act(brain.forward(prey["brains"], self.spec, np.concatenate([fs, ps], 1)),
                               r, u, f, prey["vel"], cfg.prey_force, cfg.min_speed, cfg.prey_speed)
            prey["pos"] = w.clamp(prey["pos"] + prey["vel"])
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
        cfg, prey = self.cfg, self.prey
        if not (prey["pos"].shape[0] and self.food.shape[0]):
            return
        dist, idx = cKDTree(self.food).query(prey["pos"], k=1)
        winners, eaten = _resolve(dist, idx, cfg.eat_radius)
        if winners.size:
            prey["energy"][winners] += cfg.food_value
            keep = np.ones(self.food.shape[0], dtype=bool)
            keep[eaten] = False
            self.food = self.food[keep]

    def _catch(self):
        cfg, prey, pred = self.cfg, self.prey, self.pred
        if not (pred["pos"].shape[0] and prey["pos"].shape[0]):
            return
        dist, idx = cKDTree(prey["pos"]).query(pred["pos"], k=1)
        ready = pred["cooldown"] == 0
        dist = np.where(ready, dist, np.inf)
        hunters, caught = _resolve(dist, idx, cfg.catch_radius)
        if hunters.size:
            pred["energy"][hunters] += cfg.prey_energy_value
            pred["cooldown"][hunters] = cfg.pred_handling
            keep = np.ones(prey["pos"].shape[0], dtype=bool)
            keep[caught] = False
            self._mask(prey, keep)
