"""R48 — Daisyworld: life regulates its planet (Watson & Lovelock 1983).

A cloudless grey planet seeded with two kinds of daisy: black ones (dark, they
absorb sunlight and warm their patch) and white ones (bright, they reflect it and
cool their patch). Daisies grow best near 22.5 degC and die off in the cold or
heat. As the star slowly brightens, something remarkable happens with no foresight
or coordination: when the planet is cold, black daisies spread and warm it; when
it is hot, white daisies spread and cool it — and the global temperature stays
almost flat across a wide range of solar input. A bare planet's temperature, by
contrast, rises in lockstep with the sun. Life regulating its own environment:
the cleanest model of planetary homeostasis (Gaia).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

SIGMA = 5.67e-8


@dataclass(frozen=True)
class DaisyConfig:
    flux: float = 917.0        # solar constant S (W/m^2)
    albedo_ground: float = 0.5
    albedo_black: float = 0.25
    albedo_white: float = 0.75
    death: float = 0.30        # daisy death rate
    q: float = 20.0            # local heat redistribution (degC per unit albedo diff)
    seed: float = 0.01         # minimum daisy fraction kept alive (can re-seed)
    iters: int = 200           # iterations to equilibrium per luminosity


def _beta(temp_c: np.ndarray) -> np.ndarray:
    """Growth vs local temperature: parabola peaked at 22.5 degC, zero outside 5-40."""
    return np.maximum(0.0, 1.0 - 0.003265 * (22.5 - temp_c) ** 2)


def equilibrium(cfg: DaisyConfig, L: float):
    """Iterate daisy fractions to steady state at luminosity L.
    Returns (planet_temp_c, black_frac, white_frac)."""
    ab = aw = 0.2
    Te = 0.0
    for _ in range(cfg.iters):
        ab = max(ab, cfg.seed); aw = max(aw, cfg.seed)
        ag = max(0.0, 1.0 - ab - aw)
        A = ab * cfg.albedo_black + aw * cfg.albedo_white + ag * cfg.albedo_ground
        Te = (cfg.flux * L * (1 - A) / SIGMA) ** 0.25 - 273.15
        Tb = cfg.q * (A - cfg.albedo_black) + Te      # dark patch is warmer
        Tw = cfg.q * (A - cfg.albedo_white) + Te      # bright patch is cooler
        ab = ab + ab * (ag * _beta(np.array(Tb)) - cfg.death)
        aw = aw + aw * (ag * _beta(np.array(Tw)) - cfg.death)
        ab = float(np.clip(ab, 0.0, 1.0)); aw = float(np.clip(aw, 0.0, 1.0))
    return Te, ab, aw


def bare_temp(cfg: DaisyConfig, L: float) -> float:
    """Temperature of a lifeless grey planet (constant ground albedo)."""
    return (cfg.flux * L * (1 - cfg.albedo_ground) / SIGMA) ** 0.25 - 273.15


def luminosity_sweep(cfg: DaisyConfig, Ls):
    """Return arrays (temp_alive, temp_dead, black, white) over luminosities Ls."""
    ta, td, b, w = [], [], [], []
    for L in Ls:
        Te, ab, aw = equilibrium(cfg, float(L))
        ta.append(Te); td.append(bare_temp(cfg, float(L))); b.append(ab); w.append(aw)
    return np.array(ta), np.array(td), np.array(b), np.array(w)
