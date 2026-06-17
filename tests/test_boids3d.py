"""3D Boids: same emergence guarantees as 2D, now in volume."""

from __future__ import annotations

import numpy as np
import pytest

from alife import boids3d
from alife.boids3d import Boid3DParams
from alife.world3d import World3D


def _run(seed, steps=200, n=200):
    world = World3D(size=90.0)
    p = Boid3DParams()
    rng = np.random.default_rng(seed)
    pos, vel = boids3d.spawn(world, n, p, rng)
    for _ in range(steps):
        pos, vel = boids3d.step(world, p, pos, vel)
    return world, p, pos, vel


def test_spawn_shapes_and_speed():
    world = World3D()
    p = Boid3DParams()
    pos, vel = boids3d.spawn(world, 50, p, np.random.default_rng(0))
    assert pos.shape == (50, 3) and vel.shape == (50, 3)


def test_positions_stay_in_box():
    world, p, pos, vel = _run(1)
    assert pos.min() >= 0.0 and pos.max() <= world.size + 1e-6


def test_no_nan_and_speed_limited():
    world, p, pos, vel = _run(2)
    assert np.all(np.isfinite(pos)) and np.all(np.isfinite(vel))
    speed = np.linalg.norm(vel, axis=1)
    assert speed.max() <= p.max_speed + 1e-6


def test_order_parameter_aligned():
    vel = np.tile([1.0, 0.0, 0.0], (80, 1))
    assert boids3d.order_parameter(vel) == 1.0


@pytest.mark.parametrize("seed", [0, 1])
def test_flocking_increases_order(seed):
    world = World3D(size=90.0)
    p = Boid3DParams()
    rng = np.random.default_rng(seed)
    pos, vel = boids3d.spawn(world, 250, p, rng)
    start = boids3d.order_parameter(vel)
    for _ in range(300):
        pos, vel = boids3d.step(world, p, pos, vel)
    end = boids3d.order_parameter(vel)
    assert start < 0.4
    assert end > start + 0.2, f"3D order should grow: {start:.2f} -> {end:.2f}"
