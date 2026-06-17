"""Tests for the continuous predator–prey ecosystem (lifecycle mechanics).

Coexistence itself is verified in the run (REAL-VERIFY); these pin down the
mechanics that make it possible: grazing, predation, digestion cooldown,
reproduction, death, and consistent dynamic-array bookkeeping for two species.
"""

from __future__ import annotations

import numpy as np

from alife.predprey import PredPreyConfig, PredPreyEcosystem

FIELDS = ("pos", "head", "vel", "energy", "brains", "age", "cooldown")


def _consistent(sp: dict) -> bool:
    n = sp["pos"].shape[0]
    return all(sp[f].shape[0] == n for f in FIELDS)


def test_step_keeps_species_consistent():
    eco = PredPreyEcosystem(PredPreyConfig(), seed=0)
    for _ in range(40):
        eco.step()
        assert _consistent(eco.prey) and _consistent(eco.pred)
    assert np.all(np.isfinite(eco.prey["pos"])) and np.all(np.isfinite(eco.pred["energy"]))


def test_food_regrows():
    eco = PredPreyEcosystem(PredPreyConfig(), seed=1)
    eco.food = eco.food[:5]
    before = eco.food.shape[0]
    eco.step()
    assert eco.food.shape[0] > before


def test_predation_removes_prey_and_sets_cooldown():
    eco = PredPreyEcosystem(PredPreyConfig(), seed=2)
    # park each predator right on a distinct prey, then run the catch step directly
    npd = eco.pred["pos"].shape[0]
    eco.pred["pos"][:] = eco.prey["pos"][:npd]
    eco.pred["cooldown"][:] = 0
    n_prey_before = eco.prey["pos"].shape[0]
    eco._catch()
    assert eco.prey["pos"].shape[0] == n_prey_before - npd  # each predator caught its prey
    assert (eco.pred["cooldown"] > 0).all()  # all predators are now digesting


def test_cooldown_blocks_catching():
    eco = PredPreyEcosystem(PredPreyConfig(), seed=6)
    npd = eco.pred["pos"].shape[0]
    eco.pred["pos"][:] = eco.prey["pos"][:npd]
    eco.pred["cooldown"][:] = 5  # all digesting -> cannot catch
    n_prey_before = eco.prey["pos"].shape[0]
    eco._catch()
    assert eco.prey["pos"].shape[0] == n_prey_before  # no catches while digesting


def test_reproduction_grows_population():
    eco = PredPreyEcosystem(PredPreyConfig(n_prey0=40), seed=3)
    eco.prey["energy"][:] = eco.cfg.prey_e_repro + 5.0
    n0 = eco.prey["pos"].shape[0]
    eco._reproduce(eco.prey, eco.cfg.prey_e_repro, eco.cfg.prey_cap)
    assert eco.prey["pos"].shape[0] > n0
    assert _consistent(eco.prey)


def test_starvation_and_age_cull():
    eco = PredPreyEcosystem(PredPreyConfig(n_pred0=30), seed=4)
    eco.pred["energy"][:10] = -1.0
    eco._mask(eco.pred, eco.pred["energy"] > 0)
    assert eco.pred["pos"].shape[0] == 20
    assert _consistent(eco.pred)


def test_energy_capped():
    eco = PredPreyEcosystem(PredPreyConfig(), seed=5)
    for _ in range(30):
        eco.step()
    assert eco.prey["energy"].max() <= eco.cfg.prey_e_max + 1e-6
    assert eco.pred["energy"].max() <= eco.cfg.pred_e_max + 1e-6
