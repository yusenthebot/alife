"""Tests for predator–prey co-evolution.

Mechanics, then the headline: an arms race. Measured against the FINAL evolved
opponent (de-confounded), predator hunting and prey evasion both escalate over
generations — neither could improve this way by chance.
"""

from __future__ import annotations

import numpy as np

from alife.coevo import CoevoConfig, arms_race_curves, coevolve, episode, rollout, spec
from alife.world import World
from alife import brain


def _cfg(gens: int) -> CoevoConfig:
    return CoevoConfig(world=World(180.0, 180.0, toroidal=True), n_prey=120, n_pred=36,
                       n_food=200, episode_steps=240, generations=gens)


def test_episode_shapes():
    cfg = _cfg(2)
    sp = spec()
    rng = np.random.default_rng(0)
    pf, df, info = episode(brain.random_brains(cfg.n_prey, sp, rng),
                           brain.random_brains(cfg.n_pred, sp, rng), cfg, seed=1)
    assert pf.shape == (cfg.n_prey,)
    assert df.shape == (cfg.n_pred,)
    assert "total_caught" in info and info["total_caught"] >= 0


def test_coevolve_runs_and_snapshots():
    cfg = _cfg(6)
    r = coevolve(cfg, seed=0)
    assert r["prey"].shape == (cfg.n_prey, spec().n_weights)
    assert r["pred"].shape == (cfg.n_pred, spec().n_weights)
    assert len(r["pred_snaps"]) == len(r["snap_gens"]) >= 2


def test_rollout_records_frames():
    cfg = _cfg(3)
    r = coevolve(cfg, seed=0)
    frames = rollout(r["prey"], r["pred"], cfg, seed=42, steps=60, capture_every=3)
    assert len(frames) == 20
    assert {"prey_pos", "prey_vel", "pred_pos", "pred_vel", "food"} <= frames[0].keys()


def test_arms_race_both_escalate():
    """Predator hunting and prey evasion both improve vs the final opponent."""
    cfg = _cfg(34)
    r = coevolve(cfg, seed=0)
    gens, pred_skill, prey_skill = arms_race_curves(r, cfg)
    # predators get markedly better at catching the final (evasive) prey
    assert pred_skill[-3:].mean() > pred_skill[0] + 20.0, f"predators should escalate: {pred_skill}"
    # prey get better at surviving the final predators
    assert prey_skill[-3:].mean() > prey_skill[0] + 0.02, f"prey should escalate: {prey_skill}"
