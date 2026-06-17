"""Large-scale 3D flocking (KDTree spatial index): emergence + invariants at N
beyond the O(N²) regime."""

from __future__ import annotations

import numpy as np

from alife import swarm3d
from alife.swarm3d import Swarm3DParams
from alife.world3d import World3D


def _run(seed, n=3000, steps=150):
    world = World3D(size=130.0)
    p = Swarm3DParams()
    rng = np.random.default_rng(seed)
    pos, vel = swarm3d.spawn(world, n, p, rng)
    for _ in range(steps):
        pos, vel = swarm3d.step(world, p, pos, vel)
    return world, p, pos, vel


def test_spawn_shapes():
    world = World3D()
    pos, vel = swarm3d.spawn(world, 5000, Swarm3DParams(), np.random.default_rng(0))
    assert pos.shape == (5000, 3) and vel.shape == (5000, 3)


def test_in_box_no_nan_speed_limited():
    world, p, pos, vel = _run(1)
    assert pos.min() >= 0 and pos.max() <= world.size + 1e-6
    assert np.all(np.isfinite(pos)) and np.all(np.isfinite(vel))
    assert np.linalg.norm(vel, axis=1).max() <= p.max_speed + 1e-6


def test_large_scale_flocking_increases_order():
    world = World3D(size=130.0)
    p = Swarm3DParams()
    rng = np.random.default_rng(0)
    pos, vel = swarm3d.spawn(world, 4000, p, rng)
    start = swarm3d.order_parameter(vel)
    for _ in range(200):
        pos, vel = swarm3d.step(world, p, pos, vel)
    end = swarm3d.order_parameter(vel)
    assert start < 0.4
    assert end > start + 0.2, f"order should grow at scale: {start:.2f} -> {end:.2f}"
