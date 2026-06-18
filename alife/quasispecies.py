"""R44 — the error threshold: how much mutation can heredity survive? (Eigen).

A replicator carries information only if copying is accurate enough. Eigen's
quasispecies theory (1971) predicts a sharp limit: a master sequence with a
fitness advantage sigma over its mutants is maintained only while the per-site
mutation rate stays below a critical value mu_c ~ ln(sigma)/L (L = genome length).
Cross it and the population suffers an "error catastrophe" — the master sequence
melts away and the population delocalises into a random mutant cloud, losing the
information selection had built. It is why RNA viruses sit just under their error
threshold, and a constraint on the origin of life.

A finite population of binary genomes (master = all-ones). Each generation,
genomes reproduce in proportion to fitness (sigma for the master, 1 otherwise)
and each site mutates with probability mu. Below mu_c the master frequency stays
high; above it, it collapses to the random-sequence baseline.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class QuasispeciesConfig:
    pop: int = 3000
    loci: int = 20
    sigma: float = 6.0          # fitness advantage of the master sequence
    generations: int = 300

    @property
    def mu_c(self) -> float:
        return np.log(self.sigma) / self.loci      # Eigen's error threshold


def evolve(cfg: QuasispeciesConfig, mu: float, seed: int = 0):
    rng = np.random.default_rng(seed)
    # start everyone on the master sequence (all ones)
    genomes = np.ones((cfg.pop, cfg.loci), dtype=np.int8)
    master_freq = []
    for _ in range(cfg.generations):
        is_master = genomes.all(axis=1)
        master_freq.append(float(is_master.mean()))
        fit = np.where(is_master, cfg.sigma, 1.0)
        parents = rng.choice(cfg.pop, cfg.pop, p=fit / fit.sum())
        kids = genomes[parents].copy()
        flips = rng.random((cfg.pop, cfg.loci)) < mu
        kids[flips] ^= 1                                # binary mutation
        genomes = kids
    is_master = genomes.all(axis=1)
    master_freq.append(float(is_master.mean()))
    return {"master_freq": np.array(master_freq),
            "final_master": float(is_master.mean()),
            "mean_hamming": float((cfg.loci - genomes.sum(axis=1)).mean())}


def mu_sweep(cfg: QuasispeciesConfig, mus, seed: int = 0) -> np.ndarray:
    """Steady-state master-sequence frequency across mutation rates."""
    out = []
    for mu in mus:
        r = evolve(cfg, float(mu), seed=seed)
        out.append(float(np.mean(r["master_freq"][-50:])))
    return np.array(out)
