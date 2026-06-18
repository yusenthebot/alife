"""R74 — The abelian sandpile (Bak-Tang-Wiesenfeld): self-organized criticality on a lattice.

The original SOC model (1987), and the spatial twin of R71's Bak-Sneppen. Grains of sand drop
onto a grid; when a pile reaches 4 it TOPPLES, sending one grain to each neighbour, which can
trigger neighbours to topple in turn — an avalanche. Drive the lattice slowly (one grain at a
time, relax fully) and it self-organizes to a critical state where avalanche sizes follow a
POWER LAW: most additions do nothing, a few cascade across the whole system, with no
characteristic scale. And the pile is "abelian" — the final stable configuration is independent
of the order of topplings — so a single huge point source relaxes into a striking, deterministic
SELF-SIMILAR FRACTAL. Two faces of the same rule: critical avalanches and emergent fractal order.

Pure numpy/CPU; vectorized parallel toppling (each cell topples grid//4 times per sweep).
"""

from __future__ import annotations

import numpy as np


def relax(grid: np.ndarray):
    """Topple to a stable configuration (all heights < 4), open boundary (edge grains are lost).
    Returns (stable grid, total number of individual topplings). Abelian: order-independent."""
    g = grid.astype(np.int64).copy()
    topples = 0
    while True:
        t = g // 4                                   # how many times each cell topples this sweep
        if not t.any():
            break
        topples += int(t.sum())
        g -= 4 * t
        g[1:, :] += t[:-1, :]                        # grains flow to the 4 neighbours (no wrap = open edge)
        g[:-1, :] += t[1:, :]
        g[:, 1:] += t[:, :-1]
        g[:, :-1] += t[:, 1:]
    return g, topples


def add_grain(grid: np.ndarray, x: int, y: int):
    """Drop one grain at (y,x) and relax; return (new grid, avalanche size = # topplings)."""
    grid = grid.copy()
    grid[y, x] += 1
    return relax(grid)


def point_source(size: int, n_grains: int):
    """Drop n_grains at the centre of an empty grid and relax -> the fractal sandpile.
    (Abelian: piling all grains then relaxing equals dropping them one at a time.)"""
    g = np.zeros((size, size), dtype=np.int64)
    g[size // 2, size // 2] = n_grains
    g, topples = relax(g)
    return g, topples


def drive_soc(size: int, warmup: int, measure: int, seed: int = 0, center: bool = False):
    """Slowly drive a lattice (one grain at a time, relax fully) and record avalanche sizes in
    the self-organized steady state. Returns (avalanche_sizes, final_grid, mean_height)."""
    rng = np.random.default_rng(seed)
    g = np.zeros((size, size), dtype=np.int64)
    c = size // 2
    for _ in range(warmup):                          # reach the critical steady state
        x, y = (c, c) if center else (int(rng.integers(size)), int(rng.integers(size)))
        g, _ = add_grain(g, x, y)
    sizes = np.empty(measure, dtype=np.int64)
    for i in range(measure):
        x, y = (c, c) if center else (int(rng.integers(size)), int(rng.integers(size)))
        g, s = add_grain(g, x, y)
        sizes[i] = s
    return sizes, g, float(g.mean())


def avalanche_powerlaw(sizes: np.ndarray, smin: int = 1, smax: int = None):
    """Log-log slope of the avalanche size distribution (BTW exponent τ ≈ 1.0–1.2 in 2D)."""
    s = sizes[sizes >= max(smin, 1)]
    if smax:
        s = s[s <= smax]
    if len(s) < 10:
        return np.array([]), np.array([]), float("nan")
    bins = np.unique(np.round(np.logspace(0, np.log10(s.max()), 22)).astype(int))
    hist, edges = np.histogram(s, bins=bins, density=True)
    centers = np.sqrt(edges[:-1] * edges[1:])
    ok = hist > 0
    centers, hist = centers[ok], hist[ok]
    slope = np.polyfit(np.log10(centers), np.log10(hist), 1)[0]
    return centers, hist, float(slope)
