"""R87 — Watts-Strogatz small worlds: six degrees of separation from a few shortcuts.

The companion to R83's scale-free networks — the other pillar of network science. Real social
networks have two properties that seem to pull against each other: they are highly CLUSTERED (your
friends know each other, like a regular lattice) yet have SHORT path lengths (anyone is ~6 hops
away, like a random graph). Watts & Strogatz (1998) showed both hold at once: take a ring lattice
(high clustering, long paths) and randomly rewire a tiny fraction p of its edges. A handful of
long-range "shortcuts" collapses the average path length to nearly that of a random graph while the
clustering barely changes — the small-world regime. The decoupling has a real dynamical payoff:
information, epidemics and synchronization spread far faster once the shortcuts appear.

Pure numpy + adjacency sets; BFS for path lengths. CPU-fast for n~600.
"""

from __future__ import annotations

import numpy as np


def ring_lattice(n, k):
    """Ring of n nodes, each joined to its k nearest neighbours (k/2 on each side). k even."""
    adj = [set() for _ in range(n)]
    for i in range(n):
        for d in range(1, k // 2 + 1):
            j = (i + d) % n
            adj[i].add(j)
            adj[j].add(i)
    return adj


def watts_strogatz(n, k, p, seed=0):
    """Rewire each lattice edge with probability p to a random new endpoint (no self/duplicate)."""
    rng = np.random.default_rng(seed)
    adj = ring_lattice(n, k)
    for i in range(n):
        for d in range(1, k // 2 + 1):              # consider each undirected edge once (forward)
            j = (i + d) % n
            if rng.random() < p:
                m = int(rng.integers(n))
                tries = 0
                while (m == i or m in adj[i]) and tries < 20:
                    m = int(rng.integers(n))
                    tries += 1
                if m == i or m in adj[i]:
                    continue                         # give up this rewire (keep original edge)
                adj[i].discard(j); adj[j].discard(i)
                adj[i].add(m); adj[m].add(i)
    return adj


def clustering_coefficient(adj):
    """Average local clustering: fraction of a node's neighbour-pairs that are themselves linked."""
    n = len(adj)
    cs = []
    for i in range(n):
        nb = adj[i]
        deg = len(nb)
        if deg < 2:
            continue
        links = sum(1 for a in nb for b in nb if a < b and b in adj[a])
        cs.append(links / (deg * (deg - 1) / 2))
    return float(np.mean(cs)) if cs else 0.0


def _bfs_dist(adj, src):
    n = len(adj)
    dist = np.full(n, -1)
    dist[src] = 0
    frontier = [src]
    while frontier:
        nxt = []
        for u in frontier:
            for v in adj[u]:
                if dist[v] < 0:
                    dist[v] = dist[u] + 1
                    nxt.append(v)
        frontier = nxt
    return dist


def average_path_length(adj, sources=None, seed=0):
    """Mean shortest-path length over reachable pairs (optionally sampling `sources` seeds)."""
    n = len(adj)
    if sources is None:
        srcs = range(n)
    else:
        srcs = np.random.default_rng(seed).choice(n, min(sources, n), replace=False)
    tot, cnt = 0.0, 0
    for s in srcs:
        d = _bfs_dist(adj, int(s))
        reach = d[(d > 0)]
        tot += reach.sum(); cnt += reach.size
    return tot / cnt if cnt else float("inf")


def spread_time(adj, seeds=8, seed=0):
    """Rounds for a one-hop-per-step signal to reach the whole reachable component (mean eccentricity
    over random seed nodes) — the dynamical payoff of shortcuts."""
    n = len(adj)
    rng = np.random.default_rng(seed)
    srcs = rng.choice(n, min(seeds, n), replace=False)
    return float(np.mean([_bfs_dist(adj, int(s)).max() for s in srcs]))


def ws_sweep(n=600, k=6, ps=None, seed=0, reps=4, path_sources=120):
    """Classic Watts-Strogatz curves: C(p)/C(0) and L(p)/L(0) vs rewiring probability p."""
    ps = np.asarray(ps) if ps is not None else np.logspace(-4, 0, 14)
    base = watts_strogatz(n, k, 0.0, seed)
    C0, L0 = clustering_coefficient(base), average_path_length(base, sources=path_sources, seed=seed)
    rng = np.random.default_rng(seed)
    C, L = [], []
    for p in ps:
        cc, ll = [], []
        for _ in range(reps):
            g = watts_strogatz(n, k, float(p), int(rng.integers(1 << 30)))
            cc.append(clustering_coefficient(g))
            ll.append(average_path_length(g, sources=path_sources, seed=int(rng.integers(1 << 30))))
        C.append(np.mean(cc) / C0)
        L.append(np.mean(ll) / L0)
    return ps, np.asarray(C), np.asarray(L)
