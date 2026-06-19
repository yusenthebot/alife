"""R98 — Axelrod's culture model: why contact doesn't always erase differences.

Robert Axelrod asked a puzzle: if people grow more alike each time they interact, why doesn't the
whole world converge to one culture? His 1997 model has two ingredients — HOMOPHILY (you interact
more with those already similar to you) and SOCIAL INFLUENCE (interaction makes you more similar).
Each agent holds F cultural features, each taking one of q traits. A random agent meets a neighbour
with probability equal to their cultural overlap, then copies one feature where they differ. The
result is self-organizing cultural DOMAINS — and a phase transition in the trait count q: with few
traits agents almost always share something, interact, and collapse to a single MONOCULTURE; with
many traits neighbours often share nothing, can never interact, and the map freezes into a fragmented
MULTICULTURE. Diversity survives precisely because similarity is required to influence.

Connected-component domains via scipy sparse graph; CPU.
"""

from __future__ import annotations

import numpy as np
from scipy.sparse.csgraph import connected_components
from scipy.sparse import coo_matrix


def init_culture(L, F, q, seed=0):
    return np.random.default_rng(seed).integers(0, q, size=(L, L, F))


def _neighbors(L):
    """Return arrays (a, b) of flat indices of 4-connected neighbour pairs."""
    idx = np.arange(L * L).reshape(L, L)
    a = np.concatenate([idx[:, :-1].ravel(), idx[:-1, :].ravel()])
    b = np.concatenate([idx[:, 1:].ravel(), idx[1:, :].ravel()])
    return a, b


def domains(culture):
    """Connected regions of identical culture. Returns (n_regions, largest_fraction)."""
    L = culture.shape[0]
    flat = culture.reshape(L * L, -1)
    a, b = _neighbors(L)
    same = np.all(flat[a] == flat[b], axis=1)
    a, b = a[same], b[same]
    n = L * L
    g = coo_matrix((np.ones(len(a)), (a, b)), shape=(n, n))
    n_comp, labels = connected_components(g, directed=False)
    sizes = np.bincount(labels)
    return int(n_comp), float(sizes.max() / n)


def run(L=20, F=10, q=10, seed=0, max_sweeps=8000):
    """Evolve until frozen (no active neighbour bond) or max_sweeps. Returns final state + metrics."""
    rng = np.random.default_rng(seed)
    cult = init_culture(L, F, q, seed)
    flat = cult.reshape(L * L, F)
    a, b = _neighbors(L)
    micro = L * L
    for sweep in range(max_sweeps):
        # one sweep = ~L*L random interactions
        sites = rng.integers(0, L * L, micro)
        for i in sites:
            r, c = divmod(int(i), L)
            nb = []
            if r > 0: nb.append((r - 1) * L + c)
            if r < L - 1: nb.append((r + 1) * L + c)
            if c > 0: nb.append(r * L + c - 1)
            if c < L - 1: nb.append(r * L + c + 1)
            j = nb[rng.integers(len(nb))]
            diff = flat[i] != flat[j]
            nd = int(diff.sum())
            if nd == 0 or nd == F:
                continue                                    # identical or wholly different: no change
            overlap = 1.0 - nd / F
            if rng.random() < overlap:
                feats = np.flatnonzero(diff)
                f = feats[rng.integers(len(feats))]
                flat[i, f] = flat[j, f]
        if sweep % 20 == 0:
            same = np.all(flat[a] == flat[b], axis=1)
            nd_all = np.sum(flat[a] != flat[b], axis=1)
            active = np.any((~same) & (nd_all < F))
            if not active:
                break
    n_reg, largest = domains(flat.reshape(L, L, F))
    return {"culture": flat.reshape(L, L, F), "n_regions": n_reg, "largest": largest, "sweeps": sweep + 1}


def sweep_traits(qs, L=18, F=10, seed=0, max_sweeps=8000):
    """Largest cultural-domain fraction vs trait count q (monoculture → fragmentation transition)."""
    rng = np.random.default_rng(seed)
    out = []
    for q in qs:
        out.append(run(L, F, int(q), seed=int(rng.integers(1 << 30)), max_sweeps=max_sweeps)["largest"])
    return np.asarray(qs, float), np.asarray(out)
