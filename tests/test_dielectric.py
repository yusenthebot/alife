import numpy as np

from alife.dielectric import (
    DBMConfig, solve_field, grow, fractal_dimension, dimension_curve, _perimeter,
)
from dataclasses import replace

CFG = DBMConfig(M=81, target=280, batch=4, seed=1)


def test_field_is_harmonic_and_bounded():
    cl = np.zeros((61, 61), bool)
    cl[30, 30] = True
    phi = solve_field(cl)
    assert phi.min() >= -1e-9 and phi.max() <= 1.0 + 1e-9
    assert phi[30, 30] == 0.0                               # zero on the cluster
    assert phi[0, 0] == 1.0                                 # one on the outer ring


def test_seed_grows():
    r = grow(CFG)
    assert r["mass"] >= 100                                 # grew substantially from the seed


def test_eta_orders_the_fractal_dimension():
    # THE headline: more ruthless tip-reward (higher eta) -> lower fractal dimension
    d0 = fractal_dimension(grow(replace(CFG, eta=0.0))["cluster"])
    d1 = fractal_dimension(grow(replace(CFG, eta=1.0))["cluster"])
    d4 = fractal_dimension(grow(replace(CFG, eta=4.0))["cluster"])
    assert d0 > d1 > d4


def test_eta0_is_compact():
    assert fractal_dimension(grow(replace(CFG, eta=0.0))["cluster"]) > 1.6


def test_high_eta_is_needle_like():
    assert fractal_dimension(grow(replace(CFG, eta=5.0))["cluster"]) < 1.45


def test_growth_favours_tips_over_fjords():
    # screening: on the perimeter, high-field cells sit farther out (tips) than low-field ones (fjords)
    r = grow(replace(CFG, eta=1.0, target=350))
    cl = r["cluster"]
    phi = solve_field(cl)
    per = _perimeter(cl)
    ci, cj = np.where(per)
    f = phi[ci, cj]
    c = cl.shape[0] // 2
    rad = np.hypot(ci - c, cj - c)
    hi = f > np.median(f)
    assert rad[hi].mean() > rad[~hi].mean()


def test_dimension_curve_decreasing():
    _, d = dimension_curve([0.0, 1.5, 4.0], replace(CFG, target=260))
    assert d[0] > d[1] > d[2]


def test_reproducible():
    a = grow(replace(CFG, target=160))["cluster"]
    b = grow(replace(CFG, target=160))["cluster"]
    assert np.array_equal(a, b)
