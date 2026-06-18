"""R38 — spatial reciprocity: cooperation survives because it clusters.

In a well-mixed prisoner's dilemma, defectors always win — cooperation is doomed.
Nowak & May (1992) showed that *space* changes everything: put the players on a
lattice where each only interacts with, and imitates, its neighbours, and
cooperators survive by forming clusters whose interiors reap mutual reward faster
than the defector fringe can erode them. Cooperation persists indefinitely, in
ever-shifting, famously fractal-like patterns — with no kinship, memory or
reputation, only locality.

This is the deterministic Nowak-May model: a Moore-neighbourhood lattice, payoff
b for defecting against a cooperator (1 < b < 2), 1 for mutual cooperation, 0
otherwise; every cell copies the highest-scoring strategy in its neighbourhood.
The control is the same game with positions reshuffled each step (well-mixed),
where cooperation collapses.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# the 9 Moore-neighbourhood offsets, including the cell itself
_OFFSETS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
_NEIGH = [(dx, dy) for (dx, dy) in _OFFSETS if not (dx == 0 and dy == 0)]


@dataclass(frozen=True)
class SpatialCoopConfig:
    size: int = 100            # lattice side
    b: float = 1.6             # temptation to defect (1 < b < 2); ~1.6 = coexistence
    steps: int = 200
    init_coop: float = 0.90    # initial cooperator fraction


def _neighbour_coop_count(coop: np.ndarray) -> np.ndarray:
    """How many of each cell's 8 neighbours cooperate (torus)."""
    c = coop.astype(np.float64)
    return sum(np.roll(np.roll(c, dx, 0), dy, 1) for dx, dy in _NEIGH)


def _scores(coop: np.ndarray, b: float) -> np.ndarray:
    """Nowak-May payoff: a cooperator scores its #C neighbours; a defector scores
    b times its #C neighbours (it exploits each cooperating neighbour)."""
    nc = _neighbour_coop_count(coop)
    return np.where(coop, nc, b * nc)


def _adopt_best(coop: np.ndarray, score: np.ndarray) -> np.ndarray:
    """Each cell copies the strategy of the highest-scoring cell in its Moore
    neighbourhood (including itself)."""
    best_score = np.full(coop.shape, -1.0)
    best_coop = coop.copy()
    for dx, dy in _OFFSETS:
        s = np.roll(np.roll(score, dx, 0), dy, 1)
        c = np.roll(np.roll(coop, dx, 0), dy, 1)
        take = s > best_score
        best_score = np.where(take, s, best_score)
        best_coop = np.where(take, c, best_coop)
    return best_coop


def run(cfg: SpatialCoopConfig, well_mixed: bool = False, seed: int = 0):
    rng = np.random.default_rng(seed)
    coop = rng.random((cfg.size, cfg.size)) < cfg.init_coop
    frac = [float(coop.mean())]
    snaps = {0: coop.copy()}
    for t in range(1, cfg.steps + 1):
        if well_mixed:
            # destroy spatial structure: reshuffle every cell's position each step
            flat = coop.ravel().copy()
            rng.shuffle(flat)
            coop = flat.reshape(coop.shape)
        score = _scores(coop, cfg.b)
        coop = _adopt_best(coop, score)
        frac.append(float(coop.mean()))
        if t in (5, 25, cfg.steps):
            snaps[t] = coop.copy()
    return {"coop_fraction": np.array(frac), "snaps": snaps, "final": coop}


def b_sweep(cfg: SpatialCoopConfig, bs, seed: int = 0) -> np.ndarray:
    """Steady-state cooperator fraction (spatial) across temptation values b."""
    out = []
    for b in bs:
        c = SpatialCoopConfig(size=cfg.size, b=float(b), steps=cfg.steps, init_coop=cfg.init_coop)
        r = run(c, well_mixed=False, seed=seed)
        out.append(float(np.mean(r["coop_fraction"][-30:])))
    return np.array(out)
