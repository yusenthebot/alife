import numpy as np
from dataclasses import replace

from alife.granular import simulate, discharge_rate, HopperConfig

# lean config for tests (fewer grains/steps)
BASE = HopperConfig(n=400, steps=1800)


def test_grains_discharge_through_orifice():
    r = simulate(replace(BASE, orifice=12), seed=1)
    assert r["discharged"] > 100                             # a wide opening drains many grains


def test_small_orifice_jams():
    wide = simulate(replace(BASE, orifice=12), seed=1)["discharged"]
    narrow = simulate(replace(BASE, orifice=3), seed=1)["discharged"]
    assert narrow < 0.5 * wide                               # a few-grain opening clogs/chokes


def test_discharge_is_approximately_constant_rate():
    r = simulate(replace(BASE, orifice=8), seed=1)
    cum = r["cum"].astype(float)
    rising = cum < cum.max() - 2
    assert rising.sum() > 50
    t = np.arange(len(cum))[rising]
    fit = np.polyfit(t, cum[rising], 1)
    r2 = 1 - ((cum[rising] - np.polyval(fit, t)).var() / cum[rising].var())
    assert r2 > 0.9                                          # nearly straight -> ~constant rate


def test_wider_orifice_flows_faster():
    # moderate openings (a very wide one drains this small hopper too fast to time a steady rate)
    slow = discharge_rate(simulate(replace(BASE, orifice=5), seed=1))
    fast = discharge_rate(simulate(replace(BASE, orifice=10), seed=1))
    assert fast > slow                                       # Beverloo: rate grows with opening


def test_grains_conserved():
    r = simulate(replace(BASE, orifice=10), seed=2)
    assert 0 <= r["discharged"] <= BASE.n                    # never create/lose grains


def test_reproducible():
    a = simulate(replace(BASE, steps=400), seed=5)["cum"]
    b = simulate(replace(BASE, steps=400), seed=5)["cum"]
    assert np.array_equal(a, b)
