"""R49 — evolutionary branching: one lineage splits in two (adaptive dynamics).

A population sits on a one-dimensional niche axis (say beak size, or where on a
resource gradient it feeds). Resources are richest at the centre — a carrying
capacity K(x) peaked at x=0 — so directional selection pulls the trait toward 0.
But individuals with similar traits compete most fiercely (competition kernel of
width sigma_c). When competition is narrower than the resource distribution
(sigma_c < sigma_K), the centre becomes a *branching point*: once the population
arrives there, being different from the crowd pays, and disruptive
frequency-dependent selection splits the single lineage into two that diverge and
coexist. Widen the competition (sigma_c > sigma_K) and no branching occurs — the
population just sits at the centre. This is evolutionary branching (Geritz et al.
1998), a route to diversification with no geography and no mating barrier.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AdaptiveDynConfig:
    pop: int = 500
    sigma_k: float = 1.0       # breadth of the resource / carrying-capacity curve
    sigma_c: float = 0.5       # width of the competition kernel (< sigma_k -> branching)
    generations: int = 700
    mut: float = 0.03          # mutation step on the trait
    x0_spread: float = 0.05    # initial trait spread (start as one cluster near 0)


def evolve(cfg: AdaptiveDynConfig, seed: int = 0):
    rng = np.random.default_rng(seed)
    x = rng.normal(0.6, cfg.x0_spread, cfg.pop)     # start as one cluster, off-centre
    hist = np.empty((cfg.generations + 1, cfg.pop))
    hist[0] = x
    for g in range(cfg.generations):
        # Lotka-Volterra competition fitness: carrying capacity / mean competition load
        K = np.exp(-x ** 2 / (2 * cfg.sigma_k ** 2))
        d = x[:, None] - x[None, :]
        comp = np.exp(-d ** 2 / (2 * cfg.sigma_c ** 2)).mean(axis=1)
        w = np.maximum(K / comp, 1e-9)
        parents = rng.choice(cfg.pop, cfg.pop, p=w / w.sum())
        x = x[parents] + rng.normal(0, cfg.mut, cfg.pop)
        hist[g + 1] = x
    return hist


def n_clusters(x: np.ndarray, gap: float = 0.25) -> int:
    """Count clusters in a trait sample by gaps in the sorted values."""
    s = np.sort(x)
    return 1 + int(np.sum(np.diff(s) > gap))


def branched(hist: np.ndarray) -> bool:
    """Did the final population split into >=2 well-separated clusters?"""
    return n_clusters(hist[-1]) >= 2
