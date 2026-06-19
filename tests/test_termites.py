import numpy as np

from alife.termites import TermiteConfig, run, clustering, clustering_curve
from dataclasses import replace


def test_clustering_metric_on_controls():
    rng = np.random.default_rng(0)
    flat = rng.poisson(5, (80, 80)).astype(float)
    clumpy = np.zeros((80, 80)); clumpy[20:30, 20:30] = 50; clumpy[55:65, 55:65] = 50
    assert clustering(flat) < 1.5
    assert clustering(clumpy) > 10


def test_stigmergy_builds_mounds():
    r = run(TermiteConfig(steps=3000, k=6.0, seed=1))
    assert clustering(r["M"]) > 2.5            # material clumps into mounds
    assert r["M"].sum() > 0


def test_random_deposition_stays_flat():
    r = run(TermiteConfig(steps=3000, k=0.0, seed=1))
    assert clustering(r["M"]) < 1.5            # no feedback -> uniform floor


def test_feedback_drives_clustering():
    ks, c = clustering_curve([0.0, 3.0, 7.0], replace(TermiteConfig(steps=2500, seed=2)))
    assert c[-1] > 2.0 * c[0]                  # clustering rises with stigmergy strength


def test_pheromone_nonnegative():
    r = run(TermiteConfig(steps=600, k=6.0, seed=3))
    assert r["P"].min() >= 0.0


def test_material_accumulates():
    early = run(TermiteConfig(steps=400, k=6.0, seed=3))["M"].sum()
    late = run(TermiteConfig(steps=1200, k=6.0, seed=3))["M"].sum()
    assert late > early                        # the structure grows over time


def test_positions_in_box():
    cfg = TermiteConfig(L=100, steps=500, seed=4)
    r = run(cfg)
    assert r["pos"].min() >= 0 and r["pos"].max() < cfg.L


def test_reproducible():
    a = run(TermiteConfig(steps=400, seed=7))["M"]
    b = run(TermiteConfig(steps=400, seed=7))["M"]
    assert np.array_equal(a, b)
