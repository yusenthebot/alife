"""R53 — the tree of life in the digital soup: lineages, clades, coalescence.

Instruments the R51 digital-evolution soup with ancestry. Each founding replicator
carries a neutral lineage tag that its descendants inherit; each distinct genome is
a genotype/clade. Watching the soup we see the universal signatures of an evolving
population: clades rise and fall (a Muller-style turnover), new genotypes keep
appearing (ongoing evolutionary activity), and — because reproduction + finite
space = genetic drift plus selection — the many founding lineages collapse to ONE:
every survivor eventually traces back to a single common ancestor (coalescence).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from alife.digavida import CPU, MAX_CYCLES, padded_ancestor, step


@dataclass(frozen=True)
class PhyloConfig:
    n_slots: int = 200
    n_found: int = 24           # distinct founding lineages (neutral tags)
    seed_len: int = 16
    sweeps: int = 10000
    mut_point: float = 0.02
    mut_indel: float = 0.012
    record_every: int = 25


def _indel(off, rng, p):
    from alife.digavida import MIN_LEN, MAX_LEN, N_OPS
    if rng.random() < p and len(off) > MIN_LEN:
        off = np.delete(off, int(rng.integers(0, len(off))))
    if rng.random() < p and len(off) < MAX_LEN:
        off = np.insert(off, int(rng.integers(0, len(off) + 1)), int(rng.integers(0, N_OPS)))
    return off


def run(cfg: PhyloConfig, seed: int = 0):
    rng = np.random.default_rng(seed)
    genomes = [None] * cfg.n_slots
    cpus = [None] * cfg.n_slots
    found = [-1] * cfg.n_slots          # founding-lineage tag
    for i in range(cfg.n_found):
        genomes[i] = padded_ancestor(cfg.seed_len); cpus[i] = CPU(); found[i] = i

    seen_genotypes = set()
    hist = {"t": [], "n_lineages": [], "n_genotypes": [], "cum_genotypes": [], "top_lineage": []}
    lineage_series = {k: [] for k in range(cfg.n_found)}

    def place(child, tag):
        e = [i for i in range(cfg.n_slots) if genomes[i] is None]
        s = e[0] if e else int(rng.integers(0, cfg.n_slots))
        genomes[s] = child; cpus[s] = CPU(); found[s] = tag

    for sweep in range(cfg.sweeps):
        for i in range(cfg.n_slots):
            if genomes[i] is None:
                continue
            child = step(genomes[i], cpus[i], rng, cfg.mut_point)
            if child is not None:
                child = _indel(child, rng, cfg.mut_indel)
                from alife.digavida import is_replicator
                if is_replicator(child) or rng.random() < 0.4:
                    place(child, found[i])
                cpus[i].cycles = 0
            elif cpus[i].cycles > MAX_CYCLES:
                genomes[i] = None; cpus[i] = None; found[i] = -1
        if sweep % cfg.record_every == 0:
            alive = [i for i in range(cfg.n_slots) if genomes[i] is not None]
            if not alive:
                break
            tags = [found[i] for i in alive]
            gtypes = {genomes[i].tobytes() for i in alive}
            seen_genotypes |= gtypes
            counts = {k: tags.count(k) for k in set(tags)}
            hist["t"].append(sweep)
            hist["n_lineages"].append(len(set(tags)))
            hist["n_genotypes"].append(len(gtypes))
            hist["cum_genotypes"].append(len(seen_genotypes))
            hist["top_lineage"].append(max(counts.values()) / len(alive))
            for k in range(cfg.n_found):
                lineage_series[k].append(counts.get(k, 0))
    out = {k: np.array(v, dtype=float) for k, v in hist.items()}
    out["lineage_series"] = {k: np.array(v) for k, v in lineage_series.items()}
    return out
