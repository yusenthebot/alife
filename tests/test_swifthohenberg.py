import numpy as np

from alife.swifthohenberg import (
    SHConfig, run, dominant_wavenumber, cell_count, mean_elongation, pattern_type, PRESETS,
)
from dataclasses import replace


def test_metrics_on_controls():
    N = 160
    x = np.arange(N) * 2 * np.pi / N
    X, Y = np.meshgrid(x, x)
    rolls = np.cos(8 * X)                                       # parallel stripes
    hexf = sum(np.cos(8 * (np.cos(np.radians(a)) * X + np.sin(np.radians(a)) * Y))
               for a in (0, 60, 120))                          # hexagonal lattice
    assert pattern_type(rolls) == "rolls" and mean_elongation(rolls) > 2.0
    assert pattern_type(hexf) == "hexagons" and mean_elongation(hexf) < 1.6


def test_selects_unit_wavenumber():
    # the (1+lap)^2 operator forces the pattern wavelength to k=1, whatever the noise it grew from
    for cfg in (PRESETS["rolls"], PRESETS["hexagons"]):
        u = run(replace(cfg, steps=4000, seed=1))["u"]
        assert abs(dominant_wavenumber(u) - 1.0) < 0.15


def test_rolls_regime():
    u = run(replace(PRESETS["rolls"], steps=4500, seed=1))["u"]
    assert pattern_type(u) == "rolls"
    assert mean_elongation(u) > 1.8


def test_hexagon_regime():
    u = run(replace(PRESETS["hexagons"], steps=4500, seed=1))["u"]
    assert pattern_type(u) == "hexagons"
    assert cell_count(u) > 100 and mean_elongation(u) < 1.6     # many compact honeycomb cells


def test_quadratic_term_switches_rolls_to_hexagons():
    # same drive r, only the up/down asymmetry g changes: g=0 rolls, g>0 hexagons
    rolls = run(SHConfig(N=160, r=0.12, g=0.0, steps=4500, seed=2))["u"]
    hexf = run(SHConfig(N=160, r=0.12, g=1.2, steps=4500, seed=2))["u"]
    assert mean_elongation(rolls) > mean_elongation(hexf)
    assert cell_count(hexf) > cell_count(rolls)


def test_below_threshold_is_flat():
    u = run(SHConfig(r=-0.2, g=0.0, steps=2500, seed=1))["u"]
    assert pattern_type(u) == "flat" and u.std() < 0.05


def test_reproducible():
    a = run(SHConfig(N=96, steps=300, seed=5))["u"]
    b = run(SHConfig(N=96, steps=300, seed=5))["u"]
    assert np.allclose(a, b)
