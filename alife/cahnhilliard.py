"""R125 — Cahn-Hilliard spinodal decomposition: watch a mixture unmix and coarsen.

Quench a hot, uniformly-mixed binary alloy (or oil-and-water, or a polymer blend) and it does not just
freeze — it spontaneously SEPARATES into interpenetrating domains of the two phases, which then slowly
COARSEN: small domains dissolve to feed big ones, the pattern getting blockier over time. This is the
canonical "Model B" of statistical physics — a conserved order parameter c (the local composition,
+1 / -1 for the two phases) evolving down a double-well free energy:

    dc/dt = M * lap( mu ),   mu = -eps^2 lap(c) + (c^3 - c)

The Laplacian out front makes c CONSERVED (you can't create or destroy material, only move it) — unlike
the reaction-diffusion Turing patterns (gierermeinhardt/reactiondiff) whose order parameter is not
conserved. From tiny noise the field splits into +1 / -1 domains, and the characteristic domain size
grows as the famous Lifshitz-Slyozov-Wagner power law L(t) ~ t^(1/3). You SEE the domains merge in the
animation, and the log-log L(t) line confirms the 1/3 exponent.

Integrated by a semi-implicit Fourier spectral scheme (the stiff 4th-order linear term implicit, the
cubic nonlinearity explicit), which is unconditionally stable and conserves the mean exactly. numpy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CHConfig:
    N: int = 192
    eps: float = 1.0          # interface width (sqrt of gradient-energy coefficient)
    M: float = 1.0            # mobility
    dt: float = 0.6
    steps: int = 4500
    seed: int = 0
    c0: float = 0.0           # mean composition (0 = symmetric quench)
    noise: float = 0.05
    stab: float = 1.5         # convex-splitting stabilizer (>=~1 -> unconditionally stable)


def _k2(N):
    k = 2.0 * np.pi * np.fft.fftfreq(N)
    kx, ky = np.meshgrid(k, k)
    return kx ** 2 + ky ** 2


def init(cfg: CHConfig):
    rng = np.random.default_rng(cfg.seed)
    return cfg.c0 + cfg.noise * rng.standard_normal((cfg.N, cfg.N))


def run(cfg: CHConfig, record_every: int = 0):
    """Semi-implicit spectral Cahn-Hilliard. Returns final field, snapshots, and L(t)."""
    c = init(cfg)
    k2 = _k2(cfg.N)
    A = cfg.stab
    # convex-splitting semi-implicit: stiff 4th-order term + a stabilizer A*k^2 implicit,
    # the spinodal (+k^2 c) driver and cubic nonlinearity explicit -> unconditionally stable
    denom = 1.0 + cfg.dt * cfg.M * (cfg.eps ** 2 * k2 ** 2 + A * k2)
    times, lengths, snaps = [], [], []
    for t in range(cfg.steps):
        chat = np.fft.fft2(c)
        num = chat + cfg.dt * cfg.M * k2 * ((A + 1.0) * chat - np.fft.fft2(c ** 3))
        c = np.real(np.fft.ifft2(num / denom))
        if record_every and (t % record_every == 0 or t == cfg.steps - 1):
            times.append(t + 1); lengths.append(coarsening_length(c)); snaps.append(c.copy())
    return {"c": c, "t": np.asarray(times), "L": np.asarray(lengths), "snaps": snaps}


def coarsening_length(c) -> float:
    """Domain size from the azimuthally-averaged structure factor: L = 2*pi * <S> / <k S> (k>0)."""
    N = c.shape[0]
    kr = np.sqrt(_k2(N))
    S = (np.abs(np.fft.fft2(c - c.mean())) ** 2).ravel()
    bins = np.linspace(0, kr.max(), N // 2)
    kc = 0.5 * (bins[1:] + bins[:-1])
    idx = np.digitize(kr.ravel(), bins)
    Sr = np.array([S[idx == b].mean() if np.any(idx == b) else 0.0 for b in range(1, len(bins))])
    m = (kc > 0) & (Sr > 0)
    if not m.any():
        return 0.0
    return float(2.0 * np.pi * Sr[m].sum() / (kc[m] * Sr[m]).sum())


def coarsening_exponent(t, L, t_min=300):
    """Power-law exponent n in L ~ t^n (fit after the early transient); LSW predicts 1/3."""
    t, L = np.asarray(t, float), np.asarray(L, float)
    m = t >= t_min
    return float(np.polyfit(np.log(t[m]), np.log(L[m]), 1)[0])


def phase_fractions(c):
    """Fraction of the field in each phase (c>0 vs c<0)."""
    pos = float((c > 0).mean())
    return pos, 1.0 - pos
