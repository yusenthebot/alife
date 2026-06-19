"""R131 — Excitable media (Barkley model): the spiral and target waves of the BZ reaction.

Drop a dish of Belousov-Zhabotinsky reagent and it does not just change colour — it throws out
expanding rings of oxidation from pacemaker spots (TARGET waves) and, where a wave is broken, winds
into rotating SPIRAL waves that beat forever with no external clock. The same waves run across heart
tissue, retina, and slime-mould colonies. They are the signature of an EXCITABLE medium: a cell sits at
a stable rest state, ignores small kicks, but if kicked past a threshold it fires a big pulse, then
enters a refractory dead-time before it can fire again. A firing cell excites its neighbours, so the
pulse propagates; the refractory tail stops it doubling back, so a broken front curls into a spiral.

The Barkley model is the standard fast reduction (distinct from R88 excitable.py, a discrete Greenberg-
Hastings cellular automaton — this is the continuum reaction-diffusion PDE with real wave speed and
spiral-tip motion):

    du/dt = D lap(u) + (1/eps) u (1-u) (u - (v+b)/a)      (fast excitation u, with threshold (v+b)/a)
    dv/dt = u - v                                          (slow recovery v, the refractory variable)

A periodically-firing pacemaker emits concentric TARGET rings whose spacing = wave speed x pacemaker
period; a broken initial front becomes a rotating SPIRAL. Pure numpy/CPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BarkleyConfig:
    N: int = 220
    a: float = 0.75
    b: float = 0.02
    eps: float = 0.02
    Du: float = 1.0
    dt: float = 0.005
    steps: int = 6000
    seed: int = 0


def _lap(f):
    return np.roll(f, 1, 0) + np.roll(f, -1, 0) + np.roll(f, 1, 1) + np.roll(f, -1, 1) - 4.0 * f


def step(u, v, cfg: BarkleyConfig):
    u = u + cfg.dt * (cfg.Du * _lap(u) + (1.0 / cfg.eps) * u * (1.0 - u) * (u - (v + cfg.b) / cfg.a))
    v = v + cfg.dt * (u - v)
    np.clip(u, 0.0, 1.0, out=u)
    return u, v


def spiral_ic(cfg: BarkleyConfig):
    """A broken wavefront: excited left half + refractory top half -> the free end winds into a spiral."""
    N = cfg.N
    u = np.zeros((N, N))
    v = np.zeros((N, N))
    u[:, : N // 2] = 1.0
    v[: N // 2, :] = cfg.a * 0.5
    return u, v


def run_spiral(cfg: BarkleyConfig, record_every: int = 0):
    u, v = spiral_ic(cfg)
    snaps = []
    for t in range(cfg.steps):
        u, v = step(u, v, cfg)
        if record_every and (t % record_every == 0 or t == cfg.steps - 1):
            snaps.append(u.copy())
    return {"u": u, "v": v, "snaps": snaps, "activity": float((u > 0.5).mean())}


def run_target(cfg: BarkleyConfig, pace_period: int = 320, pace_dur: int = 6, record_every: int = 0):
    """A central pacemaker fires every `pace_period` steps -> concentric target rings."""
    N = cfg.N
    u = np.zeros((N, N))
    v = np.zeros((N, N))
    c = N // 2
    snaps = []
    for t in range(cfg.steps):
        if t % pace_period < pace_dur:
            u[c - 2:c + 2, c - 2:c + 2] = 1.0
        u, v = step(u, v, cfg)
        if record_every and (t % record_every == 0 or t == cfg.steps - 1):
            snaps.append(u.copy())
    return {"u": u, "v": v, "snaps": snaps}


def _lap1d(f):
    o = np.empty_like(f)
    o[1:-1] = f[2:] - 2.0 * f[1:-1] + f[:-2]
    o[0] = f[1] - f[0]
    o[-1] = f[-2] - f[-1]                                  # zero-flux ends
    return o


def wave_speed(cfg: BarkleyConfig, length=400, steps=1500) -> float:
    """Front speed in a 1D excitable cable: excite one end, track the front position (cells/time)."""
    u = np.zeros(length)
    v = np.zeros(length)
    u[:4] = 1.0
    pos, ts = [], []
    for t in range(steps):
        u = u + cfg.dt * (cfg.Du * _lap1d(u) + (1.0 / cfg.eps) * u * (1.0 - u) * (u - (v + cfg.b) / cfg.a))
        v = v + cfg.dt * (u - v)
        np.clip(u, 0.0, 1.0, out=u)
        fr = np.where(u > 0.5)[0]
        if fr.size:
            pos.append(fr.max()); ts.append(t * cfg.dt)
    pos, ts = np.asarray(pos), np.asarray(ts)
    m = (pos > 10) & (pos < length - 10)                  # ignore launch transient + far boundary
    if m.sum() < 5:
        return 0.0
    return float(np.polyfit(ts[m], pos[m], 1)[0])


def excited_fraction(u, thresh=0.5) -> float:
    return float((u > thresh).mean())


def ring_count(u, thresh=0.5) -> int:
    """Number of concentric excited rings along a radius from the centre (target-wave wavelength proxy)."""
    N = u.shape[0]
    c = N // 2
    line = u[c, c:] > thresh                                # radial ray to the right edge
    return int(np.sum(line[1:] & ~line[:-1]))              # rising edges = rings
