import numpy as np
from dataclasses import replace

from alife.mips import simulate, density_cv, MIPSConfig

BASE = MIPSConfig(steps=500)     # n=4000 default; MIPS needs enough particles to develop (~0.2s/run)


def test_density_dependent_speed_phase_separates():
    r = simulate(BASE, seed=1)
    assert density_cv(r) > 3.0                          # strong inhomogeneity = clusters + voids


def test_constant_speed_control_stays_homogeneous():
    # speed never drops with density -> an active gas, no MIPS
    r = simulate(replace(BASE, rho_star=1e9), seed=1)
    assert density_cv(r) < 1.0


def test_passive_control_stays_homogeneous():
    # no self-propulsion -> pure diffusion, homogeneous
    r = simulate(replace(BASE, v0=0.0), seed=1)
    assert density_cv(r) < 1.0


def test_clustering_increases_with_activity():
    lo = density_cv(simulate(replace(BASE, v0=0.0), seed=2))
    hi = density_cv(simulate(replace(BASE, v0=4.0), seed=2))
    assert hi > lo + 2.0                                # MIPS onset with self-propulsion


def test_particles_conserved_and_in_box():
    r = simulate(BASE, seed=3)
    assert r["pos"].shape == (BASE.n, 2)
    assert r["pos"].min() >= 0 and r["pos"].max() <= BASE.box
    assert r["counts"].sum() == BASE.n                  # every particle binned exactly once


def test_reproducible():
    a = simulate(replace(BASE, steps=120), seed=7)["pos"]
    b = simulate(replace(BASE, steps=120), seed=7)["pos"]
    assert np.array_equal(a, b)
