import numpy as np

from alife.kpz import (random_deposition, ballistic_deposition, growth_exponent,
                       mean_growth_exponent, saturation_width, roughness_exponent)


def test_random_deposition_beta_half():
    r = random_deposition(L=400, layers=1500, seed=0)
    assert abs(growth_exponent(r["t"], r["w"]) - 0.5) < 0.08    # uncorrelated -> w ~ t^{1/2}


def test_ballistic_beta_below_random():
    # KPZ: lateral sticking correlates columns -> sub-1/2 growth exponent (single seed noisy)
    bmean, _ = mean_growth_exponent("ballistic", L=800, layers=1000, seeds=4)
    assert 0.2 < bmean < 0.45                                   # ~1/3, clearly below 0.5


def test_ballistic_beta_near_one_third_averaged():
    bmean, _ = mean_growth_exponent("ballistic", L=1000, layers=1200, seeds=5)
    assert abs(bmean - 1 / 3) < 0.1                             # seed-averaged ~ KPZ 1/3


def test_ballistic_saturates_random_does_not():
    bd = ballistic_deposition(L=120, layers=1600, seed=0)       # small L saturates
    rd = random_deposition(L=120, layers=1600, seed=0)
    # ballistic width plateaus: late growth is small; random keeps growing ~ sqrt(t)
    bw = bd["w"]; rw = rd["w"]
    assert bw[-1] / bw[len(bw) // 2] < 1.4                      # ballistic ~ saturated
    assert rw[-1] / rw[len(rw) // 2] > 1.3                      # random still climbing


def test_roughness_exponent_positive():
    Ls, wsat, alpha = roughness_exponent((32, 64, 128), seed=0)
    assert (np.diff(wsat) > 0).all()                            # bigger system -> rougher at saturation
    assert 0.2 < alpha < 0.8                                    # KPZ alpha ~ 1/2


def test_reproducible():
    a = ballistic_deposition(L=100, layers=200, seed=7)["w"]
    b = ballistic_deposition(L=100, layers=200, seed=7)["w"]
    assert np.array_equal(a, b)
