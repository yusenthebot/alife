"""Tests for evolution in 3D — same headline as R3, now in volume:
random 3D brains evolve into competent 3D foragers that generalize to a held-out
food field.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from alife import evolve3d
from alife.evolve3d import Forage3DConfig, batch_forage3d, evolve3d as run_evolve, spec
from alife.world3d import World3D


def _cfg(**kw):
    return replace(Forage3DConfig(world=World3D(size=110.0)), **kw)


def test_spec_io():
    s = spec()
    assert s.n_in == 5 and s.n_out == 3


def test_body_frame_orthonormal():
    vel = np.random.default_rng(0).normal(size=(20, 3))
    r, u, f = evolve3d._body_frame(vel)
    assert np.allclose(np.linalg.norm(r, axis=1), 1, atol=1e-5)
    assert np.allclose((r * u).sum(1), 0, atol=1e-5)
    assert np.allclose((r * f).sum(1), 0, atol=1e-5)


def test_batch_forage_shape_nonneg():
    from alife import brain
    cfg = _cfg()
    s = spec()
    fit = batch_forage3d(brain.random_brains(20, s, np.random.default_rng(0)), s, cfg, 100, seed=1)
    assert fit.shape == (20,) and (fit >= 0).all()


def test_rollout_shared_runs():
    from alife import brain
    cfg = _cfg(n_food=120)
    s = spec()
    frames = evolve3d.rollout3d_shared(brain.random_brains(40, s, np.random.default_rng(0)), s, cfg, 30, seed=1)
    assert len(frames) == 15
    assert frames[0]["pos"].shape == (40, 3)


def test_3d_foraging_evolves_and_generalizes():
    cfg = _cfg(pop=120, generations=30, eval_steps=260, n_food=240)
    brains, hist, gen0, s = run_evolve(cfg, seed=0)
    rand = batch_forage3d(gen0[:24], s, replace(cfg, eval_steps=280), 280, seed=99999).mean()
    evo = batch_forage3d(brains[:24], s, replace(cfg, eval_steps=280), 280, seed=99999).mean()
    assert hist[-1, 1] > hist[0, 1] + 8.0, f"fitness should climb: {hist[0,1]:.1f} -> {hist[-1,1]:.1f}"
    assert evo > rand * 2.0, f"evolved should generalize: random {rand:.1f} -> evolved {evo:.1f}"
