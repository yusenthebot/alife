"""Tests for the evolving ecosystem.

The headline test is *selection*: from random genomes, food-attraction is driven
up and metabolism down — fitter trait combinations become common with no fitness
function written anywhere. The rest pin down the lifecycle mechanics that make
that possible (eating, reproduction, death, food regrowth) and the array
bookkeeping a dynamic population needs.
"""

from __future__ import annotations

import numpy as np

from alife import genome as gn
from alife.ecosystem import EcoConfig, Ecosystem
from alife.world import World


def _lengths_match(eco: Ecosystem) -> bool:
    n = eco.pos.shape[0]
    return all(arr.shape[0] == n for arr in (eco.vel, eco.energy, eco.dna, eco.generation, eco.age))


def test_step_keeps_arrays_consistent():
    eco = Ecosystem(EcoConfig(), seed=0)
    for _ in range(40):
        eco.step()
        assert _lengths_match(eco)
    assert np.all(np.isfinite(eco.pos))
    assert np.all(np.isfinite(eco.energy))


def test_eating_gives_energy_and_consumes_food():
    eco = Ecosystem(EcoConfig(), seed=1)
    eco.pos[0] = eco.food[0].copy()          # park creature 0 on a food item
    food_before = eco.food.shape[0]
    e_before = eco.energy[0]
    eco._eat()
    assert eco.energy[0] > e_before
    assert eco.food.shape[0] < food_before


def test_reproduction_grows_population_and_advances_generation():
    eco = Ecosystem(EcoConfig(n0=50), seed=2)
    eco.energy[:] = eco.cfg.e_repro + 10.0   # everyone is rich enough to split
    n_before = eco.pos.shape[0]
    eco._reproduce()
    assert eco.pos.shape[0] > n_before
    assert eco.generation.max() == 1
    assert _lengths_match(eco)


def test_starvation_culls():
    eco = Ecosystem(EcoConfig(n0=50), seed=3)
    eco.energy[:10] = -1.0
    eco._cull()
    assert eco.pos.shape[0] == 40


def test_food_regrows_toward_cap():
    eco = Ecosystem(EcoConfig(), seed=4)
    eco.food = eco.food[:10]
    eco._regrow_food()
    assert eco.food.shape[0] == 10 + eco.cfg.food_regrow


def test_population_cap_respected():
    eco = Ecosystem(EcoConfig(n0=50, pop_cap=70), seed=5)
    eco.energy[:] = eco.cfg.e_repro + 10.0
    eco._reproduce()
    assert eco.pos.shape[0] <= 70


def test_selection_favors_food_seekers():
    """Emergence: directional selection on heritable traits, no fitness fn."""
    cfg = EcoConfig(world=World(150.0, 150.0, toroidal=True), n0=150,
                    pop_cap=650, food_cap=320)
    eco = Ecosystem(cfg, seed=7)
    w_food0 = eco.dna[:, gn.W_FOOD].mean()
    metab0 = eco.dna[:, gn.METABOLISM].mean()
    for _ in range(700):
        eco.step()
        if eco.pos.shape[0] == 0:
            raise AssertionError("population went extinct")
    assert eco.generation.max() >= 4, "needs real generational turnover"
    assert eco.dna[:, gn.W_FOOD].mean() > w_food0 + 0.3, "food-attraction should be selected up"
    assert eco.dna[:, gn.METABOLISM].mean() < metab0 - 0.1, "metabolism should be selected down"
