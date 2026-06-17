"""Evolution of cooperation — Hamilton's rule from assortment.

Altruism is a puzzle: a cooperator pays a cost c to give a partner a benefit b,
so a selfish defector always does better in any given pair. Cooperation can still
evolve if cooperators tend to meet cooperators — assortment (a stand-in for
relatedness). Each generation individuals pair up; with probability `assortment`
the pairing is like-with-like (similar cooperation tendency), otherwise random.
Sweeping assortment recovers Hamilton's rule exactly: cooperation evolves when
assortment·b > c, with the threshold at assortment = c/b.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CooperationConfig:
    pop: int = 1000
    generations: int = 250
    benefit: float = 4.0
    cost: float = 1.0
    mut: float = 0.03
    elite_frac: float = 0.4


def _pairs(p: np.ndarray, assortment: float, rng):
    """Pair indices; a fraction `assortment` of pairs are like-with-like."""
    n = p.shape[0]
    order = np.argsort(p)                      # similar traits adjacent
    rand = rng.permutation(n)
    use_assort = rng.random(n // 2) < assortment
    a = np.empty(n, int)
    # assorted pairs come from sorted order, random pairs from a permutation
    a[0::2] = np.where(use_assort, order[0::2], rand[0::2])
    a[1::2] = np.where(use_assort, order[1::2], rand[1::2])
    return a[0::2], a[1::2]


def evolve(cfg: CooperationConfig, assortment: float, seed: int = 0):
    rng = np.random.default_rng(seed)
    p = rng.uniform(0, 1, cfg.pop)             # P(cooperate)
    n_elite = max(2, int(cfg.pop * cfg.elite_frac))
    hist = []
    for _ in range(cfg.generations):
        hist.append(float(p.mean()))
        i, j = _pairs(p, assortment, rng)
        ci = rng.random(i.size) < p[i]
        cj = rng.random(j.size) < p[j]
        payoff = np.ones(cfg.pop)
        payoff[i] += cfg.benefit * cj - cfg.cost * ci
        payoff[j] += cfg.benefit * ci - cfg.cost * cj
        payoff = np.maximum(payoff, 1e-6)
        idx = rng.choice(cfg.pop, cfg.pop, p=payoff / payoff.sum())   # replicator (fitness-proportionate)
        p = np.clip(p[idx] + rng.normal(0, cfg.mut, cfg.pop), 0, 1)
    hist.append(float(p.mean()))
    return np.array(hist)


def sweep_assortment(cfg: CooperationConfig, assortments, seed: int = 0):
    """Final cooperation level vs assortment — should switch on near c/b."""
    return np.array([evolve(cfg, a, seed=seed)[-1] for a in assortments])
