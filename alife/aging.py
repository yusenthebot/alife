"""Evolution of aging — why organisms senesce.

Each genome encodes an intrinsic survival probability at every age. The force of
selection on a gene acting at age a is proportional to the chance of *reaching*
age a — which decays with age because of extrinsic mortality. So late-acting
deleterious mutations are barely selected against and accumulate (Medawar), and
intrinsic mortality rises with age: senescence. Williams' prediction follows
directly — populations with HIGHER extrinsic mortality evolve FASTER aging,
because the force of selection decays faster.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AgingConfig:
    max_age: int = 25
    pop: int = 800
    generations: int = 600
    mut_bias: float = 0.004     # deleterious pressure: mutations tend to lower survival
    mut_sigma: float = 0.03
    elite_frac: float = 0.4
    fertility: float = 1.0


def lifetime_reproduction(s: np.ndarray, m: float, fertility: float) -> np.ndarray:
    """Expected lifetime offspring per genome. s:(pop, A) intrinsic survival.
    P(reach age a) = prod_{i<a} s[i]*(1-m); LRS = sum_a P(reach a)*fertility."""
    step_survival = s * (1.0 - m)
    reach = np.cumprod(np.concatenate([np.ones((s.shape[0], 1)), step_survival[:, :-1]], axis=1), axis=1)
    return (reach * fertility).sum(1)


def evolve(cfg: AgingConfig, extrinsic_mortality: float, seed: int = 0):
    """Returns the evolved mean intrinsic survival by age (and its history)."""
    rng = np.random.default_rng(seed)
    s = np.full((cfg.pop, cfg.max_age), 0.95)
    n_elite = max(2, int(cfg.pop * cfg.elite_frac))
    for _ in range(cfg.generations):
        lrs = lifetime_reproduction(s, extrinsic_mortality, cfg.fertility)
        elite = np.argsort(lrs)[::-1][:n_elite]
        idx = elite[rng.integers(0, n_elite, cfg.pop)]
        noise = rng.normal(-cfg.mut_bias, cfg.mut_sigma, s.shape)   # deleterious-biased mutation
        s = np.clip(s[idx] + noise, 0.0, 1.0)
    return s.mean(0)
