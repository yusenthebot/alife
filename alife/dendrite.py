"""R139 — Dendritic solidification: a snowflake crystal grows from an undercooled melt (phase field).

Freeze a pure liquid below its melting point and a crystal does not grow as a smooth ball — it throws
out sharp branching arms, a dendrite (the shape inside every snowflake and most cast metals). Two
ingredients make it: (1) the Mullins-Sekerka instability — a protruding tip sheds the latent heat it
releases faster, stays colder, and so grows faster, runaway tip-sharpening; (2) ANISOTROPIC surface
tension — the crystal lattice makes some directions cheaper, so the runaway picks a fixed number of
preferred directions, giving j sharp primary arms (j=6 for ice, j=4 for cubic metals). Side branches
then sprout on the arms from the same instability.

Model: the Kobayashi (1993) phase field. A phase p (1=solid, 0=liquid) couples to a temperature T;
the gradient-energy coefficient ε(θ)=ε̄(1+δ cos(j(θ-θ0))) depends on the interface normal angle θ
(this is the anisotropy), and latent heat K·∂p/∂t reheats the melt. Explicit finite differences, numpy.
Distinct from snowflake.py (Reiter hexagonal CA — a discrete vapour rule) and dla.py (random-walk
aggregation): this is a continuum PDE with real latent-heat coupling and tunable lattice anisotropy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class DendriteConfig:
    N: int = 360
    dx: float = 0.03
    dt: float = 0.0002
    eps_bar: float = 0.01     # mean gradient-energy coefficient
    delta: float = 0.04       # anisotropy strength (0 -> isotropic, no arms)
    j: int = 6                # anisotropy mode = number of primary arms
    theta0: float = 0.2       # arm orientation offset
    tau: float = 0.0003
    alpha: float = 0.9
    gamma: float = 10.0
    Teq: float = 1.0          # equilibrium (melting) temperature; melt starts undercooled at T=0
    kappa: float = 1.8        # latent heat
    noise: float = 0.0        # interface noise amplitude (seeds side-branching)
    steps: int = 4500
    seed_r: float = 3.0
    seed: int = 0


def _ddx(f, dx):
    return (np.roll(f, -1, 1) - np.roll(f, 1, 1)) / (2 * dx)


def _ddy(f, dx):
    return (np.roll(f, -1, 0) - np.roll(f, 1, 0)) / (2 * dx)


def _lap(f, dx):
    return (np.roll(f, 1, 0) + np.roll(f, -1, 0) + np.roll(f, 1, 1) + np.roll(f, -1, 1) - 4 * f) / dx ** 2


def run(cfg: DendriteConfig, record_every: int = 0):
    """Grow a dendrite from a central seed in an undercooled melt. Returns p, T, snapshots."""
    rng = np.random.default_rng(cfg.seed)
    N, dx = cfg.N, cfg.dx
    p = np.zeros((N, N))
    T = np.zeros((N, N))
    yy, xx = np.indices((N, N))
    c = N // 2
    p[((xx - c) ** 2 + (yy - c) ** 2) < cfg.seed_r ** 2] = 1.0
    snaps = {}
    for s in range(cfg.steps):
        pdx = _ddx(p, dx); pdy = _ddy(p, dx)
        theta = np.arctan2(pdy, pdx)
        eps = cfg.eps_bar * (1 + cfg.delta * np.cos(cfg.j * (theta - cfg.theta0)))
        deps = -cfg.eps_bar * cfg.delta * cfg.j * np.sin(cfg.j * (theta - cfg.theta0))
        term1 = _ddy(eps * deps * pdx, dx)
        term2 = _ddx(eps * deps * pdy, dx)
        m = (cfg.alpha / np.pi) * np.arctan(cfg.gamma * (cfg.Teq - T))
        if cfg.noise:
            m = m + cfg.noise * (rng.random((N, N)) - 0.5)
        dpdt = (term1 - term2 + eps ** 2 * _lap(p, dx) + p * (1 - p) * (p - 0.5 + m)) / cfg.tau
        p = p + cfg.dt * dpdt
        T = T + cfg.dt * (_lap(T, dx) + cfg.kappa * dpdt)
        np.clip(p, 0.0, 1.0, out=p)
        if record_every and s % record_every == 0:
            snaps[s] = p.copy()
    return {"p": p, "T": T, "snaps": snaps}


def _radial_profile(p, nbins=180):
    """Tip radius as a function of angle around the crystal centroid."""
    ys, xs = np.where(p > 0.5)
    c = p.shape[0] / 2
    ang = np.arctan2(ys - c, xs - c)
    rad = np.hypot(xs - c, ys - c)
    bins = ((ang + np.pi) / (2 * np.pi) * nbins).astype(int) % nbins
    prof = np.zeros(nbins)
    for b, r in zip(bins, rad):
        prof[b] = max(prof[b], r)
    return prof


def arm_count(p) -> int:
    """Number of primary arms = dominant angular Fourier mode of the tip-radius profile."""
    prof = _radial_profile(p)
    prof = prof - prof.mean()
    F = np.abs(np.fft.rfft(prof))
    return int(np.argmax(F[1:13]) + 1)


def solid_fraction(p) -> float:
    return float((p > 0.5).mean())
