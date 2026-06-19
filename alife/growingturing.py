"""R117 — Turing patterns on a GROWING domain: how a stripe pattern keeps its spacing as it grows.

A static Turing system (R45/gierermeinhardt) picks ONE wavelength and freezes a fixed number of
stripes. But an embryo grows while it is being patterned — a fish adds stripes, a snake adds somites,
a leaf adds veins — and the new tissue must be patterned too. Crampin, Gaffney & Maini (1999) studied
reaction-diffusion on a slowly GROWING domain and found the resolution: the intrinsic Turing wavelength
is set by the chemistry (diffusion + reaction), so it stays fixed in absolute units while the domain
lengthens; when the existing stripes are stretched past ~1.5x the preferred spacing the gap between
them goes Turing-unstable and a NEW stripe INSERTS (or a peak splits in two). The pattern keeps its
wavelength by adding stripes — so the stripe count grows in PROPORTION to domain size:

    n_stripes(L)  ~  L / lambda*   (lambda* = the fixed intrinsic wavelength).

This is a developmental route distinct from R114 somitogenesis (there a clock+front SET the spacing;
here a self-organizing instability does) and from static Turing (there the count is frozen). Model:
Schnakenberg kinetics in 1D on a dx=1 lattice; growth = periodic uniform stretch (interpolate the
fields onto a longer grid), after which the dynamics re-select the wavelength. Pure numpy/scipy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import find_peaks


@dataclass(frozen=True)
class GrowTuringConfig:
    Du: float = 1.0
    Dv: float = 40.0
    gamma: float = 4.0          # reaction rate -> sets the intrinsic wavelength (~1/sqrt(gamma))
    a: float = 0.1
    b: float = 0.9
    dt: float = 0.004
    seed: int = 0
    noise: float = 0.01


def _lap(f):
    """1D Laplacian with zero-flux (Neumann) boundaries, dx=1."""
    out = np.empty_like(f)
    out[1:-1] = f[2:] - 2.0 * f[1:-1] + f[:-2]
    out[0] = f[1] - f[0]
    out[-1] = f[-2] - f[-1]
    return out


def _ss(cfg):
    return cfg.a + cfg.b, cfg.b / (cfg.a + cfg.b) ** 2


def step(u, v, cfg, n=1):
    for _ in range(n):
        u2v = u * u * v
        u = u + cfg.dt * (cfg.Du * _lap(u) + cfg.gamma * (cfg.a - u + u2v))
        v = v + cfg.dt * (cfg.Dv * _lap(v) + cfg.gamma * (cfg.b - u2v))
    return u, v


def make_fields(cfg, N, rng):
    us, vs = _ss(cfg)
    return (us + cfg.noise * rng.standard_normal(N), vs + cfg.noise * rng.standard_normal(N))


def count_peaks(u) -> int:
    pk, _ = find_peaks(u, height=float(u.mean()), distance=2)
    return int(pk.size)


def wavelength(u) -> float:
    n = count_peaks(u)
    return float(u.size / n) if n else float("inf")


def run_static(cfg: GrowTuringConfig, N=200, steps=60000):
    """Fixed-domain control: the pattern settles to a constant number of stripes."""
    rng = np.random.default_rng(cfg.seed)
    u, v = make_fields(cfg, N, rng)
    u, v = step(u, v, cfg, steps)
    return {"u": u, "v": v, "n": count_peaks(u), "wavelength": wavelength(u)}


def _stretch(u, v, N_new):
    x_old = np.linspace(0.0, 1.0, u.size)
    x_new = np.linspace(0.0, 1.0, N_new)
    return np.interp(x_new, x_old, u), np.interp(x_new, x_old, v)


def run_growing(cfg: GrowTuringConfig, N0=70, Nmax=420, grow_factor=1.04,
                settle=45000, grow_steps=2500, disp_width=420):
    """Equilibrate a small domain, then repeatedly STRETCH (uniform growth) + relax.

    Returns stripe count vs domain length, plus a normalized-coordinate kymograph showing insertions."""
    rng = np.random.default_rng(cfg.seed)
    u, v = make_fields(cfg, N0, rng)
    u, v = step(u, v, cfg, settle)
    lengths, counts, kymo = [], [], []

    def record():
        lengths.append(u.size)
        counts.append(count_peaks(u))
        x_old = np.linspace(0.0, 1.0, u.size)
        kymo.append(np.interp(np.linspace(0.0, 1.0, disp_width), x_old, u))

    record()
    while u.size < Nmax:
        N_new = min(int(round(u.size * grow_factor)) + 1, Nmax)
        u, v = _stretch(u, v, N_new)
        u = u + cfg.noise * 0.5 * rng.standard_normal(u.size)      # tiny noise to seed insertions
        u, v = step(u, v, cfg, grow_steps)
        record()
    return {"lengths": np.asarray(lengths), "counts": np.asarray(counts),
            "kymo": np.asarray(kymo), "u": u, "v": v}
