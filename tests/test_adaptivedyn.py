import numpy as np

from dataclasses import replace

from alife.adaptivedyn import AdaptiveDynConfig, evolve, n_clusters


def test_branches_when_competition_narrow():
    """sigma_c < sigma_k -> disruptive selection splits the lineage."""
    cfg = AdaptiveDynConfig(generations=700)
    assert n_clusters(evolve(cfg, seed=0)[-1]) >= 2


def test_no_branch_when_competition_wide():
    """sigma_c > sigma_k -> the population stays one cluster at the resource peak."""
    cfg = replace(AdaptiveDynConfig(generations=700), sigma_c=1.6)
    h = evolve(cfg, seed=0)
    assert n_clusters(h[-1]) == 1
    assert abs(h[-1].mean()) < 0.3            # sits near the centre


def test_branching_increases_trait_variance():
    cfg = AdaptiveDynConfig(generations=700)
    h = evolve(cfg, seed=0)
    wide = evolve(replace(cfg, sigma_c=1.6), seed=0)
    assert h[-1].std() > 2 * wide[-1].std()


def test_converges_toward_centre_before_branching():
    """The population first moves from its off-centre start toward the resource peak."""
    cfg = AdaptiveDynConfig(generations=700)
    h = evolve(cfg, seed=0)
    assert abs(h[0].mean()) > 0.4             # starts off-centre (~0.6)
    assert abs(h[h.shape[0] // 6].mean()) < abs(h[0].mean())   # moves toward 0 early


def test_branches_are_symmetric_ish():
    cfg = AdaptiveDynConfig(generations=700)
    h = evolve(cfg, seed=0)[-1]
    assert h.max() > 0.4 and h.min() < -0.4   # clusters on both sides of centre


def test_reproducible():
    cfg = AdaptiveDynConfig(generations=120)
    a = evolve(cfg, seed=3)
    b = evolve(cfg, seed=3)
    assert np.array_equal(a, b)
