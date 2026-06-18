import numpy as np

from alife.baksneppen import (
    run, avalanche_sizes, power_law_fit, threshold_estimate, activity_spacetime, F_C_1D,
)


def test_fitness_in_range_and_neighbours_mutate():
    r = run(n=50, steps=2000, seed=0)
    assert np.all((r["f"] >= 0) & (r["f"] <= 1))
    assert r["min_trace"].shape == (2000,)


def test_self_organized_gap():
    # steady state: most species sit ABOVE f_c, only a few active below
    r = run(n=300, steps=200_000, seed=1)
    assert (r["f"] > F_C_1D).mean() > 0.85           # the self-organized gap
    assert (r["f"] < 0.3).mean() < 0.15              # only a small active minority is low


def test_threshold_near_critical():
    r = run(n=300, steps=200_000, seed=2)
    fc = threshold_estimate(r["min_trace"])
    assert 0.55 < fc < 0.72                          # self-organizes near the 1D critical ~0.667


def test_avalanches_power_law_and_grow_to_criticality():
    r = run(n=300, steps=300_000, seed=3)
    small = avalanche_sizes(r["min_trace"], 0.45)
    big = avalanche_sizes(r["min_trace"], 0.62)
    assert big.max() > small.max()                   # avalanches diverge as f0 -> f_c
    _, _, slope = power_law_fit(big, smin=1, smax=50_000)
    assert -2.0 < slope < -0.7                       # scale-free distribution (SOC exponent)


def test_punctuation_is_sparse():
    # activity is bursty/localized: most space-time cells are quiet
    grid, _ = activity_spacetime(200, 100_000, seed=0)
    assert (grid == 0).mean() > 0.6                  # long stasis dominates


def test_reproducible():
    a = run(n=80, steps=5000, seed=7)["min_trace"]
    b = run(n=80, steps=5000, seed=7)["min_trace"]
    assert np.allclose(a, b)
