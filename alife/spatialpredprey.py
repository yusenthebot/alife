"""R109 — Spatial predator-prey: how space rescues coexistence.

Well-mixed predator-prey models are notoriously fragile: the Rosenzweig-MacArthur system limit-cycles
with such large swings that the populations skim zero and, with any noise, crash to extinction (the
"paradox of enrichment"). Give the same dynamics SPACE — let prey and predators diffuse on a 2D
landscape — and coexistence is rescued. Local patches still oscillate, but neighbouring patches fall
out of phase, organising into travelling/spiral PURSUIT WAVES (predator chasing prey across the
landscape). Because the patches are desynchronised, the global population is the average of many
out-of-phase oscillators, so its swings are far smaller and it stays well away from extinction. Space
turns a boom-bust system into a persistent one — a classic argument for why real ecologies survive.

Explicit reaction-diffusion (5-point Laplacian, periodic); pure numpy/CPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PPConfig:
    n: int = 128
    Du: float = 1.0
    Dv: float = 1.0
    alpha: float = 0.4        # Holling half-saturation
    beta: float = 2.0         # predator conversion
    gamma: float = 0.6        # predator death
    dt: float = 0.05
    dx2: float = 1.0
    steps: int = 4000


def _lap(a):
    return (np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1) - 4 * a)


def _react(U, V, c):
    pred = U * V / (U + c.alpha)
    dU = U * (1 - U) - pred
    dV = c.beta * pred - c.gamma * V
    return dU, dV


def equilibrium(c=PPConfig()):
    """Interior fixed point (U*, V*)."""
    Us = c.gamma * c.alpha / (c.beta - c.gamma)
    Vs = (1 - Us) * (Us + c.alpha)
    return Us, Vs


def simulate(c=PPConfig(), seed=0, record_every=0):
    """2D spatial RD predator-prey. Returns global-mean time series + final fields + snapshots."""
    rng = np.random.default_rng(seed)
    Us, Vs = equilibrium(c)
    U = Us + 0.1 * rng.standard_normal((c.n, c.n))
    V = Vs + 0.1 * rng.standard_normal((c.n, c.n))
    U = np.clip(U, 1e-4, None); V = np.clip(V, 1e-4, None)
    mu, mv, snaps = [], [], {}
    for t in range(c.steps):
        dU, dV = _react(U, V, c)
        U = U + c.dt * (c.Du * _lap(U) / c.dx2 + dU)
        V = V + c.dt * (c.Dv * _lap(V) / c.dx2 + dV)
        U = np.clip(U, 0.0, None); V = np.clip(V, 0.0, None)
        mu.append(float(U.mean())); mv.append(float(V.mean()))
        if record_every and (t % record_every == 0 or t == c.steps - 1):
            snaps[t] = (U.copy(), V.copy())
    return {"U": U, "V": V, "mu": np.asarray(mu), "mv": np.asarray(mv), "snaps": snaps}


def well_mixed(c=PPConfig(), seed=0):
    """0D (no space) ODE limit cycle — the fragile, large-amplitude control."""
    rng = np.random.default_rng(seed)
    Us, Vs = equilibrium(c)
    U, V = Us + 0.1, Vs + 0.1
    mu, mv = [], []
    for t in range(c.steps):
        dU, dV = _react(np.array(U), np.array(V), c)
        U = max(0.0, U + c.dt * float(dU)); V = max(0.0, V + c.dt * float(dV))
        mu.append(U); mv.append(V)
    return {"mu": np.asarray(mu), "mv": np.asarray(mv)}


def fluctuation(series, tail=0.5):
    """Std of the global density over the late portion (small = stabilised)."""
    s = series[int((1 - tail) * len(series)):]
    return float(s.std())


def min_density(series, tail=0.5):
    """Lowest global density reached late (high = far from extinction)."""
    s = series[int((1 - tail) * len(series)):]
    return float(s.min())
