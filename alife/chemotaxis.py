"""R95 — Bacterial chemotaxis: climbing a gradient with no sense of direction.

An E. coli bacterium is far too small to sense which way "uphill" is — across its body the
concentration difference is swamped by noise. Yet it reliably swims toward food. Berg's resolution
(run-and-tumble): the cell alternates straight RUNS with random reorienting TUMBLES, and it biases
the walk in time, not space. It remembers the concentration it just saw and, when things are getting
better, SUPPRESSES tumbling — so favourable runs last longer. That single temporal trick turns an
undirected random walk into a steady climb up the gradient. Remove the modulation and the same cell
just diffuses. A minimal model of sensing, memory and goal-directed motion with no map.

Vectorized over N cells on a smooth attractant field; pure numpy/CPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ChemoConfig:
    world: float = 100.0
    width: float = 20.0         # attractant width (steep enough to leave room to climb)
    speed: float = 1.2          # run speed
    p0: float = 0.25            # baseline tumble probability per step
    alpha: float = 6.0          # how strongly improvement suppresses tumbling (0 = no chemotaxis)
    p_min: float = 0.02
    p_max: float = 0.9
    steps: int = 700


def gaussian_field(world=100.0, width=20.0):
    """A smooth attractant peak at the centre; returns conc(xy) and grad-free sampling."""
    cx = cy = world / 2.0

    def conc(xy):
        d2 = (xy[:, 0] - cx) ** 2 + (xy[:, 1] - cy) ** 2
        return np.exp(-d2 / (2.0 * width ** 2))
    return conc, (cx, cy)


def simulate(cfg=ChemoConfig(), n=400, seed=0, record_every=0):
    """Run N run-and-tumble cells. Returns mean concentration & mean distance-to-source over time,
    final positions, and (optionally) recorded position snapshots."""
    rng = np.random.default_rng(seed)
    conc, (cx, cy) = gaussian_field(cfg.world, cfg.width)
    pos = rng.uniform(0, cfg.world, (n, 2))
    ang = rng.uniform(0, 2 * np.pi, n)
    c_prev = conc(pos)
    mean_c, mean_d, snaps = [], [], {}
    for t in range(cfg.steps):
        c_now = conc(pos)
        dc = c_now - c_prev                                  # temporal derivative along the path
        # improving (dc>0) -> suppress tumbling; worsening -> tumble more
        p_tumble = np.clip(cfg.p0 * np.exp(-cfg.alpha * dc / max(cfg.speed, 1e-6)), cfg.p_min, cfg.p_max)
        tumble = rng.random(n) < p_tumble
        ang = np.where(tumble, rng.uniform(0, 2 * np.pi, n), ang)
        pos = pos + cfg.speed * np.c_[np.cos(ang), np.sin(ang)]
        pos = np.clip(pos, 0, cfg.world)                     # reflective-ish walls
        hit = (pos <= 0) | (pos >= cfg.world)
        ang = np.where(hit.any(axis=1), rng.uniform(0, 2 * np.pi, n), ang)
        c_prev = c_now
        mean_c.append(float(conc(pos).mean()))
        mean_d.append(float(np.hypot(pos[:, 0] - cx, pos[:, 1] - cy).mean()))
        if record_every and (t % record_every == 0 or t == cfg.steps - 1):
            snaps[t] = pos.copy()
    return {"mean_c": np.asarray(mean_c), "mean_d": np.asarray(mean_d),
            "pos": pos, "snaps": snaps, "center": (cx, cy), "width": cfg.width}


def chemotactic_index(result):
    """Fraction of cells that ended within one field-width of the source (accumulation)."""
    cx, cy = result["center"]
    d = np.hypot(result["pos"][:, 0] - cx, result["pos"][:, 1] - cy)
    return float(np.mean(d < result["width"]))
