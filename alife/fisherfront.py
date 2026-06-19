"""R137 — Invasion fronts: how fast life spreads, and when it can't get started.

Drop a population into empty habitat and it spreads as a travelling wave — a sharp front advancing at a
constant speed, leaving the carrying-capacity behind it. Fisher (1937) and Kolmogorov-Petrovsky-Piskunov
showed the logistic reaction-diffusion u_t = D u_xx + r u(1-u) selects a unique front speed c = 2*sqrt(rD)
— and remarkably this is a PULLED front: the speed is set entirely by the dilute leading edge (linearise
about u=0), not by the bulk. Faster growth or faster diffusion → faster invasion, as the square root.

Add an Allee effect — growth that turns NEGATIVE when the population is too sparse, r u(1-u)(u-a) with a
threshold a — and the front becomes PUSHED (speed set by the bulk, c = sqrt(rD/2)(1-2a)). Now there is a
critical threshold: for a < 1/2 the population still invades, at a = 1/2 the front stalls, and for a > 1/2
the front RETREATS — a large founder population is driven extinct because sparse edges can't grow. The
same diffusion that spreads life can fail to, depending on one number.

Model: explicit finite-difference reaction-diffusion, 1D for clean front-speed measurement and 2D for the
radially expanding (or collapsing) colony. numpy only.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FrontConfig:
    D: float = 1.0
    r: float = 1.0
    allee: float | None = None   # None -> Fisher logistic; float a -> Allee r u(1-u)(u-a)
    dx: float = 0.5
    dt: float = 0.04
    seed: int = 0


def fisher_speed_theory(cfg: FrontConfig) -> float:
    return 2.0 * np.sqrt(cfg.r * cfg.D)


def allee_speed_theory(cfg: FrontConfig) -> float:
    return np.sqrt(cfg.r * cfg.D / 2.0) * (1.0 - 2.0 * cfg.allee)


def _react(u, cfg: FrontConfig):
    if cfg.allee is None:
        return cfg.r * u * (1.0 - u)
    return cfg.r * u * (1.0 - u) * (u - cfg.allee)


def _front_pos(u, dx) -> float:
    """Position of the u = 0.5 level set (linear interpolation)."""
    below = u < 0.5
    if not below.any() or below.all():
        return 0.0
    i = int(np.argmax(below))
    if i == 0:
        return 0.0
    return dx * (i - 1 + (u[i - 1] - 0.5) / (u[i - 1] - u[i] + 1e-12))


def run1d(cfg: FrontConfig, N: int = 1500, steps: int = 3000, seed_width: int = 80):
    """1D front. Returns final profile, front position vs time, fitted speed, profile snapshots."""
    u = np.zeros(N)
    u[:seed_width] = 1.0
    pos, ts, profiles = [], [], []
    for s in range(steps):
        lap = (np.roll(u, 1) + np.roll(u, -1) - 2 * u) / cfg.dx ** 2
        u = u + cfg.dt * (cfg.D * lap + _react(u, cfg))
        np.clip(u, 0.0, 1.0, out=u)
        u[0] = 1.0; u[-1] = 0.0
        if s % 200 == 0:
            pos.append(_front_pos(u, cfg.dx)); ts.append(s * cfg.dt); profiles.append(u.copy())
    pos = np.asarray(pos); ts = np.asarray(ts)
    h = len(pos) // 2
    speed = float(np.polyfit(ts[h:], pos[h:], 1)[0])
    return {"u": u, "pos": pos, "ts": ts, "speed": speed, "profiles": profiles}


def run2d(cfg: FrontConfig, N: int = 200, steps: int = 1500, seed_radius: float = 20.0,
          record_every: int = 0):
    """2D radial colony. Returns final field, effective-radius vs time, snapshots."""
    u = np.zeros((N, N))
    yy, xx = np.indices((N, N))
    c = N / 2
    u[((xx - c) ** 2 + (yy - c) ** 2) < (seed_radius / cfg.dx) ** 2] = 1.0
    rad, ts, snaps = [], [], {}
    for s in range(steps):
        lap = (np.roll(u, 1, 0) + np.roll(u, -1, 0) + np.roll(u, 1, 1) + np.roll(u, -1, 1) - 4 * u) / cfg.dx ** 2
        u = u + cfg.dt * (cfg.D * lap + _react(u, cfg))
        np.clip(u, 0.0, 1.0, out=u)
        if s % 50 == 0:
            area = (u > 0.5).sum() * cfg.dx ** 2
            rad.append(float(np.sqrt(area / np.pi))); ts.append(s * cfg.dt)
        if record_every and s % record_every == 0:
            snaps[s] = u.copy()
    return {"u": u, "radius": np.asarray(rad), "ts": np.asarray(ts), "snaps": snaps}
