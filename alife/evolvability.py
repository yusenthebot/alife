"""Evolution of evolvability — the mutation rate itself evolves.

Each individual carries not just a trait `x` (under stabilizing selection toward
an optimum) but its own heritable mutation rate `sigma`, which mutates
log-normally when inherited (self-adaptation, as in evolution strategies). The
prediction, and the result: in a STATIC environment selection drives sigma DOWN
(most mutations are deleterious once you're near the optimum), while under a
MOVING optimum it stays HIGH (you must keep mutating to track a shifting target).
Evolvability is itself an evolved property.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class EvolvabilityConfig:
    pop: int = 400
    generations: int = 400
    sel_w: float = 0.35         # selection width (sharp => mutation load matters)
    tau: float = 0.10           # log-normal mutation strength on sigma itself
    sigma_min: float = 0.002
    sigma_max: float = 1.5
    elite_frac: float = 0.3
    drift: float = 0.18         # optimum movement per generation (fast => tracking needs mutation)


def evolve(cfg: EvolvabilityConfig, moving: bool, seed: int = 0):
    """(μ,λ) evolution-strategy self-adaptation: each generation is entirely new
    offspring (comma selection, no parent carryover), so sigma is selected purely
    through the fitness of the offspring it produced."""
    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, 0.5, cfg.pop)
    sigma = np.full(cfg.pop, 0.4)
    n_parents = max(1, int(cfg.pop * cfg.elite_frac))
    opt = 0.0
    hist_sigma, hist_fit = [], []

    for g in range(cfg.generations):
        fit = np.exp(-((x - opt) ** 2) / (2 * cfg.sel_w ** 2))
        hist_sigma.append(float(np.median(sigma)))
        hist_fit.append(float(fit.mean()))

        parents = np.argsort(fit)[::-1][:n_parents]      # top μ
        pi = parents[rng.integers(0, n_parents, cfg.pop)]  # λ offspring from them
        sigma = np.clip(sigma[pi] * np.exp(rng.normal(0, cfg.tau, cfg.pop)), cfg.sigma_min, cfg.sigma_max)
        x = x[pi] + rng.normal(0, 1, cfg.pop) * sigma     # mutate x with the just-mutated sigma
        if moving:
            opt += cfg.drift

    hist_sigma.append(float(np.median(sigma)))
    hist_fit.append(float(np.exp(-((x - opt) ** 2) / (2 * cfg.sel_w ** 2)).mean()))
    return np.array(hist_sigma), np.array(hist_fit)
