"""R83 — Network science: how a growing network becomes scale-free, and its Achilles heel.

A different substrate: not space or agents but the TOPOLOGY of who-connects-to-whom — the
skeleton of metabolic, neural, ecological and social systems. Barabasi & Albert (1999) showed
two ingredients suffice for the broad, hub-dominated connectivity seen in real networks: GROWTH
(nodes are added over time) and PREFERENTIAL ATTACHMENT (a new node links to existing nodes with
probability proportional to their degree — the rich get richer). The result is a SCALE-FREE
degree distribution P(k) ~ k^-3 with a few enormous hubs, utterly unlike the bell-shaped Poisson
of an Erdos-Renyi random graph. And it has an Achilles heel (Albert-Jeong-Barabasi): a scale-free
net is extraordinarily ROBUST to random failures yet FRAGILE to a targeted attack on its hubs,
while a random graph degrades the same way under both. Emergent architecture from a local rule.

Pure numpy + scipy (connected components). Preferential attachment via a stub list.
"""

from __future__ import annotations

import numpy as np


def ba_graph(n: int, m: int = 2, seed: int = 0):
    """Barabasi-Albert: grow to n nodes, each new node attaching to m existing nodes chosen with
    probability proportional to degree. Returns the (E,2) edge array."""
    rng = np.random.default_rng(seed)
    edges = []
    stubs = []                                          # each node id appears once per incident edge
    for i in range(m):                                  # seed: a small clique of m+1 nodes
        for j in range(i):
            edges.append((i, j)); stubs += [i, j]
    for new in range(m, n):
        chosen = set()
        while len(chosen) < min(m, new):
            chosen.add(int(stubs[rng.integers(len(stubs))]))   # preferential = uniform over stubs
        for t in chosen:
            edges.append((new, t)); stubs += [new, t]
    return np.array(edges)


def er_graph(n: int, n_edges: int, seed: int = 0):
    """Erdos-Renyi random graph with n nodes and n_edges distinct undirected edges."""
    rng = np.random.default_rng(seed)
    seen = set()
    edges = []
    while len(edges) < n_edges:
        a, b = int(rng.integers(n)), int(rng.integers(n))
        if a != b and (a, b) not in seen and (b, a) not in seen:
            seen.add((a, b)); edges.append((a, b))
    return np.array(edges)


def degrees(edges, n):
    d = np.zeros(n, dtype=np.int64)
    np.add.at(d, edges[:, 0], 1); np.add.at(d, edges[:, 1], 1)
    return d


def degree_distribution(edges, n):
    d = degrees(edges, n)
    k = np.arange(d.max() + 1)
    pk = np.bincount(d, minlength=len(k)) / n
    return k, pk


def ccdf(edges, n):
    """Complementary cumulative degree distribution P(K >= k) — the clean way to see a power law."""
    d = degrees(edges, n)
    ks = np.arange(1, d.max() + 1)
    return ks, np.array([(d >= k).mean() for k in ks])


def powerlaw_exponent(edges, n, kmin=3):
    """Log-log slope of the CCDF tail. BA scale-free -> ~ -2 (= 1 - gamma, gamma~3); a random
    graph's CCDF falls off far more steeply (no heavy tail)."""
    ks, cc = ccdf(edges, n)
    ok = (ks >= kmin) & (cc > 1e-3)
    if ok.sum() < 3:
        return float("nan")
    return float(np.polyfit(np.log(ks[ok]), np.log(cc[ok]), 1)[0])


def _giant_fraction(edges, n, alive):
    """Largest connected component size (as a fraction of n) among `alive` nodes."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    keep = np.zeros(n, bool); keep[list(alive)] = True
    e = edges[keep[edges[:, 0]] & keep[edges[:, 1]]]
    if len(e) == 0:
        return 1.0 / n if alive else 0.0
    A = coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
    ncomp, lab = connected_components(A + A.T, directed=False)
    sizes = np.bincount(lab[list(alive)])
    return float(sizes.max() / n)


def attack_curve(edges, n, fractions, mode="random", seed=0):
    """Giant-component fraction as nodes are removed `random`ly or by `targeted` highest-degree."""
    rng = np.random.default_rng(seed)
    if mode == "targeted":
        order = np.argsort(degrees(edges, n))[::-1]      # remove hubs first
    else:
        order = rng.permutation(n)
    out = []
    for f in fractions:
        removed = set(order[:int(f * n)].tolist())
        alive = [i for i in range(n) if i not in removed]
        out.append(_giant_fraction(edges, n, alive))
    return np.array(out)


def spring_layout(edges, n, iters=200, seed=0):
    """Minimal Fruchterman-Reingold layout for drawing a small network."""
    rng = np.random.default_rng(seed)
    pos = rng.standard_normal((n, 2))
    k = 1.0 / np.sqrt(n)
    for it in range(iters):
        disp = np.zeros((n, 2))
        diff = pos[:, None, :] - pos[None, :, :]
        dist = np.hypot(diff[..., 0], diff[..., 1]) + 1e-6
        rep = (k * k / dist)[..., None] * (diff / dist[..., None])   # repulsion
        disp += rep.sum(1)
        d = pos[edges[:, 0]] - pos[edges[:, 1]]                       # attraction along edges
        dd = np.hypot(d[:, 0], d[:, 1])[:, None] + 1e-6
        att = (dd / k) * (d / dd)
        np.add.at(disp, edges[:, 0], -att); np.add.at(disp, edges[:, 1], att)
        ln = np.hypot(disp[:, 0], disp[:, 1])[:, None] + 1e-9
        pos += (disp / ln) * np.minimum(ln, 0.1 * (1 - it / iters) + 0.01)
    return pos
