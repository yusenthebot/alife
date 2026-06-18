import numpy as np

from dataclasses import replace

from alife.quasispecies import QuasispeciesConfig, evolve, mu_sweep


def test_master_maintained_below_threshold():
    cfg = QuasispeciesConfig(generations=200)
    r = evolve(cfg, mu=cfg.mu_c * 0.4, seed=0)
    assert r["final_master"] > 0.3


def test_error_catastrophe_above_threshold():
    cfg = QuasispeciesConfig(generations=200)
    r = evolve(cfg, mu=cfg.mu_c * 1.6, seed=0)
    assert r["final_master"] < 0.05            # master sequence lost


def test_zero_mutation_keeps_all_master():
    cfg = QuasispeciesConfig(generations=100)
    r = evolve(cfg, mu=0.0, seed=0)
    assert r["final_master"] > 0.99


def test_sweep_is_decreasing():
    cfg = QuasispeciesConfig(generations=150)
    sw = mu_sweep(cfg, [0.0, cfg.mu_c * 0.5, cfg.mu_c * 1.5])
    assert sw[0] > sw[1] > sw[2]
    assert sw[0] > 0.9 and sw[2] < 0.1


def test_delocalisation_above_threshold():
    """Above the threshold the population sits at the random-sequence baseline ~L/2."""
    cfg = QuasispeciesConfig(generations=200)
    above = evolve(cfg, mu=cfg.mu_c * 1.8, seed=0)
    assert above["mean_hamming"] > cfg.loci * 0.3


def test_threshold_scales_with_log_sigma():
    """Higher fitness advantage tolerates a higher mutation rate (mu_c ~ ln sigma)."""
    lo = replace(QuasispeciesConfig(generations=150), sigma=2.0)
    hi = replace(QuasispeciesConfig(generations=150), sigma=16.0)
    # at a mu fatal for low-sigma, high-sigma may still hold the master
    mu = lo.mu_c * 1.5
    assert evolve(lo, mu=mu, seed=0)["final_master"] < evolve(hi, mu=mu, seed=0)["final_master"]


def test_reproducible():
    cfg = QuasispeciesConfig(generations=80)
    a = evolve(cfg, mu=0.04, seed=3)["master_freq"]
    b = evolve(cfg, mu=0.04, seed=3)["master_freq"]
    assert np.array_equal(a, b)
