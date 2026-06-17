"""Tests for Red Queen host-parasite coevolution (matching-allele)."""

from __future__ import annotations

import numpy as np

from alife.redqueen import RedQueenConfig, evolve, host_parasite_lag, oscillation_strength


def test_frequencies_are_valid_distributions():
    cfg = RedQueenConfig()
    H, P = evolve(cfg, seed=0)
    assert np.allclose(H.sum(1), 1, atol=1e-6) and np.allclose(P.sum(1), 1, atol=1e-6)
    assert (H >= 0).all() and (P >= 0).all()


def test_sustained_oscillation():
    cfg = RedQueenConfig()
    H, _ = evolve(cfg, seed=0)
    # a converged equilibrium would have ~0 variance; the Red Queen keeps moving
    assert oscillation_strength(H) > 0.05, "allele frequencies should keep oscillating"
    # and span a wide range (no allele permanently fixed or lost)
    assert H[100:, 0].max() - H[100:, 0].min() > 0.2


def test_parasites_lag_hosts():
    cfg = RedQueenConfig()
    H, P = evolve(cfg, seed=0)
    assert host_parasite_lag(H, P) > 0, "parasites should chase (lag behind) hosts"
