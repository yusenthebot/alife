"""R99 — Motility-induced phase separation: clustering with no attraction.

Ordinary phase separation (oil and water, R79 cell-sorting) needs attractive forces. Active matter
can do it with none. Self-propelled particles that simply SLOW DOWN where they are crowded undergo
"motility-induced phase separation" (MIPS): a slow-in-crowds rule creates a runaway — particles pile
up where they are slow, which makes them slower, which piles up more — until the system splits into a
dense, nearly-frozen cluster and a dilute active gas. There is no cohesion anywhere; the cluster is
held together purely by the dynamics of self-propulsion. It is the textbook example of how activity
alone produces order, and a candidate mechanism for bacterial colonies and synthetic active colloids.

Active Brownian particles with a density-dependent speed v(ρ)=v0·max(0,1−ρ/ρ*); coarse-grid density,
periodic box; pure numpy/CPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MIPSConfig:
    n: int = 4000
    box: float = 100.0
    v0: float = 4.0           # base self-propulsion speed (0 = passive control)
    rho_star: float = 1.4     # density at which motion stalls (relative to cell area)
    cell: float = 4.0         # sensing/coarse-grid cell size
    Dr: float = 0.03          # rotational diffusion (low = persistent runs)
    dt: float = 1.0
    steps: int = 600


def _cell_counts(pos, box, ncell):
    ix = np.clip((pos[:, 0] / box * ncell).astype(int), 0, ncell - 1)
    iy = np.clip((pos[:, 1] / box * ncell).astype(int), 0, ncell - 1)
    flat = ix * ncell + iy
    counts = np.bincount(flat, minlength=ncell * ncell)
    return flat, counts


def simulate(cfg=MIPSConfig(), seed=0, record_every=0):
    """Run active Brownian particles with density-dependent speed. Returns final positions, the
    coarse density field, and a clustering metric over time."""
    rng = np.random.default_rng(seed)
    pos = rng.uniform(0, cfg.box, (cfg.n, 2))
    theta = rng.uniform(0, 2 * np.pi, cfg.n)
    ncell = max(1, int(cfg.box / cfg.cell))
    cell_area = (cfg.box / ncell) ** 2
    clustering, snaps = [], {}
    for t in range(cfg.steps):
        flat, counts = _cell_counts(pos, cfg.box, ncell)
        rho = counts[flat] / cell_area
        v = cfg.v0 * np.clip(1.0 - rho / cfg.rho_star, 0.0, 1.0)
        theta = theta + np.sqrt(2 * cfg.Dr * cfg.dt) * rng.standard_normal(cfg.n)
        pos = (pos + (v * cfg.dt)[:, None] * np.c_[np.cos(theta), np.sin(theta)]) % cfg.box
        if t >= cfg.steps // 2:
            clustering.append(_dense_fraction(pos, cfg.box, ncell))
        if record_every and (t % record_every == 0 or t == cfg.steps - 1):
            snaps[t] = pos.copy()
    flat, counts = _cell_counts(pos, cfg.box, ncell)
    return {"pos": pos, "counts": counts.reshape(ncell, ncell), "ncell": ncell,
            "dense_fraction": float(np.mean(clustering)), "snaps": snaps, "cell_area": cell_area}


def _dense_fraction(pos, box, ncell):
    """Fraction of particles sitting in cells whose occupancy exceeds 3x the mean (cluster mass)."""
    flat, counts = _cell_counts(pos, box, ncell)
    mean = counts[counts > 0].mean()
    dense_cells = counts > 3 * mean
    return float(dense_cells[flat].sum() / len(flat))


def density_cv(result):
    """Coefficient of variation of cell occupancy: ~uniform for a gas, large when phase-separated."""
    c = result["counts"].ravel().astype(float)
    return float(c.std() / c.mean()) if c.mean() > 0 else 0.0
