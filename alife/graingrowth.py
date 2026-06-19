"""R136 — Grain growth: a polycrystal coarsens by curvature, like soap froth or annealed metal.

Quench a melt and it freezes into a mosaic of randomly-oriented crystal grains; heat it and the mosaic
COARSENS — small grains shrink and vanish, big grains swallow them, the average grain grows. The same
thing happens in a soap froth: small bubbles disappear, large ones grow, and the foam gets coarser over
time. The driving force is simply boundary energy: every grain boundary costs energy proportional to its
length, so the network relaxes by straightening and retracting boundaries — curved boundaries migrate
toward their centre of curvature (von Neumann-Mullins). The signature is a power-law coarsening: the mean
grain area grows like a power of time, equivalently the total boundary length per area decays.

Model: the Q-state Potts model (Anderson-Srolovitz-Grest 1984). Each lattice site carries one of Q grain
orientations; the energy counts unlike-neighbour bonds (boundary length). Metropolis dynamics at low T:
a site proposes to adopt a random neighbour's orientation, accepted if it lowers boundary energy (thermal
noise lets it hop over lattice pinning). No area constraint, no type-dependent adhesion — pure boundary
minimisation, which makes this DISTINCT from the cellular Potts model in cellsort.py (cell sorting by
differential adhesion + an area constraint). Vectorised checkerboard update; numpy + scipy.ndimage.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import label as _label


@dataclass(frozen=True)
class GrainConfig:
    L: int = 200
    Q: int = 64          # number of grain orientations
    T: float = 0.6       # temperature (thermal noise to beat lattice pinning)
    greedy: bool = False  # True = accept only strictly-downhill moves (no noise) -> lattice pinning control
    steps: int = 200
    seed: int = 0


def bond_density(s) -> float:
    """Fraction of unlike nearest-neighbour bonds = total boundary length per site."""
    up = (s != np.roll(s, 1, 0))
    lf = (s != np.roll(s, 1, 1))
    return float((up.sum() + lf.sum()) / (2 * s.size))


def count_grains(s) -> int:
    """Number of connected single-orientation domains (4-connectivity), summed over orientations."""
    total = 0
    for q in np.unique(s):
        _, n = _label(s == q)
        total += n
    return total


def _sweep(s, T, rng, greedy=False):
    L = s.shape[0]
    ii, jj = np.indices((L, L))
    for color in (0, 1):
        m = ((ii + jj) % 2 == color)
        nb = np.stack([np.roll(s, 1, 0), np.roll(s, -1, 0), np.roll(s, 1, 1), np.roll(s, -1, 1)])
        prop = np.take_along_axis(nb, rng.integers(0, 4, (L, L))[None], 0)[0]
        old = sum((s != n).astype(np.int8) for n in nb)
        new = sum((prop != n).astype(np.int8) for n in nb)
        dE = new - old
        if greedy:
            accept = dE < 0                        # strictly downhill only -> freezes (pinning control)
        else:
            accept = (dE <= 0) | (rng.random((L, L)) < np.exp(-np.clip(dE, 0, None) / T))
        s = np.where(accept & m, prop, s)
    return s


def run(cfg: GrainConfig, log_at=None, record_at=None):
    """Anneal a random polycrystal. Returns final field, coarsening history, optional snapshots."""
    rng = np.random.default_rng(cfg.seed)
    s = rng.integers(0, cfg.Q, (cfg.L, cfg.L))
    log_at = set(log_at or [])
    record_at = set(record_at or [])
    ts, bd, ng, snaps = [], [], [], {}
    for step in range(cfg.steps + 1):
        if step in log_at:
            ts.append(step); bd.append(bond_density(s)); ng.append(count_grains(s))
        if step in record_at:
            snaps[step] = s.copy()
        if step < cfg.steps:
            s = _sweep(s, cfg.T, rng, cfg.greedy)
    return {"s": s, "t": np.asarray(ts), "bond": np.asarray(bd, float),
            "ngrains": np.asarray(ng, float), "snaps": snaps}


def coarsening_exponent(ts, vals) -> float:
    """Log-log slope of vals vs ts (skip t=0)."""
    ts = np.asarray(ts, float); vals = np.asarray(vals, float)
    keep = ts > 0
    return float(np.polyfit(np.log(ts[keep]), np.log(vals[keep]), 1)[0])
