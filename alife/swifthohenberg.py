"""R127 — Swift-Hohenberg / Rayleigh-Benard convection: rolls and honeycomb hexagons.

Heat a thin fluid layer from below and, past a threshold, it stops conducting and starts CONVECTING in
an ordered pattern of cells — parallel rolls, or a honeycomb of hexagons. Swift & Hohenberg (1977)
distilled this (and every other pattern that forms at a sharp wavelength) into the simplest equation
that has a BUILT-IN wavelength:

    du/dt = r u - (1 + lap)^2 u + g u^2 - u^3

The operator (1+lap)^2 is minimised at wavenumber k=1, so any growing pattern picks that wavelength
automatically (no diffusion-ratio tuning, unlike Turing). The control r is the drive (heating): below
r=0 the flat state is stable; above it, a pattern grows. The quadratic term g is the up/down asymmetry
of convection (warm rising plumes differ from cool sinking ones): with g=0 the medium has no preferred
sign and forms ROLLS (stripes); with g>0 near onset it breaks into HEXAGONS — the classic Benard cells.

You SEE the difference instantly (parallel rolls vs a honeycomb), and the Fourier ring confirms it:
rolls have ONE orientation (2 spots), hexagons THREE (6 spots at 60deg). Integrated by a Fourier
integrating-factor split (the stiff 4th-order linear part exact, the nonlinearity explicit). numpy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage


@dataclass(frozen=True)
class SHConfig:
    N: int = 160
    r: float = 0.3            # drive (heating); pattern grows for r > 0
    g: float = 0.0            # up/down asymmetry: 0 -> rolls, >0 (small r) -> hexagons
    dt: float = 0.1
    steps: int = 4000
    seed: int = 0


def _expL(cfg: SHConfig):
    k = 2.0 * np.pi * np.fft.fftfreq(cfg.N)
    kx, ky = np.meshgrid(k, k)
    k2 = kx ** 2 + ky ** 2
    return np.exp((cfg.r - (1.0 - k2) ** 2) * cfg.dt)


def run(cfg: SHConfig, record_every: int = 0):
    rng = np.random.default_rng(cfg.seed)
    u = 0.1 * rng.standard_normal((cfg.N, cfg.N))
    expL = _expL(cfg)
    snaps = []
    for t in range(cfg.steps):
        u = u + cfg.dt * (cfg.g * u ** 2 - u ** 3)                # nonlinear (explicit)
        u = np.real(np.fft.ifft2(np.fft.fft2(u) * expL))          # linear (integrating factor, exact)
        if record_every and (t % record_every == 0 or t == cfg.steps - 1):
            snaps.append(u.copy())
    return {"u": u, "snaps": snaps}


def dominant_wavenumber(u) -> float:
    """First moment of |k| weighted by the power spectrum; Swift-Hohenberg selects ~1."""
    N = u.shape[0]
    k = 2.0 * np.pi * np.fft.fftfreq(N)
    kx, ky = np.meshgrid(k, k)
    kr = np.sqrt(kx ** 2 + ky ** 2)
    S = np.abs(np.fft.fft2(u - u.mean())) ** 2
    return float((kr * S).sum() / S.sum())


def _cells(u, level=None):
    """Connected convection cells (field above a level)."""
    if level is None:
        level = u.mean() + 0.5 * u.std()
    return ndimage.label(u > level)


def cell_count(u) -> int:
    return int(_cells(u)[1])


def mean_elongation(u) -> float:
    """Mean cell elongation (bounding-box long/short): ~1 for round hexagonal cells, >2 for rolls."""
    lbl, n = _cells(u)
    if n == 0:
        return 0.0
    el = []
    for s in ndimage.find_objects(lbl):
        h, w = s[0].stop - s[0].start, s[1].stop - s[1].start
        el.append(max(h, w) / max(1, min(h, w)))
    return float(np.mean(el))


def pattern_type(u) -> str:
    """'flat' (no convection), 'rolls' (elongated stripes), or 'hexagons' (round honeycomb cells)."""
    if u.std() < 0.05:
        return "flat"
    return "rolls" if mean_elongation(u) > 1.8 else "hexagons"


PRESETS = {
    "rolls": SHConfig(r=0.4, g=0.0),
    "hexagons": SHConfig(r=0.1, g=1.2),
}
