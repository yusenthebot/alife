"""Tests for 3D predator-prey co-evolution — mechanics + the arms-race headline."""

from __future__ import annotations

import numpy as np

from alife import brain
from alife.coevo3d import Coevo3DConfig, arms_race_curves3d, coevolve3d, episode3d, spec
from alife.world3d import World3D


def _cfg(gens):
    return Coevo3DConfig(world=World3D(size=110.0), n_prey=110, n_pred=32,
                         n_food=180, episode_steps=220, generations=gens)


def test_spec_io():
    s = spec()
    assert s.n_in == 8 and s.n_out == 3


def test_episode_shapes():
    cfg = _cfg(2)
    s, rng = spec(), np.random.default_rng(0)
    pf, df, info = episode3d(brain.random_brains(cfg.n_prey, s, rng),
                             brain.random_brains(cfg.n_pred, s, rng), cfg, seed=1)
    assert pf.shape == (cfg.n_prey,) and df.shape == (cfg.n_pred,)
    assert info["total_caught"] >= 0


def test_record_rollout():
    cfg = _cfg(2)
    s, rng = spec(), np.random.default_rng(0)
    frames = episode3d(brain.random_brains(cfg.n_prey, s, rng),
                       brain.random_brains(cfg.n_pred, s, rng), cfg, seed=1, steps=40, record=True)
    assert len(frames) == 40
    assert frames[0]["prey_pos"].shape[1] == 3 and frames[0]["pred_pos"].shape[1] == 3


def test_3d_arms_race_both_escalate():
    cfg = _cfg(34)
    r = coevolve3d(cfg, seed=0)
    gens, pred_skill, prey_skill = arms_race_curves3d(r, cfg)
    assert pred_skill[-3:].mean() > pred_skill[0] + 15.0, f"predators escalate: {pred_skill}"
    assert prey_skill[-3:].mean() > prey_skill[0] + 0.02, f"prey escalate: {prey_skill}"
