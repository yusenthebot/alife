import numpy as np
from dataclasses import replace

from alife.turingsphere import (TuringSphereConfig, run, count_spots,
                                icosphere, build_laplacian)

BASE = TuringSphereConfig(subdiv=4, F=0.0367, k=0.0649, steps=9000, seed=1)


def test_icosphere_vertex_count():
    for n in range(4):
        V, _ = icosphere(n)
        assert len(V) == 10 * 4 ** n + 2


def test_icosphere_on_unit_sphere():
    V, _ = icosphere(3)
    assert np.allclose(np.linalg.norm(V, axis=1), 1.0)


def test_laplacian_conserves_constants():
    V, F = icosphere(3)
    L, _ = build_laplacian(V, F)
    assert np.abs(L @ np.ones(len(V))).max() < 1e-10   # row-normalized: constant -> zero diffusion


def test_pattern_forms():
    r = run(BASE)
    assert r["v"].max() > 0.2 and r["v"].std() > 0.02   # a real pattern, not a flat field
    assert count_spots(r["v"], r["A"]) > 5


def test_spots_isolated_in_mitosis():
    r = run(BASE)
    assert (r["v"] > 0.2).mean() < 0.2                  # isolated spots, not a filled labyrinth


def test_more_spots_on_bigger_sphere():
    small = count_spots(run(BASE)["v"], run(BASE)["A"])
    big_r = run(replace(BASE, subdiv=5))
    big = count_spots(big_r["v"], big_r["A"])
    assert big > 1.5 * small                            # finer mesh = larger sphere in λ -> more spots


def test_field_finite_bounded():
    r = run(replace(BASE, steps=3000))
    assert np.isfinite(r["v"]).all() and r["v"].min() >= -1e-9 and r["v"].max() < 1.0


def test_reproducible():
    a = run(replace(BASE, steps=2000))["v"]
    b = run(replace(BASE, steps=2000))["v"]
    assert np.array_equal(a, b)
