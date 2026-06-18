import numpy as np
from dataclasses import replace

from alife.cellsort import CPMConfig, init_tissue, heterotypic_boundary, run, type_image


def test_init_tissue():
    cfg = CPMConfig(size=60, cell=5)
    spin, types, area, A0 = init_tissue(cfg, seed=0)
    assert A0 == 25
    assert set(np.unique(types)).issubset({0, 1, 2})  # medium + two cell types
    ncells = (types > 0).sum()
    assert ncells > 20                                # a tissue of many cells
    assert 0.6 * A0 < area[1:].mean() < 1.4 * A0      # initial cells near target area


def test_heterotypic_boundary_positive_when_mixed():
    cfg = CPMConfig(size=50, cell=5)
    spin, types, area, A0 = init_tissue(cfg, seed=1)
    assert heterotypic_boundary(spin, types) > 0


def test_area_constraint_keeps_cells_alive():
    cfg = CPMConfig(size=60, cell=5, temp=10.0)
    r = run(cfg, sweeps=120, seed=0)
    a = r["area"][1:]
    assert a.min() > 0.3 * 25 and a.max() < 3 * 25    # no cell vanished or ballooned


def test_differential_adhesion_sorts():
    cfg = CPMConfig(size=70, cell=5, temp=10.0)
    r = run(cfg, sweeps=400, seed=0)
    assert r["hetero"][-1] < 0.8 * r["hetero"][0]     # unlike-cell contacts fall: sorting


def test_equal_adhesion_does_not_sort():
    cfg = replace(CPMConfig(size=70, cell=5, temp=10.0), J=((0, 16, 16), (16, 8, 8), (16, 8, 8)))
    r = run(cfg, sweeps=400, seed=0)
    assert r["hetero"][-1] > 0.9 * r["hetero"][0]     # control: no sorting without type preference


def test_type_image_and_reproducible():
    cfg = CPMConfig(size=50, cell=5)
    a = run(cfg, sweeps=40, seed=3)
    b = run(cfg, sweeps=40, seed=3)
    assert np.array_equal(a["spin"], b["spin"])
    img = type_image(a["spin"], a["types"])
    assert img.shape == (50, 50) and set(np.unique(img)).issubset({0, 1, 2})
