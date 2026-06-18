import numpy as np

from alife.hypercycle import (
    SpatialConfig, replicator_hypercycle, replicator_independent,
    spatial_hypercycle, persistent, amplitude, survivors, area_fractions, spatial_structure,
)


def test_simplex_conserved():
    tr = replicator_hypercycle(5, steps=2000, dt=0.02, seed=0)
    assert np.allclose(tr.sum(axis=1), 1.0, atol=1e-9)
    assert np.all(tr >= -1e-12)


def test_small_cycle_settles_large_cycle_oscillates():
    # n=3 -> stable fixed point (no oscillation); n=5 -> sustained limit cycle
    assert amplitude(replicator_hypercycle(3, steps=30000, seed=0)) < 0.05
    assert amplitude(replicator_hypercycle(5, steps=30000, seed=0)) > 0.3


def test_hypercycle_coexists_independent_excludes():
    hc = replicator_hypercycle(5, steps=30000, seed=0)
    ind = replicator_independent(5, steps=40000, k=1 + 0.3 * np.arange(5) / 5, seed=1)
    assert persistent(hc) == 5                      # cooperation: all coexist
    assert persistent(ind) == 1                     # exclusion: one winner


def test_parasite_collapses_well_mixed():
    par = replicator_hypercycle(5, steps=30000, seed=0, parasite_k=1.0, parasite_host=0)
    assert persistent(par[:, :5]) < 5               # a cycle member is lost
    assert par[-1, 5] > 0.1                          # parasite establishes


def test_spatial_forms_waves_and_coexists():
    cfg = SpatialConfig(n=5, size=120, death=0.06, cat=2.0, empty_w=0.3)
    r = spatial_hypercycle(cfg, steps=800, seed=3)
    fr = area_fractions(r["state"], 5)
    assert (fr > 0.02).all()                         # all 5 coexist spatially
    assert 0.4 < (r["state"] >= 0).mean() < 1.0      # alive, not full/dead
    assert spatial_structure(r["state"], 5) > 0.1    # wave fronts (not a uniform domain)


def test_spatial_coexistence_is_balanced():
    # rotating waves keep all 5 species near 1/5 each (no spatial competitive exclusion)
    cfg = SpatialConfig(n=5, size=120, death=0.06, cat=2.0, empty_w=0.3)
    r = spatial_hypercycle(cfg, steps=1000, seed=3)
    fr = area_fractions(r["state"], 5)
    assert (fr > 0.05).all()                         # every species holds a real share
    assert fr.max() - fr.min() < 0.18                # roughly balanced (cyclic symmetry preserved)


def test_reproducible():
    a = replicator_hypercycle(5, steps=500, seed=2)
    b = replicator_hypercycle(5, steps=500, seed=2)
    assert np.allclose(a, b)
