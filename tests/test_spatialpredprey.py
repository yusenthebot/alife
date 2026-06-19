import numpy as np

from alife.spatialpredprey import (simulate, well_mixed, equilibrium, fluctuation,
                                   min_density, PPConfig)

FAST = PPConfig(n=96, steps=3000)


def test_equilibrium_formula():
    Us, Vs = equilibrium(FAST)
    assert abs(Us - FAST.gamma * FAST.alpha / (FAST.beta - FAST.gamma)) < 1e-9
    assert 0 < Us < 1 and Vs > 0


def test_well_mixed_is_boom_bust():
    wm = well_mixed(FAST, seed=1)
    assert fluctuation(wm["mu"]) > 0.1                      # large-amplitude limit cycle
    assert min_density(wm["mu"]) < 0.05                     # crashes near extinction


def test_spatial_persists_with_structure():
    sp = simulate(FAST, seed=1)
    assert sp["U"].mean() > 0.05 and sp["V"].mean() > 0.05  # both persist
    assert sp["U"].std() > 0.03                             # patchy/wave heterogeneity


def test_space_stabilizes_coexistence():
    wm = well_mixed(FAST, seed=1)
    sp = simulate(FAST, seed=1)
    assert fluctuation(sp["mu"]) < 0.6 * fluctuation(wm["mu"])   # smaller global swings
    assert min_density(sp["mu"]) > 2 * min_density(wm["mu"])     # higher floor (safer)


def test_fields_nonnegative_finite():
    sp = simulate(PPConfig(n=64, steps=800), seed=2)
    assert np.isfinite(sp["U"]).all() and (sp["U"] >= 0).all()
    assert np.isfinite(sp["V"]).all() and (sp["V"] >= 0).all()


def test_reproducible():
    a = simulate(PPConfig(n=48, steps=300), seed=7)["mu"]
    b = simulate(PPConfig(n=48, steps=300), seed=7)["mu"]
    assert np.array_equal(a, b)
