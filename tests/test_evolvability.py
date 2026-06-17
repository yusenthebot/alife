"""Tests for evolution of evolvability: the mutation rate evolves down in a
static environment and stays high under a moving optimum."""

from __future__ import annotations

import numpy as np

from alife.evolvability import EvolvabilityConfig, evolve


def test_static_environment_lowers_mutation_rate():
    cfg = EvolvabilityConfig()
    sigma, fit = evolve(cfg, moving=False, seed=0)
    assert sigma[-1] < sigma[0] * 0.5, f"sigma should fall in a static env: {sigma[0]:.3f}->{sigma[-1]:.3f}"
    assert fit[-1] > 0.8, "should sit near the optimum"


def test_moving_optimum_keeps_mutation_rate_higher():
    cfg = EvolvabilityConfig()
    s_static, _ = evolve(cfg, moving=False, seed=0)
    s_moving, _ = evolve(cfg, moving=True, seed=0)
    assert s_moving[-1] > s_static[-1] * 3, \
        f"moving env should keep sigma higher: static {s_static[-1]:.3f} vs moving {s_moving[-1]:.3f}"


def test_robust_across_seeds():
    cfg = EvolvabilityConfig()
    for s in (0, 1, 2):
        st, _ = evolve(cfg, moving=False, seed=s)
        mv, _ = evolve(cfg, moving=True, seed=s)
        assert mv[-1] > st[-1], f"seed {s}: moving sigma should exceed static"
