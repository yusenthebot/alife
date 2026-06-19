"""R123 — Self-propelled particles: the same swarm becomes a spinning MILL or a marching FLOCK.

Fish schools, bird flocks, bacterial swarms and locust bands all run on the same three urges — don't
collide, stay together, go with the flow — yet they settle into strikingly different SHAPES you can
name at a glance. D'Orsogna, Chuang, Bertozzi & Chayes (2006) captured this with a Newtonian
self-propelled-particle model: each particle is driven toward a preferred speed by a self-propulsion /
drag term (alpha - beta|v|^2)v, and interacts with the others through a Morse potential — short-range
REPULSION, longer-range ATTRACTION. Add a weak tendency to ALIGN with neighbours and one parameter
flips the collective state between the two iconic, instantly-recognisable forms:

  * MILL  (no alignment): a hollow rotating RING — everyone circles a common empty centre, with NO net
          heading. The donut you cannot get from Reynolds boids (R1 boids/boids3d/swarm3d only flock).
  * FLOCK (alignment on): a cohesive group that all points one way and MARCHES across the arena.
  * CLUMP (weak self-propulsion): a tight, slow, disordered blob that just sits there.

You verify the state by EYE (a spinning hole vs a moving arrow vs a still blob) and confirm it with two
order parameters: polarization P = |mean heading| and milling M = |mean of the signed (r x v) about the
centroid|. The (P,M) signature is unambiguous: mill (P~0, M~1), flock (P~1, M~0), clump (P~0, M~0).
Newtonian force model — distinct from Reynolds heading-rule boids. Pure numpy/CPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SPPConfig:
    N: int = 300
    alpha: float = 1.6        # self-propulsion (drives toward preferred speed sqrt(alpha/beta))
    beta: float = 0.5         # drag
    Cr: float = 1.0           # Morse repulsion strength
    lr: float = 0.5           # repulsion length
    Ca: float = 0.5           # Morse attraction strength
    la: float = 2.0           # attraction length
    align: float = 0.0        # alignment strength: 0 -> mill, >~0.5 -> flock
    dt: float = 0.05
    steps: int = 2500
    seed: int = 0


def init(cfg: SPPConfig, rng):
    return rng.uniform(-3, 3, (cfg.N, 2)), rng.normal(0, 0.3, (cfg.N, 2))


def _unit(a):
    return a / np.maximum(np.linalg.norm(a, axis=-1, keepdims=True), 1e-9)


def morse_force(x, cfg: SPPConfig):
    """Net Morse force on each particle: short-range repulsion + longer-range attraction."""
    d = x[:, None, :] - x[None, :, :]                      # d[i,j] = x_i - x_j
    r = np.sqrt((d ** 2).sum(2))
    np.fill_diagonal(r, np.inf)
    r = np.maximum(r, 1e-3)
    # F = -grad U, U = Cr e^{-r/lr} - Ca e^{-r/la}; positive -> push i away from j (repel)
    fmag = (cfg.Cr / cfg.lr * np.exp(-r / cfg.lr) - cfg.Ca / cfg.la * np.exp(-r / cfg.la)) / r
    return (fmag[:, :, None] * d).sum(1), r


def step(x, v, cfg: SPPConfig):
    F, r = morse_force(x, cfg)
    if cfg.align > 0:
        near = r < cfg.la
        vsum = (v[None, :, :] * near[:, :, None]).sum(1)
        F = F + cfg.align * (_unit(vsum) - _unit(v))       # bounded torque toward neighbours' heading
    sp2 = (v ** 2).sum(1, keepdims=True)
    v = v + cfg.dt * ((cfg.alpha - cfg.beta * sp2) * v + F)
    x = x + cfg.dt * v
    return x, v


def polarization(v) -> float:
    """P = |mean heading|: ~1 flock, ~0 mill/clump."""
    return float(np.linalg.norm(_unit(v).mean(axis=0)))


def milling(x, v) -> float:
    """M = |mean signed (r_hat x v)| about the centroid: ~1 rotating mill, ~0 flock/clump."""
    r = x - x.mean(axis=0)
    rn = np.maximum(np.linalg.norm(r, axis=1), 1e-9)
    vu = _unit(v)
    cross = r[:, 0] * vu[:, 1] - r[:, 1] * vu[:, 0]
    return float(np.abs((cross / rn).mean()))


def run(cfg: SPPConfig, record_every: int = 0):
    rng = np.random.default_rng(cfg.seed)
    x, v = init(cfg, rng)
    P, M, snaps = [], [], []
    for t in range(cfg.steps):
        x, v = step(x, v, cfg)
        P.append(polarization(v)); M.append(milling(x, v))
        if record_every and (t % record_every == 0 or t == cfg.steps - 1):
            snaps.append((x.copy(), v.copy()))
    return {"x": x, "v": v, "P": np.asarray(P), "M": np.asarray(M), "snaps": snaps}


PRESETS = {
    "mill":  SPPConfig(align=0.0, alpha=1.6),
    "flock": SPPConfig(align=2.0, alpha=1.6),
    "clump": SPPConfig(align=0.0, alpha=0.15),
}


def classify(P, M, pol=0.5, mill=0.5) -> str:
    """Name the collective state from the (polarization, milling) signature."""
    if P >= pol:
        return "flock"
    if M >= mill:
        return "mill"
    return "clump"
