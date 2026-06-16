"""Sensor tests: egocentric geometry must be correct or the brain is blind."""

from __future__ import annotations

import numpy as np

from alife import sensors
from alife.world import World


def test_n_inputs():
    assert sensors.n_inputs(6) == 13


def test_sense_shape():
    world = World(100.0, 100.0, toroidal=True)
    pos = np.array([[50.0, 50.0]])
    vel = np.array([[1.0, 0.0]])
    food = np.array([[60.0, 50.0]])
    x = sensors.sense(world, pos, vel, np.array([10.0]), food, sense_range=34.0, e_norm=100.0)
    assert x.shape == (1, sensors.n_inputs())


def test_food_ahead_lights_front_sector():
    """Food straight ahead must register in the forward sector, not behind."""
    world = World(200.0, 200.0, toroidal=False)
    pos = np.array([[100.0, 100.0]])
    vel = np.array([[1.0, 0.0]])              # facing +x
    ahead = sensors.sense(world, pos, vel, np.array([0.0]),
                          np.array([[110.0, 100.0]]), sense_range=34.0, e_norm=100.0)
    behind = sensors.sense(world, pos, vel, np.array([0.0]),
                           np.array([[90.0, 100.0]]), sense_range=34.0, e_norm=100.0)
    front_sector = 3                          # angle 0 -> sector 3 of 6
    assert ahead[0, front_sector] > 0.6       # 1 - 10/34 ~ 0.71
    assert behind[0, front_sector] == 0.0     # nothing ahead when food is behind


def test_energy_channel():
    world = World(100.0, 100.0, toroidal=True)
    pos = np.array([[50.0, 50.0]])
    vel = np.array([[1.0, 0.0]])
    x = sensors.sense(world, pos, vel, np.array([50.0]), np.empty((0, 2)),
                      sense_range=34.0, e_norm=100.0)
    assert abs(x[0, -1] - 0.5) < 1e-9         # energy 50 / norm 100
