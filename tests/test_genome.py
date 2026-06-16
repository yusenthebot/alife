"""Genome invariants: bounds and heritable variation."""

from __future__ import annotations

import numpy as np

from alife import genome as gn


def test_random_within_bounds():
    g = gn.random_genomes(500, np.random.default_rng(0))
    assert g.shape == (500, gn.N_TRAITS)
    assert (g >= gn.TRAIT_LO).all()
    assert (g <= gn.TRAIT_HI).all()


def test_mutate_stays_within_bounds():
    rng = np.random.default_rng(1)
    g = gn.random_genomes(500, rng)
    for _ in range(20):
        g = gn.mutate(g, gn.MutationConfig(rate=1.0, sigma_frac=0.5), rng)
    assert (g >= gn.TRAIT_LO - 1e-9).all()
    assert (g <= gn.TRAIT_HI + 1e-9).all()


def test_mutate_produces_variation():
    rng = np.random.default_rng(2)
    parents = np.tile((gn.TRAIT_LO + gn.TRAIT_HI) / 2, (200, 1))
    kids = gn.mutate(parents, gn.MutationConfig(), rng)
    assert not np.allclose(kids, parents)
    # mean is preserved in expectation (no directional bias from mutation alone)
    assert np.allclose(kids.mean(0), parents.mean(0), atol=0.15 * (gn.TRAIT_HI - gn.TRAIT_LO))


def test_column_shape():
    g = gn.random_genomes(10, np.random.default_rng(0))
    assert gn.column(g, gn.W_FOOD).shape == (10, 1)
