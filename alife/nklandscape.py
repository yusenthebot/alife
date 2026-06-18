"""R76 — NK fitness landscapes (Kauffman): the geometry of evolution and the complexity catastrophe.

Every earlier evolution round was about the DYNAMICS of search; this one is about the SHAPE of the
space being searched. Kauffman's NK model tunes ruggedness with one knob. A genome is N binary
loci; each locus's fitness contribution depends on its own value AND on K others (epistasis).
With K=0 the loci are independent — a single smooth Fujiyama peak that any hill-climb reaches.
As K rises the contributions conflict, the landscape shatters into exponentially many local
optima, and adaptive walks get trapped on ever-poorer peaks — Kauffman's COMPLEXITY CATASTROPHE:
at maximal epistasis the optima you can reach are barely better than random (fitness → 0.5).

A foundational result on WHY complex, highly-interdependent systems are hard to evolve. Pure
numpy/CPU; small N so the global optimum is brute-forceable for comparison.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class NKLandscape:
    N: int
    K: int
    deps: np.ndarray          # (N, K+1) dependency loci per site (site i first)
    contrib: np.ndarray       # (N, 2^(K+1)) random fitness contributions
    pow2: np.ndarray          # (K+1,) bit weights


def make_landscape(N: int, K: int, seed: int = 0) -> NKLandscape:
    rng = np.random.default_rng(seed)
    deps = np.empty((N, K + 1), dtype=np.int64)
    for i in range(N):
        others = [j for j in range(N) if j != i]
        chosen = rng.choice(others, K, replace=False) if K > 0 else np.array([], dtype=int)
        deps[i] = np.concatenate([[i], chosen]).astype(np.int64)
    contrib = rng.random((N, 1 << (K + 1)))
    pow2 = (1 << np.arange(K + 1)).astype(np.int64)
    return NKLandscape(N, K, deps, contrib, pow2)


def fitness_batch(L: NKLandscape, genomes: np.ndarray) -> np.ndarray:
    """Mean per-locus contribution for a batch of genomes (G, N) of 0/1 -> (G,) fitness."""
    g = genomes.astype(np.int64)
    total = np.zeros(len(g))
    for i in range(L.N):
        idx = g[:, L.deps[i]] @ L.pow2                # (K+1)-bit pattern -> table index
        total += L.contrib[i, idx]
    return total / L.N


def fitness(L: NKLandscape, genome: np.ndarray) -> float:
    return float(fitness_batch(L, genome[None, :])[0])


def adaptive_walk(L: NKLandscape, start: np.ndarray):
    """Steepest-ascent single-flip hill-climb to a local optimum. Returns (optimum, fitness trace)."""
    g = start.copy()
    f = fitness(L, g)
    trace = [f]
    while True:
        nbrs = np.tile(g, (L.N, 1))
        nbrs[np.arange(L.N), np.arange(L.N)] ^= 1     # all single-bit flips
        fn = fitness_batch(L, nbrs)
        j = int(fn.argmax())
        if fn[j] <= f:
            break                                     # local optimum: no single flip improves
        g = nbrs[j]; f = float(fn[j]); trace.append(f)
    return g, np.array(trace)


def all_genomes(N: int) -> np.ndarray:
    idx = np.arange(1 << N, dtype=np.int64)
    return ((idx[:, None] >> np.arange(N)) & 1).astype(np.int8)


def global_optimum(L: NKLandscape) -> float:
    return float(fitness_batch(L, all_genomes(L.N)).max())


def count_local_optima(L: NKLandscape) -> int:
    """Exact count of local optima (genomes no single flip can improve). Brute force, N<=~18."""
    G = all_genomes(L.N)
    f = fitness_batch(L, G)
    is_opt = np.ones(len(G), bool)
    for i in range(L.N):
        flipped = G.copy(); flipped[:, i] ^= 1
        fi = fitness_batch(L, flipped)
        is_opt &= f >= fi                             # no improving flip at locus i
    return int(is_opt.sum())


def survey(N: int, Ks, walks: int = 120, instances: int = 5, seed: int = 0):
    """For each K, averaged over `instances` random landscapes: mean local-optimum fitness reached
    by adaptive walks, fraction reaching the GLOBAL optimum, mean walk length, the global optimum,
    and the exact number of local optima."""
    rng = np.random.default_rng(seed)
    rows = []
    for K in Ks:
        mo, gl, fg, wl, no = [], [], [], [], []
        for _ in range(instances):
            L = make_landscape(N, K, seed=int(rng.integers(1 << 30)))
            gopt = global_optimum(L)
            reached, lengths, hit = [], [], 0
            for _ in range(walks):
                s = rng.integers(0, 2, N).astype(np.int8)
                _, tr = adaptive_walk(L, s)
                reached.append(tr[-1]); lengths.append(len(tr) - 1)
                if abs(tr[-1] - gopt) < 1e-9:
                    hit += 1
            mo.append(np.mean(reached)); gl.append(gopt); fg.append(hit / walks)
            wl.append(np.mean(lengths)); no.append(count_local_optima(L))
        rows.append({"K": K, "mean_opt": float(np.mean(mo)), "global": float(np.mean(gl)),
                     "frac_global": float(np.mean(fg)), "walk_len": float(np.mean(wl)),
                     "n_optima": float(np.mean(no))})
    return rows
