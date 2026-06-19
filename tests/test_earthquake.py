import numpy as np

from alife.earthquake import simulate, size_distribution, gr_exponent, big_quake_fraction


def test_soc_regime_is_power_law():
    s = simulate(L=40, alpha=0.22, n_quakes=4000, seed=1, warmup=800)
    tau = gr_exponent(s)
    assert 1.3 < tau < 2.6                                  # Gutenberg-Richter exponent range
    assert s.max() > 50                                     # broad scaling range (not just tiny quakes)


def test_strong_dissipation_only_small_quakes():
    s = simulate(L=40, alpha=0.10, n_quakes=3000, seed=1, warmup=600)
    assert s.max() < 30                                     # very dissipative -> no large ruptures
    assert big_quake_fraction(s, 40) < 0.05


def test_conservation_grows_big_quakes():
    lo = big_quake_fraction(simulate(L=40, alpha=0.17, n_quakes=3000, seed=1, warmup=600), 40)
    hi = big_quake_fraction(simulate(L=40, alpha=0.25, n_quakes=3000, seed=1, warmup=600), 40)
    assert hi > lo + 0.3                                    # more conservation -> bigger ruptures


def test_quakes_are_positive_integers():
    s = simulate(L=30, alpha=0.2, n_quakes=500, seed=2, warmup=200)
    assert (s >= 1).all() and s.dtype.kind in "iu"


def test_size_distribution_decreasing():
    s = simulate(L=40, alpha=0.22, n_quakes=4000, seed=3, warmup=800)
    cx, cy = size_distribution(s)
    assert cy[0] > cy[-1]                                   # small quakes far more common than large


def test_reproducible():
    a = simulate(L=30, alpha=0.2, n_quakes=300, seed=7, warmup=100)
    b = simulate(L=30, alpha=0.2, n_quakes=300, seed=7, warmup=100)
    assert np.array_equal(a, b)
