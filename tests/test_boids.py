"""Behavioral tests for the Boids substrate.

The headline test is emergence: starting from a random swarm, the order
parameter must rise — flocking is not coded into any boid, it has to appear.
The rest are invariants that keep the sim physically sane.
"""

from __future__ import annotations

import numpy as np
import pytest

from alife import boids, metrics
from alife.boids import BoidParams
from alife.sim import SimConfig, run
from alife.world import World


def _run(seed: int, steps: int = 250, n: int = 250) -> "object":
    world = World(width=140.0, height=140.0, toroidal=True)
    cfg = SimConfig(n=n, steps=steps, seed=seed, world=world, params=BoidParams())
    return run(cfg)


def test_no_nan_or_inf():
    res = _run(seed=1)
    assert np.all(np.isfinite(res.pos))
    assert np.all(np.isfinite(res.vel))
    for series in res.metrics.values():
        assert np.all(np.isfinite(series))


def test_positions_stay_in_world():
    res = _run(seed=2)
    assert res.pos.min() >= 0.0
    assert res.pos[:, 0].max() < 140.0
    assert res.pos[:, 1].max() < 140.0


def test_speed_within_limits():
    p = BoidParams()
    res = _run(seed=3)
    speed = np.linalg.norm(res.vel, axis=1)
    assert speed.max() <= p.max_speed + 1e-6
    assert speed.min() >= p.min_speed - 1e-6


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_flocking_increases_order(seed):
    """Emergence: alignment grows from a disordered start (averaged over time)."""
    res = _run(seed=seed, steps=300, n=300)
    order = res.metrics["order"]
    start = order[:20].mean()
    end = order[-40:].mean()
    assert start < 0.45, f"random start should be disordered, got {start:.3f}"
    assert end > start + 0.2, f"order should grow: {start:.3f} -> {end:.3f}"


def test_step_is_pure():
    """step() must not mutate its inputs (needed for safe evolution branching)."""
    world = World()
    p = BoidParams()
    rng = np.random.default_rng(0)
    pos, vel = boids.spawn(world, 50, p, rng)
    pos0, vel0 = pos.copy(), vel.copy()
    boids.step(world, p, pos, vel)
    assert np.array_equal(pos, pos0)
    assert np.array_equal(vel, vel0)


def test_cohesion_pulls_together():
    """With flocking on, the swarm packs tighter than a non-interacting one."""
    world = World(width=140.0, height=140.0, toroidal=True)
    flock = run(SimConfig(n=250, steps=250, seed=5, world=world, params=BoidParams()))
    inert = BoidParams(w_sep=0.0, w_ali=0.0, w_coh=0.0)
    drift = run(SimConfig(n=250, steps=250, seed=5, world=world, params=inert))
    assert flock.metrics["nn_dist"][-1] < drift.metrics["nn_dist"][-1]
