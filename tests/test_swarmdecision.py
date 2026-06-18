import numpy as np

from alife.swarmdecision import SwarmConfig, simulate, decision, decided, accuracy


def test_conservation():
    cfg = SwarmConfig(n_bees=500)
    r = simulate([1.2, 1.0], cfg, steps=100, seed=0)
    total = r["frac"].sum(axis=1) + r["uncommitted"]
    assert np.allclose(total, 1.0)                    # every bee is uncommitted or at one site


def test_value_sensitive_best_wins():
    cfg = SwarmConfig()
    r = simulate([1.5, 1.0], cfg, steps=600, seed=0)
    assert decision(r["frac"]) == 0                   # the better site (index 0) wins


def test_cross_inhibition_breaks_deadlock():
    cfg = SwarmConfig()
    r = simulate([1.2, 1.2], cfg, steps=700, seed=1, cross_inhibition=True)
    f = np.sort(r["frac"][-1])[::-1]
    assert f[0] > 0.8 and f[1] < 0.1                  # decisive consensus, rival suppressed


def test_without_inhibition_stays_split():
    cfg = SwarmConfig()
    r = simulate([1.2, 1.2], cfg, steps=700, seed=1, cross_inhibition=False)
    f = np.sort(r["frac"][-1])[::-1]
    assert f[1] > 0.2                                 # the loser keeps a big share — swarm divided


def test_three_sites_pick_best():
    cfg = SwarmConfig()
    r = simulate([1.6, 1.0, 1.2], cfg, steps=700, seed=3)
    assert decision(r["frac"]) == 0                   # best of three


def test_accuracy_high_for_unequal():
    cfg = SwarmConfig()
    assert accuracy([1.5, 1.0], cfg, trials=12, steps=600, seed=2) > 0.8


def test_reproducible():
    cfg = SwarmConfig(n_bees=300)
    a = simulate([1.3, 1.0], cfg, steps=200, seed=4)["frac"]
    b = simulate([1.3, 1.0], cfg, steps=200, seed=4)["frac"]
    assert np.allclose(a, b)
