"""Unit tests for the emergence metrics — known inputs, known outputs."""

from __future__ import annotations

import numpy as np

from alife import metrics
from alife.world import World


def test_order_parameter_aligned_is_one():
    vel = np.tile([1.0, 0.0], (100, 1))
    assert metrics.order_parameter(vel) == 1.0


def test_order_parameter_opposed_is_zero():
    vel = np.array([[1.0, 0.0]] * 50 + [[-1.0, 0.0]] * 50)
    assert metrics.order_parameter(vel) < 1e-9


def test_order_parameter_random_is_small():
    rng = np.random.default_rng(0)
    ang = rng.uniform(0, 2 * np.pi, 2000)
    vel = np.stack([np.cos(ang), np.sin(ang)], axis=1)
    assert metrics.order_parameter(vel) < 0.1


def test_mean_neighbor_distance_known():
    world = World(width=100.0, height=100.0, toroidal=False)
    pos = np.array([[0.0, 0.0], [3.0, 0.0], [3.0, 4.0]])
    # nearest neighbors: 0->1 =3, 1->0 =3, 2->1 =4 ; mean = 10/3
    assert abs(metrics.mean_neighbor_distance(world, pos) - 10.0 / 3.0) < 1e-9


def test_cluster_count_two_groups():
    world = World(width=1000.0, height=1000.0, toroidal=False)
    pos = np.array([[0.0, 0.0], [1.0, 0.0], [500.0, 500.0], [501.0, 500.0]])
    assert metrics.cluster_count(world, pos, radius=5.0) == 2


def test_rotation_order_ring_is_high():
    """Boids on a circle all moving tangentially => strong milling signal."""
    world = World(width=200.0, height=200.0, toroidal=False)
    ang = np.linspace(0, 2 * np.pi, 60, endpoint=False)
    pos = np.stack([100 + 30 * np.cos(ang), 100 + 30 * np.sin(ang)], axis=1)
    vel = np.stack([-np.sin(ang), np.cos(ang)], axis=1)
    assert metrics.rotation_order(world, pos, vel) > 0.95
