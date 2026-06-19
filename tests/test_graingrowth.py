import numpy as np
from dataclasses import replace

from alife.graingrowth import (GrainConfig, run, bond_density, count_grains,
                               coarsening_exponent)

BASE = GrainConfig(L=100, Q=64, T=0.6, steps=120, seed=1)
LOG = [5, 15, 40, 120]


def test_boundary_length_decays():
    r = run(BASE, log_at=LOG)
    assert r["bond"][-1] < 0.4 * r["bond"][0]              # boundaries retract as grains coarsen


def test_grain_count_decreases():
    r = run(BASE, log_at=LOG)
    assert r["ngrains"][-1] < 0.3 * r["ngrains"][0]        # small grains vanish into big ones


def test_mean_grain_area_grows():
    r = run(BASE, log_at=LOG)
    area0 = BASE.L ** 2 / r["ngrains"][0]
    area1 = BASE.L ** 2 / r["ngrains"][-1]
    assert area1 > 5 * area0                               # parabolic-style coarsening


def test_power_law_and_two_measures_consistent():
    r = run(BASE, log_at=LOG)
    eb = coarsening_exponent(r["t"], r["bond"])            # bond ~ 1/R ~ t^-x
    eg = coarsening_exponent(r["t"], r["ngrains"])         # grains ~ 1/area ~ t^-2x
    assert eb < -0.25 and eg < -0.5                        # clear power-law decay
    assert abs(eg / eb - 2.0) < 0.5                        # area ~ R^2 -> grain exp = 2x bond exp


def test_greedy_pins_no_coarsening():
    r = run(replace(BASE, greedy=True), log_at=LOG)        # no thermal noise -> lattice pinning
    assert r["bond"][-1] > 0.9 * r["bond"][1]              # boundaries freeze (plateau), not coarsen


def test_annealing_beats_greedy():
    a = run(BASE, log_at=[120])
    g = run(replace(BASE, greedy=True), log_at=[120])
    assert a["bond"][-1] < 0.5 * g["bond"][-1]             # thermal anneal coarsens far past pinned


def test_field_valid():
    r = run(replace(BASE, steps=20))
    assert r["s"].min() >= 0 and r["s"].max() < BASE.Q


def test_reproducible():
    a = run(replace(BASE, steps=30))["s"]
    b = run(replace(BASE, steps=30))["s"]
    assert np.array_equal(a, b)
