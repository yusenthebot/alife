"""R112 — Keller-Segel chemotactic aggregation: how scattered cells decide to become one body.

When food runs out, a lawn of identical Dictyostelium amoebae — until then crawling around as
independent single cells — streams together into a single multicellular slug that migrates and builds
a fruiting body. Keller & Segel (1970) explained the trigger with a startlingly small model: each cell
secretes a diffusing chemoattractant (cAMP) and crawls UP its gradient. That is a positive feedback —
a patch that happens to be slightly denser secretes more attractant, which draws in neighbours, which
secrete yet more. Diffusion of the attractant and random cell motility fight back, smearing patches
out. Keller & Segel found the balance is a sharp threshold: below a critical chemotactic sensitivity
chi_c the uniform state is LINEARLY STABLE (perturbations decay, cells stay scattered); above it ANY
perturbation grows and the population collapses into aggregates ("chemotactic collapse").

It is a pattern-forming instability like Turing's (R45 Gray-Scott), but driven not by reaction
kinetics — by nonlinear ADVECTION, the chi*rho*grad(c) drift. And its onset is analytically
predictable: linearising about the uniform state (rho0, c0=a*rho0/b) gives, for a perturbation of
wavenumber k, instability when  chi*rho0*a > Drho*(Dc*k^2 + b). The longest box-spanning mode
k_min=2*pi/L destabilises first, so

    chi_c = Drho * (Dc*k_min^2 + b) / (a * rho0).

This module integrates the Keller-Segel system with a CONSERVATIVE finite-volume scheme (cell mass is
conserved to machine precision) and an UPWIND chemotactic flux (keeps density non-negative), verifies
the predicted threshold against the measured onset, and shows the collapse. Pure numpy/CPU.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np


@dataclass(frozen=True)
class KSConfig:
    L: int = 128
    Drho: float = 1.0      # cell motility (random diffusion of cells)
    Dc: float = 1.0        # chemoattractant diffusion
    chi: float = 4.0       # chemotactic sensitivity — THE control parameter
    prod: float = 1.0      # a: attractant produced per unit cell density
    decay: float = 1.0     # b: attractant decay rate
    rho0: float = 1.0      # mean cell density (conserved)
    dt: float = 0.02
    steps: int = 3000
    seed: int = 0
    noise: float = 0.02    # amplitude of the initial uniform-state perturbation


def chi_critical(cfg: KSConfig) -> float:
    """Linear-stability prediction for the onset sensitivity (longest box mode k_min = 2*pi/L)."""
    kmin2 = (2.0 * np.pi / cfg.L) ** 2
    return cfg.Drho * (cfg.Dc * kmin2 + cfg.decay) / (cfg.prod * cfg.rho0)


def make_state(cfg: KSConfig):
    """Uniform cell lawn rho0 + tiny noise, attractant at its homogeneous equilibrium c0=a*rho0/b."""
    rng = np.random.default_rng(cfg.seed)
    rho = cfg.rho0 + cfg.noise * cfg.rho0 * rng.standard_normal((cfg.L, cfg.L))
    rho = np.maximum(rho, 0.0)
    c = np.full((cfg.L, cfg.L), cfg.prod * cfg.rho0 / cfg.decay, dtype=float)
    return rho, c


def _lap(f):
    return np.roll(f, 1, 0) + np.roll(f, -1, 0) + np.roll(f, 1, 1) + np.roll(f, -1, 1) - 4.0 * f


def _drho_dt(rho, c, cfg: KSConfig):
    """d(rho)/dt = -div(J),  J = -Drho*grad(rho) + chi*rho*grad(c).

    Flux form on cell faces (periodic) so the total mass sum telescopes to exactly 0. The chemotactic
    (advective) part uses UPWIND donor-cell density, which keeps rho >= 0 under the CFL limit."""
    rho_xp = np.roll(rho, -1, 0)                    # rho at i+1 (x faces)
    rho_yp = np.roll(rho, -1, 1)                    # rho at j+1 (y faces)
    vx = cfg.chi * (np.roll(c, -1, 0) - c)          # chemotactic velocity at +x face
    vy = cfg.chi * (np.roll(c, -1, 1) - c)          # chemotactic velocity at +y face
    # diffusive flux (central) + chemotactic flux (upwind: donor cell is upstream of v)
    Jx = -cfg.Drho * (rho_xp - rho) + vx * np.where(vx > 0, rho, rho_xp)
    Jy = -cfg.Drho * (rho_yp - rho) + vy * np.where(vy > 0, rho, rho_yp)
    divJ = (Jx - np.roll(Jx, 1, 0)) + (Jy - np.roll(Jy, 1, 1))
    return -divJ


def step(state, cfg: KSConfig):
    rho, c = state
    rho_new = rho + cfg.dt * _drho_dt(rho, c, cfg)
    c_new = c + cfg.dt * (cfg.Dc * _lap(c) + cfg.prod * rho - cfg.decay * c)
    return rho_new, c_new


def run(cfg: KSConfig, record_every: int = 0):
    """Integrate the Keller-Segel system. Returns final fields, mass/peak time-series, snapshots."""
    rho, c = make_state(cfg)
    m0 = float(rho.sum())
    mass, peak, snaps = [], [], {}
    for t in range(cfg.steps):
        rho, c = step((rho, c), cfg)
        mass.append(float(rho.sum()))
        peak.append(float(rho.max()))
        if record_every and (t % record_every == 0 or t == cfg.steps - 1):
            snaps[t] = (rho.copy(), c.copy())
    return {
        "rho": rho, "c": c,
        "mass": np.asarray(mass), "peak": np.asarray(peak),
        "mass0": m0, "snaps": snaps,
    }


def aggregation(rho, rho0: float) -> float:
    """Peak-to-mean density ratio: ~1 for a uniform lawn, large once cells collapse into aggregates."""
    return float(rho.max() / rho0)


def growth_rate(cfg: KSConfig, t0: int = 150, t1: int = 1500, mode=(1, 0)) -> float:
    """Measured early-time growth rate of a SINGLE Fourier mode of the cell field (per unit time).

    Tracking one mode (the longest, k_min, by default) isolates it from the many decaying stable
    modes that contaminate a bulk std() measurement near threshold. Linear-stability theory predicts
    this is NEGATIVE below chi_c (the mode decays), POSITIVE above it (it grows), and crosses zero AT
    chi_c — independent of run length, unlike the finite-time end-state which suffers critical
    slowing-down near threshold."""
    rho, c = make_state(replace(cfg, steps=t1))
    amp = np.empty(t1)
    for t in range(t1):
        rho, c = step((rho, c), cfg)
        amp[t] = abs(np.fft.fft2(rho)[mode])
    slope = np.polyfit(np.arange(t0, t1), np.log(amp[t0:t1]), 1)[0]
    return float(slope / cfg.dt)


def _sigma_of_mu(cfg: KSConfig, chi: float, mu):
    """Larger root of the dispersion quadratic for modes with discrete -Laplacian eigenvalue mu."""
    mu = np.atleast_1d(np.asarray(mu, float))
    B = (cfg.Drho + cfg.Dc) * mu + cfg.decay
    C = cfg.Drho * mu * (cfg.Dc * mu + cfg.decay) - chi * cfg.rho0 * cfg.prod * mu
    return (-B + np.sqrt(np.maximum(B * B - 4.0 * C, 0.0))) / 2.0


def growth_rate_theory(cfg: KSConfig, chi: float, mode=None) -> float:
    """Linear growth rate from the dispersion relation. With `mode` (n_x, n_y), the rate of that one
    mode; otherwise the largest rate over all lattice modes. Both reductions are zero at chi_c.

    Linearising the scheme about (rho0, c0) gives, for a mode with discrete -Laplacian eigenvalue mu,
    sigma^2 + sigma*((Drho+Dc)*mu + b) + (Drho*mu*(Dc*mu+b) - chi*rho0*a*mu) = 0."""
    if mode is not None:
        mu = sum(2.0 * (1.0 - np.cos(2.0 * np.pi * n / cfg.L)) for n in mode)
        return float(_sigma_of_mu(cfg, chi, mu)[0])
    mu1 = 2.0 * (1.0 - np.cos(2.0 * np.pi * np.arange(cfg.L) / cfg.L))
    mu = (mu1[:, None] + mu1[None, :]).ravel()
    mu = mu[mu > 1e-12]                                     # drop the conserved uniform mode
    return float(_sigma_of_mu(cfg, chi, mu).max())


def sweep_chi(chis, cfg: KSConfig):
    """Final aggregation metric vs chemotactic sensitivity — flat ~1 below chi_c, rising above it."""
    out = [aggregation(run(replace(cfg, chi=float(chi)))["rho"], cfg.rho0) for chi in chis]
    return np.asarray(chis, float), np.asarray(out)


def onset_chi(chis, metric, thresh: float = 2.0):
    """First sensitivity in the sweep at which the aggregation metric crosses `thresh`."""
    chis = np.asarray(chis, float)
    above = np.asarray(metric) > thresh
    return float(chis[np.argmax(above)]) if above.any() else float("inf")
