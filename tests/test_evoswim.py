import numpy as np

from alife.evoswim import gait_speed, evolve, random_baseline, _stabilize, LO, HI, MACH_CAP

FAST = dict(nx=120, ny=70, length=36, steps=900, mass=400.0)   # lean eval for tests


def test_stabilize_enforces_bounds_and_mach():
    g = _stabilize(np.array([20.0, 0.05, 100.0]))              # over all bounds
    assert (g >= LO).all() and (g <= HI).all()
    assert g[0] * 2 * np.pi * g[1] <= MACH_CAP + 1e-9          # low-Mach constraint held


def test_gait_speed_finite_nonnegative():
    s = gait_speed([6.0, 0.003, 40.0], **FAST)
    assert np.isfinite(s) and s >= 0.0


def test_speed_varies_with_gait():
    weak = gait_speed([1.5, 0.001, 30.0], **FAST)
    strong = gait_speed([8.0, 0.01, 45.0], **FAST)
    assert strong > weak + 1e-3                                # a real fitness landscape exists


def test_evolution_beats_initial_and_random():
    res = evolve(gens=5, pop=6, seed=0, **FAST)
    assert res["best_fitness"] >= res["best_hist"][0]          # best is monotone non-decreasing
    base = random_baseline(n=6, seed=3, **FAST)
    assert res["best_fitness"] >= np.median(base)              # evolved at least beats typical random


def test_best_genome_is_stable_and_in_bounds():
    res = evolve(gens=3, pop=6, seed=1, **FAST)
    g = res["best_genome"]
    assert (g >= LO).all() and (g <= HI).all()
    assert g[0] * 2 * np.pi * g[1] <= MACH_CAP + 1e-9


def test_reproducible():
    a = evolve(gens=2, pop=4, seed=5, **FAST)["best_hist"]
    b = evolve(gens=2, pop=4, seed=5, **FAST)["best_hist"]
    assert np.array_equal(a, b)
