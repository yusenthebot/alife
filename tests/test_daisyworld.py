import numpy as np

from alife.daisyworld import DaisyConfig, bare_temp, equilibrium, luminosity_sweep


def test_homeostasis_regulates_temperature():
    """Across the daisy-viable luminosity range, the living planet's temperature
    varies far less than a bare planet's."""
    cfg = DaisyConfig()
    Ls = np.arange(0.7, 1.25, 0.05)
    ta, td, b, w = luminosity_sweep(cfg, Ls)
    assert ta.std() < 0.4 * td.std()
    assert ta.std() < 4.0                       # held within a few degrees


def test_black_dominates_cold_white_dominates_hot():
    cfg = DaisyConfig()
    _, _, b_cold, w_cold = luminosity_sweep(cfg, [0.75])
    _, _, b_hot, w_hot = luminosity_sweep(cfg, [1.2])
    assert b_cold[0] > w_cold[0]               # cold: black daisies lead
    assert w_hot[0] > b_hot[0]                 # hot: white daisies lead


def test_regulation_breaks_at_extremes():
    """Too hot for daisies -> they die and temperature snaps to the bare-planet value."""
    cfg = DaisyConfig()
    Te, ab, aw = equilibrium(cfg, 1.7)
    assert ab + aw < 0.05
    assert abs(Te - bare_temp(cfg, 1.7)) < 1.0


def test_bare_planet_monotonic():
    cfg = DaisyConfig()
    temps = [bare_temp(cfg, L) for L in np.arange(0.6, 1.7, 0.1)]
    assert all(b > a for a, b in zip(temps, temps[1:]))   # rises with luminosity


def test_living_planet_cooler_when_hot():
    """In the regulated range the daisies keep it cooler than a bare planet would be."""
    cfg = DaisyConfig()
    Te, _, _ = equilibrium(cfg, 1.2)
    assert Te < bare_temp(cfg, 1.2)


def test_reproducible():
    cfg = DaisyConfig()
    a = equilibrium(cfg, 1.0)
    b = equilibrium(cfg, 1.0)
    assert a == b
