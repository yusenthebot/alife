"""R93 — Schelling segregation: how mild preferences make extreme separation.

Thomas Schelling's 1971 model is the canonical demonstration that macro-patterns need not mirror
micro-motives. Two kinds of agents share a grid with some empty cells. An agent is content as long as
at least a fraction tau of its occupied neighbours are its own kind, and relocates to a random empty
cell otherwise. No agent wants segregation — a tolerant agent is happy in a mixed neighbourhood — yet
even a mild preference (tau ~ 0.3, "I just want a third of my neighbours to be like me") drives the
whole grid into large, sharply separated single-type blocks. Sweeping tau reveals a tipping point:
below it the grid stays mixed, above it it segregates, and at very high tau no one can ever be
satisfied so the grid never settles. Emergent segregation from individually-modest preferences.

Pure numpy + scipy convolution; CPU-fast.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import convolve2d

MOORE = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.int32)


def init_grid(size, frac_empty=0.1, seed=0):
    """Two agent types (1, 2) in equal share plus empty cells (0), placed at random."""
    rng = np.random.default_rng(seed)
    cells = rng.random((size, size))
    grid = np.where(cells < frac_empty, 0, np.where(cells < frac_empty + (1 - frac_empty) / 2, 1, 2))
    return grid.astype(np.int8)


def _same_frac(grid):
    """For every occupied cell, the fraction of its occupied neighbours that share its type."""
    a = (grid == 1).astype(np.int32)
    b = (grid == 2).astype(np.int32)
    na = convolve2d(a, MOORE, mode="same", boundary="fill")
    nb = convolve2d(b, MOORE, mode="same", boundary="fill")
    occ = na + nb
    same = np.where(grid == 1, na, nb).astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        frac = np.where(occ > 0, same / occ, 1.0)         # isolated agents count as content
    return frac, occ


def unhappy_mask(grid, tau):
    frac, occ = _same_frac(grid)
    return (grid > 0) & (occ > 0) & (frac < tau)


def step(grid, tau, rng):
    """One relocation round: unhappy agents and empty cells are randomly reshuffled among their
    combined sites (happy agents stay put)."""
    unhappy = unhappy_mask(grid, tau)
    empty = grid == 0
    pool = unhappy | empty
    coords = np.argwhere(pool)
    if len(coords) == 0:
        return grid, 0
    tokens = grid[unhappy]                                 # the agents that move
    tokens = np.concatenate([tokens, np.zeros(int(empty.sum()), np.int8)])
    rng.shuffle(tokens)
    new = grid.copy()
    new[coords[:, 0], coords[:, 1]] = tokens
    return new, int(unhappy.sum())


def segregation(grid):
    """Mean same-type neighbour fraction over occupied cells (0.5 = mixed, →1 = segregated)."""
    frac, occ = _same_frac(grid)
    m = (grid > 0) & (occ > 0)
    return float(frac[m].mean()) if m.any() else 0.0


def happiness(grid, tau):
    """Fraction of agents that are content."""
    agents = grid > 0
    if not agents.any():
        return 1.0
    return float(1.0 - unhappy_mask(grid, tau).sum() / agents.sum())


def run(size=80, frac_empty=0.1, tau=0.3, steps=60, seed=0):
    rng = np.random.default_rng(seed)
    grid = init_grid(size, frac_empty, seed)
    seg_hist = [segregation(grid)]
    happy_hist = [happiness(grid, tau)]
    moved_hist = []
    for _ in range(steps):
        grid, moved = step(grid, tau, rng)
        seg_hist.append(segregation(grid))
        happy_hist.append(happiness(grid, tau))
        moved_hist.append(moved)
        if moved == 0:
            break
    return {"grid": grid, "seg": np.asarray(seg_hist), "happy": np.asarray(happy_hist),
            "moved": np.asarray(moved_hist), "final_seg": seg_hist[-1], "final_happy": happy_hist[-1]}


def tipping_curve(taus, size=70, frac_empty=0.1, steps=60, seed=0):
    """Final segregation index as a function of the tolerance threshold tau."""
    rng = np.random.default_rng(seed)
    out = []
    for t in taus:
        r = run(size, frac_empty, float(t), steps, seed=int(rng.integers(1 << 30)))
        out.append(r["final_seg"])
    return np.asarray(taus, float), np.asarray(out)
