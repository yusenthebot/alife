import numpy as np

from alife.lanes import LaneConfig, run, lane_order, init
from dataclasses import replace


def test_lane_order_on_controls():
    rng = np.random.default_rng(0)
    L = 40.0
    pos = rng.uniform(0, L, (500, 2))
    laned = np.where((pos[:, 1] // 4).astype(int) % 2 == 0, 1.0, -1.0)   # species in y-bands
    mixed = rng.choice([1.0, -1.0], 500)
    assert lane_order(pos, laned, L) > 0.7
    assert lane_order(pos, mixed, L) < 0.35


def test_counter_flow_forms_lanes():
    r = run(replace(LaneConfig(N=500, steps=2500, seed=1)))
    assert r["order"][-20:].mean() > 0.55


def test_no_drive_stays_mixed():
    r = run(replace(LaneConfig(N=500, steps=2500, seed=1, v0=0.0)))
    assert r["order"][-20:].mean() < 0.3


def test_noise_melts_lanes():
    laned = run(replace(LaneConfig(N=500, steps=2500, seed=1, noise=0.3)))["order"][-20:].mean()
    melted = run(replace(LaneConfig(N=500, steps=2500, seed=1, noise=2.5)))["order"][-20:].mean()
    assert laned > melted


def test_order_rises_over_time():
    r = run(replace(LaneConfig(N=500, steps=2500, seed=1)))
    assert r["order"][-20:].mean() > r["order"][:20].mean() + 0.2


def test_species_conserved():
    cfg = replace(LaneConfig(N=400, steps=800, seed=2))
    r = run(cfg)
    assert int((r["species"] > 0).sum()) == cfg.N // 2


def test_positions_stay_in_box():
    cfg = replace(LaneConfig(N=400, steps=800, seed=2))
    r = run(cfg)
    assert r["pos"].min() >= 0 and r["pos"].max() < cfg.L


def test_reproducible():
    a = run(replace(LaneConfig(N=300, steps=400, seed=5)))["pos"]
    b = run(replace(LaneConfig(N=300, steps=400, seed=5)))["pos"]
    assert np.array_equal(a, b)
