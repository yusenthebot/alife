"""A major transition — the evolution of multicellularity.

Each cell carries a heritable `stickiness` that determines how large a cluster it
forms. Clustering has a cost (interior cells get fewer resources, so per-cell
reproduction falls with size) but also a benefit when a SIZE-SELECTIVE predator is
present: it eats lone and small clusters, while large clusters are protected.
With the predator, stickiness evolves UP to an intermediate optimum — cells become
multicellular; without it, only the cost remains and cells stay unicellular. This
is the predation route to multicellularity (Boraas' Chlorella, Ratcliff's
snowflake yeast), an evolutionary major transition reproduced from scratch.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MulticellConfig:
    pop: int = 800
    generations: int = 300
    max_cluster: float = 12.0    # cluster size at stickiness = 1
    pred_threshold: float = 5.0  # clusters below this size are vulnerable
    pred_sharpness: float = 1.2
    cost: float = 0.55           # reproduction penalty for being big
    mut: float = 0.03
    elite_frac: float = 0.4


def cluster_size(stickiness: np.ndarray, cfg: MulticellConfig) -> np.ndarray:
    return 1.0 + (cfg.max_cluster - 1.0) * stickiness


def fitness(stickiness: np.ndarray, cfg: MulticellConfig, predation: bool) -> np.ndarray:
    size = cluster_size(stickiness, cfg)
    reproduction = 1.0 - cfg.cost * (size - 1.0) / (cfg.max_cluster - 1.0)
    if predation:
        survival = 1.0 / (1.0 + np.exp(-cfg.pred_sharpness * (size - cfg.pred_threshold)))
    else:
        survival = np.ones_like(size)
    return np.maximum(survival * reproduction, 1e-6)


def evolve(cfg: MulticellConfig, predation: bool, seed: int = 0):
    rng = np.random.default_rng(seed)
    s = rng.uniform(0, 0.15, cfg.pop)      # start nearly unicellular
    n_elite = max(2, int(cfg.pop * cfg.elite_frac))
    hist = []
    for _ in range(cfg.generations):
        hist.append(float(s.mean()))
        fit = fitness(s, cfg, predation)
        elite = np.argsort(fit)[::-1][:n_elite]
        idx = elite[rng.integers(0, n_elite, cfg.pop)]
        s = np.clip(s[idx] + rng.normal(0, cfg.mut, cfg.pop), 0, 1)
    hist.append(float(s.mean()))
    return np.array(hist), float(cluster_size(s, cfg).mean())
