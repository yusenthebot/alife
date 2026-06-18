import numpy as np

from alife.spatialcoop import SpatialCoopConfig, b_sweep, run


def test_spatial_sustains_cooperation():
    cfg = SpatialCoopConfig(steps=150)
    r = run(cfg, well_mixed=False, seed=0)
    assert np.mean(r["coop_fraction"][-30:]) > 0.2     # cooperation persists


def test_well_mixed_collapses():
    cfg = SpatialCoopConfig(steps=150)
    r = run(cfg, well_mixed=True, seed=0)
    assert np.mean(r["coop_fraction"][-30:]) < 0.02    # defection wins

def test_spatial_beats_well_mixed_across_seeds():
    cfg = SpatialCoopConfig(steps=150)
    for seed in range(3):
        sp = np.mean(run(cfg, False, seed)["coop_fraction"][-30:])
        wm = np.mean(run(cfg, True, seed)["coop_fraction"][-30:])
        assert sp > wm + 0.15


def test_high_temptation_kills_cooperation_even_spatially():
    """Above the spatial-reciprocity threshold, even clustering can't save it."""
    cfg = SpatialCoopConfig(steps=150, b=1.95)
    r = run(cfg, well_mixed=False, seed=0)
    assert np.mean(r["coop_fraction"][-30:]) < 0.1


def test_b_sweep_is_monotone_ish():
    """Higher temptation -> less cooperation."""
    cfg = SpatialCoopConfig(steps=120)
    sweep = b_sweep(cfg, [1.3, 1.6, 1.9])
    assert sweep[0] > sweep[1] > sweep[2]


def test_snapshots_and_shape():
    cfg = SpatialCoopConfig(size=40, steps=30)
    r = run(cfg, well_mixed=False, seed=0)
    assert r["final"].shape == (40, 40)
    assert cfg.steps in r["snaps"]


def test_reproducible():
    cfg = SpatialCoopConfig(steps=60)
    a = run(cfg, False, 1)["coop_fraction"]
    b = run(cfg, False, 1)["coop_fraction"]
    assert np.array_equal(a, b)
