"""Sympatric speciation — one population splitting into two species.

A single heritable trait, `diet` ∈ [0,1], under DISRUPTIVE selection: two
resources reward the extremes (diet≈0 and diet≈1) while a generalist (diet≈0.5)
does poorly at both. Disruptive selection alone makes two ecological morphs, but
random mating blends them back into one population. Add ASSORTATIVE mating (like
breeds with like) and the two clusters stop interbreeding — reproductive
isolation — so the population genuinely splits into two species. The contrast
between assortative and random mating is the experiment.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SpeciationConfig:
    pop: int = 600
    generations: int = 120
    sigma: float = 0.17      # resource specialization width (smaller = more disruptive)
    mut: float = 0.04
    tournament: int = 12     # assortative-mating strength (bigger = pickier mate)
    # population starts as a UNIFORM spread of diets (both resource peaks seeded);
    # disruptive selection then carves out the middle, and mating decides whether
    # the two surviving clusters stay isolated (speciate) or blend back.


def fitness(diet: np.ndarray, sigma: float, capacity: float = 120.0) -> np.ndarray:
    """Two resources at diet=0 and diet=1; generalists fall in the valley.

    Frequency-dependent: each resource is depleted by its consumers, so the rarer
    morph is favored (rare-morph advantage). This stably balances the two clusters
    at ~50/50 instead of letting one drift to fixation — the key to a *stable*
    two-species polymorphism.
    """
    a = np.exp(-(diet - 0.0) ** 2 / (2 * sigma ** 2))
    b = np.exp(-(diet - 1.0) ** 2 / (2 * sigma ** 2))
    avail_a = 1.0 / (1.0 + a.sum() / capacity)
    avail_b = 1.0 / (1.0 + b.sum() / capacity)
    return a * avail_a + b * avail_b + 1e-6


def bimodality_coefficient(x: np.ndarray) -> float:
    """Pearson BC = (skew² + 1)/kurtosis. > ~0.555 indicates bimodality."""
    n = x.size
    m = x.mean()
    s = x.std()
    if s < 1e-9:
        return 0.0
    g = (((x - m) ** 3).mean()) / s ** 3
    k = (((x - m) ** 4).mean()) / s ** 4
    return (g ** 2 + 1) / k


def _next_gen(diet: np.ndarray, cfg: SpeciationConfig, assortative: bool, rng) -> np.ndarray:
    n = diet.size
    fit = fitness(diet, cfg.sigma)
    probs = fit / fit.sum()
    p1 = rng.choice(n, n, p=probs)
    d1 = diet[p1]
    if assortative:
        cand = rng.choice(n, size=(n, cfg.tournament), p=probs)   # fitness-weighted suitors
        best = np.abs(diet[cand] - d1[:, None]).argmin(1)          # pick the most diet-similar
        d2 = diet[cand[np.arange(n), best]]
    else:
        d2 = diet[rng.choice(n, n, p=probs)]
    child = (d1 + d2) / 2 + rng.normal(0, cfg.mut, n)
    return np.clip(child, 0.0, 1.0)


def evolve(cfg: SpeciationConfig, assortative: bool, seed: int = 0):
    """Returns (history_of_diet_arrays, bimodality_curve)."""
    rng = np.random.default_rng(seed)
    diet = rng.uniform(0.0, 1.0, cfg.pop)
    hist, bc = [], []
    for _ in range(cfg.generations):
        hist.append(diet.copy())
        bc.append(bimodality_coefficient(diet))
        diet = _next_gen(diet, cfg, assortative, rng)
    hist.append(diet.copy()); bc.append(bimodality_coefficient(diet))
    return hist, np.array(bc)


def count_species(diet: np.ndarray, gap: float = 0.25) -> int:
    """Distinct diet clusters separated by an empty gap — a crude species count."""
    d = np.sort(diet)
    return 1 + int((np.diff(d) > gap).sum())
