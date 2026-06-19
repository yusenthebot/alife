import numpy as np

from alife.chladni import (
    ChladniConfig, eigenfrequency, mode_field, assemble_sand, node_amplitude,
    nodal_line_count, is_symmetric_combo, _phi_at,
)
from dataclasses import replace


def test_eigenfrequency_and_degeneracy():
    assert abs(eigenfrequency(3, 2) - np.sqrt(13)) < 1e-9
    assert eigenfrequency(3, 2) == eigenfrequency(2, 3)        # (m,n) and (n,m) are degenerate


def test_mode_vanishes_on_boundary():
    phi = mode_field(ChladniConfig(m=3, n=2, N=120))
    assert np.abs(phi[0, :]).max() < 1e-9 and np.abs(phi[-1, :]).max() < 1e-9
    assert np.abs(phi[:, 0]).max() < 1e-9 and np.abs(phi[:, -1]).max() < 1e-9


def test_degenerate_combination_symmetry():
    assert is_symmetric_combo(ChladniConfig(m=4, n=2, c=1.0))      # + -> symmetric under x<->y
    assert is_symmetric_combo(ChladniConfig(m=4, n=2, c=-1.0))     # - -> antisymmetric


def test_sand_settles_on_nodes():
    # the headline: grains end up where |phi| is small (on the nodal lines), far below random
    cfg = ChladniConfig(m=3, n=2, c=-1.0, ngrain=4000, steps=500, seed=1)
    r = assemble_sand(cfg)
    rng = np.random.default_rng(0)
    rand = rng.uniform(0.02, 0.98, (4000, 2))
    assert node_amplitude(r["phi"], r["pos"]) < 0.3 * np.abs(_phi_at(r["phi"], rand)).mean()


def test_sand_stays_on_plate():
    r = assemble_sand(ChladniConfig(ngrain=2000, steps=300, seed=2))
    assert r["pos"].min() >= 0.0 and r["pos"].max() <= 1.0


def test_sand_concentrates():
    # final grain distribution is more clustered than uniform (higher cell-occupancy variance)
    r = assemble_sand(ChladniConfig(m=3, n=2, ngrain=4000, steps=500, seed=3))
    h, _, _ = np.histogram2d(r["pos"][:, 0], r["pos"][:, 1], bins=30)
    rng = np.random.default_rng(0)
    hr, _, _ = np.histogram2d(*rng.uniform(0, 1, (2, 4000)), bins=30)
    assert h.var() > 2.0 * hr.var()


def test_higher_mode_has_more_nodal_lines():
    assert nodal_line_count(ChladniConfig(m=5, n=4)) > nodal_line_count(ChladniConfig(m=2, n=1))


def test_reproducible():
    a = assemble_sand(ChladniConfig(ngrain=500, steps=100, seed=7))["pos"]
    b = assemble_sand(ChladniConfig(ngrain=500, steps=100, seed=7))["pos"]
    assert np.array_equal(a, b)
