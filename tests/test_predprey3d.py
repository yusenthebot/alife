"""Tests for the continuous 3D ecosystem (lifecycle mechanics in the volume)."""

from __future__ import annotations

import numpy as np

from alife.predprey3d import PredPrey3DConfig, PredPrey3DEcosystem

FIELDS = ("pos", "vel", "energy", "brains", "age", "cooldown")


def _consistent(sp):
    n = sp["pos"].shape[0]
    return all(sp[k].shape[0] == n for k in FIELDS) and sp["pos"].shape[1] == 3


def test_step_keeps_species_consistent():
    eco = PredPrey3DEcosystem(PredPrey3DConfig(), seed=0)
    for _ in range(30):
        eco.step()
        assert _consistent(eco.prey) and _consistent(eco.pred)
    assert np.all(np.isfinite(eco.prey["pos"])) and np.all(np.isfinite(eco.pred["energy"]))


def test_positions_in_box():
    eco = PredPrey3DEcosystem(PredPrey3DConfig(), seed=1)
    for _ in range(20):
        eco.step()
    assert eco.prey["pos"].min() >= 0 and eco.prey["pos"].max() <= eco.cfg.world.size + 1e-6


def test_predation_with_cooldown():
    eco = PredPrey3DEcosystem(PredPrey3DConfig(), seed=2)
    npd = eco.pred["pos"].shape[0]
    eco.pred["pos"][:] = eco.prey["pos"][:npd]
    eco.pred["cooldown"][:] = 0
    n_before = eco.prey["pos"].shape[0]
    eco._catch()
    assert eco.prey["pos"].shape[0] == n_before - npd
    assert (eco.pred["cooldown"] > 0).all()


def test_reproduction_and_energy_cap():
    eco = PredPrey3DEcosystem(PredPrey3DConfig(n_prey0=40), seed=3)
    eco.prey["energy"][:] = eco.cfg.prey_e_repro + 5
    n0 = eco.prey["pos"].shape[0]
    eco._reproduce(eco.prey, eco.cfg.prey_e_repro, eco.cfg.prey_cap)
    assert eco.prey["pos"].shape[0] > n0 and _consistent(eco.prey)
    for _ in range(10):
        eco.step()
    assert eco.prey["energy"].max() <= eco.cfg.prey_e_max + 1e-6
