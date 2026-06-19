import numpy as np

from alife.cahnhilliard import (
    CHConfig, init, run, coarsening_length, coarsening_exponent, phase_fractions,
)
from dataclasses import replace


def test_order_parameter_is_conserved():
    # the Laplacian out front conserves the spatial mean exactly (the k=0 mode is untouched)
    cfg = CHConfig(N=96, steps=400, seed=1)
    c0 = init(cfg).mean()
    c = run(cfg)["c"]
    assert abs(c.mean() - c0) < 1e-6


def test_phase_separation_to_two_phases():
    c = run(CHConfig(N=128, steps=2500, seed=1))["c"]
    # field has separated toward +/-1 (most cells near a phase, not near 0)
    assert c.min() < -0.8 and c.max() > 0.8
    assert (np.abs(c) > 0.5).mean() > 0.8
    pos, neg = phase_fractions(c)
    assert 0.3 < pos < 0.7              # symmetric quench -> roughly equal phases


def test_coarsening_length_grows():
    r = run(CHConfig(N=160, steps=3000, seed=1), record_every=300)
    assert r["L"][-1] > 1.5 * r["L"][0]


def test_coarsening_exponent_near_one_third():
    r = run(CHConfig(N=192, steps=4500, seed=1), record_every=200)
    n = coarsening_exponent(r["t"], r["L"], t_min=400)
    assert 0.25 < n < 0.42             # Lifshitz-Slyozov-Wagner t^(1/3), finite-size honest


def test_coarsening_length_metric_on_control():
    # validate the length metric: stripes of known period P -> measured L ~ P
    N, P = 128, 16
    x = np.arange(N)
    c = np.sign(np.sin(2 * np.pi * x / P))[None, :] * np.ones((N, 1))
    assert abs(coarsening_length(c) - P) < 0.25 * P


def test_higher_eps_gives_coarser_pattern():
    # larger interface width eps -> larger domains at the same time
    fine = run(CHConfig(N=128, eps=0.7, steps=1500, seed=2))["c"]
    coarse = run(CHConfig(N=128, eps=1.6, steps=1500, seed=2))["c"]
    assert coarsening_length(coarse) > coarsening_length(fine)


def test_reproducible():
    a = run(CHConfig(N=64, steps=300, seed=5))["c"]
    b = run(CHConfig(N=64, steps=300, seed=5))["c"]
    assert np.allclose(a, b)
