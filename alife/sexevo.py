"""R37 — the evolution of sex: Muller's ratchet.

Why is sex worth its two-fold cost? One classic answer: without recombination, a
finite asexual population cannot stop deleterious mutations from piling up. The
least-loaded class of individuals is, now and then, lost to chance — and since
nothing creates a *cleaner* genome than the cleanest parent, asexual lineages can
only ratchet downward. Sex breaks the ratchet: recombination reassembles a
low-mutation genome from two more-loaded parents, regenerating the clean class.

This is Muller's ratchet (Muller 1964; Felsenstein 1974), the cleanest model of
the advantage of recombination. Genomes are vectors of loci that are either wild
or carry a deleterious mutation; fitness is (1-s)^(#mutations); each generation
adds new mutations and never removes them. Asexual mean load climbs without
bound; sexual load settles at mutation-selection balance.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SexEvoConfig:
    pop: int = 150
    loci: int = 1000            # many loci so mutations never saturate the genome
    mut_rate: float = 0.30      # expected new deleterious mutations / genome / generation
    sel: float = 0.03           # fitness cost per deleterious mutation (balance ~ mut_rate/sel)
    generations: int = 800


def _fitness(load: np.ndarray, cfg: SexEvoConfig) -> np.ndarray:
    return (1.0 - cfg.sel) ** load


def _select_parents(genomes: np.ndarray, cfg: SexEvoConfig, rng, n: int) -> np.ndarray:
    w = _fitness(genomes.sum(axis=1), cfg)
    p = w / w.sum()
    return rng.choice(genomes.shape[0], size=n, p=p)


def _mutate(genomes: np.ndarray, cfg: SexEvoConfig, rng) -> np.ndarray:
    """Add Poisson(mut_rate) new deleterious mutations per genome at wild loci."""
    g = genomes.copy()
    n_new = rng.poisson(cfg.mut_rate, g.shape[0])
    for i in range(g.shape[0]):
        if n_new[i]:
            wild = np.where(g[i] == 0)[0]
            if wild.size:
                hit = rng.choice(wild, size=min(n_new[i], wild.size), replace=False)
                g[i, hit] = 1
    return g


def evolve(cfg: SexEvoConfig, sexual: bool, seed: int = 0):
    rng = np.random.default_rng(seed)
    genomes = np.zeros((cfg.pop, cfg.loci), dtype=np.int8)   # start mutation-free
    mean_load = []
    min_load = []
    for _ in range(cfg.generations):
        load = genomes.sum(axis=1)
        mean_load.append(float(load.mean()))
        min_load.append(int(load.min()))
        if sexual:
            pa = _select_parents(genomes, cfg, rng, cfg.pop)
            pb = _select_parents(genomes, cfg, rng, cfg.pop)
            mask = rng.random((cfg.pop, cfg.loci)) < 0.5    # per-locus inheritance
            kids = np.where(mask, genomes[pa], genomes[pb])
        else:
            pa = _select_parents(genomes, cfg, rng, cfg.pop)
            kids = genomes[pa].copy()
        genomes = _mutate(kids, cfg, rng)
    load = genomes.sum(axis=1)
    mean_load.append(float(load.mean())); min_load.append(int(load.min()))
    return {"mean_load": np.array(mean_load), "min_load": np.array(min_load),
            "mean_fitness": (1 - cfg.sel) ** np.array(mean_load)}
