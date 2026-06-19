"""R97 — Percolation: the geometric birth of long-range connectivity.

Fill each cell of a grid independently with probability p and ask: does an unbroken cluster of filled
cells span from one side to the other? Percolation is the simplest model of a connectivity phase
transition and underlies forest fires, porous flow, epidemics and conductivity. The striking fact is
sharpness: below a critical density p_c the grid holds only small finite clusters; the instant p
crosses p_c (≈0.5927 for 2D site percolation on a square lattice) a single SPANNING cluster appears
and the largest-cluster fraction jumps from ~0 to a finite value. Exactly at p_c the cluster sizes are
scale-free — a power law n(s) ~ s^(-tau) with the Fisher exponent tau ≈ 2 — the signature of
criticality, with no tuning beyond setting p = p_c.

scipy.ndimage connected components; CPU-fast.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage

PC_2D = 0.592746        # site percolation threshold, 2D square lattice (4-connectivity)
_CROSS = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])     # 4-connectivity


def occupy(size, p, seed=0):
    return (np.random.default_rng(seed).random((size, size)) < p)


def label_clusters(grid):
    lbl, n = ndimage.label(grid, structure=_CROSS)
    return lbl, n


def spans(grid):
    """True if one cluster touches both the top and bottom rows (vertical spanning)."""
    lbl, n = label_clusters(grid)
    if n == 0:
        return False
    top = set(lbl[0][lbl[0] > 0])
    bot = set(lbl[-1][lbl[-1] > 0])
    return len(top & bot) > 0


def largest_fraction(grid):
    """Size of the largest cluster as a fraction of all cells (percolation order parameter)."""
    lbl, n = label_clusters(grid)
    if n == 0:
        return 0.0
    sizes = np.bincount(lbl.ravel())[1:]
    return float(sizes.max() / grid.size)


def cluster_sizes(grid):
    lbl, n = label_clusters(grid)
    return np.bincount(lbl.ravel())[1:] if n else np.array([], int)


def spanning_probability(size, p, trials=40, seed=0):
    rng = np.random.default_rng(seed)
    return float(np.mean([spans(occupy(size, p, int(rng.integers(1 << 30)))) for _ in range(trials)]))


def sweep_p(ps, size=80, trials=40, seed=0, measure="span"):
    """Spanning probability (or mean largest-cluster fraction) vs occupation probability p."""
    rng = np.random.default_rng(seed)
    out = []
    for p in ps:
        if measure == "span":
            out.append(spanning_probability(size, float(p), trials, int(rng.integers(1 << 30))))
        else:
            out.append(float(np.mean([largest_fraction(occupy(size, float(p), int(rng.integers(1 << 30))))
                                      for _ in range(trials)])))
    return np.asarray(ps, float), np.asarray(out)


def cluster_size_distribution(size, p, trials=30, seed=0, nbins=22):
    """Log-binned cluster-size distribution (excludes the spanning cluster) — power-law at p_c."""
    rng = np.random.default_rng(seed)
    all_sizes = []
    for _ in range(trials):
        s = cluster_sizes(occupy(size, p, int(rng.integers(1 << 30))))
        if s.size:
            all_sizes.append(s[s < s.max()] if p >= PC_2D and s.size > 1 else s)
    sizes = np.concatenate(all_sizes) if all_sizes else np.array([1])
    bins = np.unique(np.round(np.logspace(0, np.log10(max(sizes.max(), 2)), nbins)).astype(int))
    hist, edges = np.histogram(sizes, bins=bins)
    centers = np.sqrt(edges[:-1] * edges[1:])
    widths = np.diff(edges)
    dens = hist / (widths * sizes.size)
    keep = hist > 0
    return centers[keep], dens[keep]
