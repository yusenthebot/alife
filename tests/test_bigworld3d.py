"""Tests for the large-scale KD-tree-accelerated 3D ecosystem."""

from __future__ import annotations

import numpy as np

from alife.bigworld3d import BigWorld3D, _resolve

FIELDS = ("pos", "vel", "energy", "brains", "age", "cooldown")


def test_resolve_assigns_each_target_to_closest_hunter():
    # 3 hunters, idx says hunters 0&1 both target food 5, hunter 2 targets food 9
    dist = np.array([0.5, 0.2, 0.4])
    idx = np.array([5, 5, 9])
    hunters, targets = _resolve(dist, idx, radius=1.0)
    # food 5 -> hunter 1 (closer, 0.2); food 9 -> hunter 2
    assert set(targets.tolist()) == {5, 9}
    pair = dict(zip(targets.tolist(), hunters.tolist()))
    assert pair[5] == 1 and pair[9] == 2


def test_resolve_respects_radius():
    hunters, targets = _resolve(np.array([2.0, 3.0]), np.array([0, 1]), radius=1.0)
    assert hunters.size == 0 and targets.size == 0


def test_step_runs_and_consistent_at_scale():
    eco = BigWorld3D(seed=0)
    n = eco.prey["pos"].shape[0]
    assert n >= 2000  # genuinely large
    for _ in range(5):
        eco.step()
    for sp in (eco.prey, eco.pred):
        m = sp["pos"].shape[0]
        assert all(sp[k].shape[0] == m for k in FIELDS)
    assert np.all(np.isfinite(eco.prey["pos"]))
    assert eco.prey["pos"].min() >= 0 and eco.prey["pos"].max() <= eco.cfg.world.size + 1e-6


def test_predation_removes_prey_at_scale():
    eco = BigWorld3D(seed=1)
    # drop predators onto prey, force catches
    eco.pred["pos"][:] = eco.prey["pos"][: eco.pred["pos"].shape[0]]
    eco.pred["cooldown"][:] = 0
    before = eco.prey["pos"].shape[0]
    eco._catch()
    assert eco.prey["pos"].shape[0] < before
