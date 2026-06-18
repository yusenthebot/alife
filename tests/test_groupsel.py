from dataclasses import replace

import numpy as np

from alife.groupsel import GroupSelConfig, assortment_sweep, evolve


def test_simpsons_paradox():
    """Global cooperation rises while it declines within every group."""
    cfg = GroupSelConfig(generations=50)
    r = evolve(cfg, seed=0)
    assert r["coop_fraction"][-1] > r["coop_fraction"][0] + 0.2   # up in the whole
    assert np.all(r["within_group_dp"] <= 1e-6)                   # down in every part
    assert r["within_group_dp"].mean() < -0.005


def test_random_groups_kill_cooperation():
    cfg = GroupSelConfig(generations=50, assortment=0.0)
    r = evolve(cfg, seed=0)
    assert r["coop_fraction"][-1] < 0.1


def test_assortment_threshold_is_monotone():
    cfg = GroupSelConfig(generations=40)
    sweep = assortment_sweep(cfg, [0.0, 0.15, 0.4])
    assert sweep[0] < sweep[1] <= sweep[2] + 1e-9
    assert sweep[0] < 0.1 and sweep[-1] > 0.8


def test_assorted_beats_random_across_seeds():
    cfg = GroupSelConfig(generations=50)
    for seed in range(3):
        hi = evolve(cfg, seed)["coop_fraction"][-1]
        lo = evolve(replace(cfg, assortment=0.0), seed)["coop_fraction"][-1]
        assert hi > lo + 0.5


def test_no_benefit_no_cooperation():
    """With zero benefit, cooperation is pure cost and cannot be favored."""
    cfg = GroupSelConfig(generations=50, benefit=0.0)
    r = evolve(cfg, seed=0)
    assert r["coop_fraction"][-1] < 0.1


def test_reproducible():
    cfg = GroupSelConfig(generations=30)
    a = evolve(cfg, seed=2)["coop_fraction"]
    b = evolve(cfg, seed=2)["coop_fraction"]
    assert np.array_equal(a, b)
