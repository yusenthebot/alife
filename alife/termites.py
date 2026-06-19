"""R133 — Termite construction: structure with no blueprint (stigmergy).

A termite colony builds mounds, pillars and arches with no architect, no plan, and no termite that sees
the whole. Grassé (1959) named the trick STIGMERGY: a termite deposits a grain of cement laced with a
pheromone, and that pheromone makes other termites more likely to deposit nearby. The structure itself
is the only coordination — work begets work. From a flat floor this positive feedback breaks symmetry:
tiny chance excesses seed mounds, the mounds' pheromone draws yet more cement, and the material
self-organises into piles. The colony "computes" a building through the environment, not a brain.

Model: random-walking termites on a toroidal grid; each deposits material with probability that rises
with the local pheromone; deposited material emits pheromone that diffuses and evaporates (setting an
interaction range). With the feedback ON, material clumps into MOUNDS; turn it off (deposit at random)
and the floor stays flat. Distinct from antcolony (foraging trails) and gpuslime (transport networks):
this is CONSTRUCTION — agents accreting persistent structure. Honest: in 2D the positive feedback
COARSENS into irregular mounds rather than the perfectly regular pillars of a real 3D nest. Pure numpy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TermiteConfig:
    L: int = 120
    n: int = 2500            # termites
    steps: int = 4000
    k: float = 6.0           # stigmergy strength: deposit prob rises by k*pheromone (0 = random)
    base: float = 0.02       # baseline deposit probability
    emit: float = 0.02       # pheromone emitted per unit material
    evap: float = 0.04       # pheromone evaporation
    diff: float = 0.18       # pheromone diffusion (sets the interaction range)
    seed: int = 0


def _lap(a):
    return np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1) - 4.0 * a


def run(cfg: TermiteConfig, record_every: int = 0):
    rng = np.random.default_rng(cfg.seed)
    L = cfg.L
    M = np.zeros((L, L))           # deposited material (the structure)
    P = np.zeros((L, L))           # cement pheromone
    ax = rng.integers(0, L, cfg.n)
    ay = rng.integers(0, L, cfg.n)
    snaps = []
    for t in range(cfg.steps):
        ax = (ax + rng.integers(-1, 2, cfg.n)) % L
        ay = (ay + rng.integers(-1, 2, cfg.n)) % L
        prob = cfg.base + cfg.k * P[ay, ax]                # stigmergy: build where others built
        dep = rng.random(cfg.n) < prob
        np.add.at(M, (ay[dep], ax[dep]), 1.0)
        P += cfg.diff * _lap(P) + cfg.emit * M - cfg.evap * P
        np.clip(P, 0.0, None, out=P)
        if record_every and (t % record_every == 0 or t == cfg.steps - 1):
            snaps.append(M.copy())
    return {"M": M, "P": P, "snaps": snaps, "pos": np.c_[ax, ay]}


def clustering(M) -> float:
    """Index of dispersion of the material field: ~1 flat/random, >1 clumped into mounds."""
    m = M.mean()
    return float(M.var() / m) if m > 0 else 0.0


def n_mounds(M, rel=0.6) -> int:
    """Count distinct mounds (connected blobs above rel*max)."""
    from scipy import ndimage
    if M.max() <= 0:
        return 0
    _, n = ndimage.label(M > rel * M.max())
    return int(n)


def clustering_curve(ks, cfg: TermiteConfig):
    """Material clustering vs stigmergy strength k — flat (~1) at k=0, rising as feedback grows."""
    from dataclasses import replace
    return np.asarray(ks, float), np.array([clustering(run(replace(cfg, k=float(k)))["M"]) for k in ks])
