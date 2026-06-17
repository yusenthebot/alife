"""Tests for sympatric speciation: assortative mating splits one population into
two species; random mating does not."""

from __future__ import annotations

import numpy as np

from alife.speciation import (SpeciationConfig, bimodality_coefficient, count_species,
                              evolve, fitness)


def test_fitness_is_disruptive():
    # specialists (0 and 1) beat the generalist (0.5)
    f = fitness(np.array([0.0, 0.5, 1.0]), sigma=0.17)
    assert f[0] > f[1] and f[2] > f[1]


def test_bimodality_coefficient_detects_two_clusters():
    rng = np.random.default_rng(0)
    bimodal = np.concatenate([rng.normal(0, 0.03, 300), rng.normal(1, 0.03, 300)])
    unimodal = rng.normal(0.5, 0.05, 600)
    assert bimodality_coefficient(bimodal) > 0.7
    assert bimodality_coefficient(unimodal) < 0.555


def test_assortative_mating_speciates():
    cfg = SpeciationConfig()
    hist, bc = evolve(cfg, assortative=True, seed=0)
    final = hist[-1]
    assert count_species(final) == 2, "assortative mating should yield two species"
    assert bc[-1] > 0.6, f"final distribution should be bimodal, BC={bc[-1]:.2f}"
    assert (final < 0.25).mean() > 0.2 and (final > 0.75).mean() > 0.2


def test_random_mating_does_not_cleanly_speciate():
    cfg = SpeciationConfig()
    _, bc_assort = evolve(cfg, assortative=True, seed=1)
    _, bc_random = evolve(cfg, assortative=False, seed=1)
    # assortative ends more bimodal than random (reproductive isolation matters)
    assert bc_assort[-1] > bc_random[-1]
