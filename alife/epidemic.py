"""R84 — Epidemics on networks: why scale-free topology has no epidemic threshold.

Builds on R83's networks. Run an SIR contagion (Susceptible→Infected→Recovered) over a graph: an
infected node infects each susceptible neighbour per step with probability beta, and recovers with
probability gamma. On a homogeneous random graph there is a finite EPIDEMIC THRESHOLD — below a
critical beta the outbreak fizzles. But on a SCALE-FREE network the threshold collapses toward
zero (Pastor-Satorras & Vespignani 2001): the hubs act as super-spreaders, so even a tiny
infectiousness can ignite a system-wide epidemic. The flip side of R83's Achilles heel becomes a
public-health lever — TARGETED immunisation of the hubs halts an epidemic with a handful of
vaccinations, where random vaccination barely moves it.

Reuses alife.network for BA / ER graphs. Vectorized SIR over the edge list; pure numpy/CPU.
"""

from __future__ import annotations

import numpy as np

from alife.network import ba_graph, er_graph, degrees  # noqa: F401  (re-exported for convenience)


def sir(edges, n, beta, gamma=1.0, seed=0, n_seed=1, immune=None):
    """One SIR outbreak. State 0=S,1=I,2=R; `immune` nodes start removed (vaccinated).
    Returns (final_state, ever_infected boolean array)."""
    rng = np.random.default_rng(seed)
    state = np.zeros(n, dtype=np.int8)
    if immune is not None and len(immune):
        state[np.asarray(list(immune))] = 2
    sus = np.flatnonzero(state == 0)
    seeds = rng.choice(sus, min(n_seed, len(sus)), replace=False)
    state[seeds] = 1
    i, j = edges[:, 0], edges[:, 1]
    ever = state == 1
    while np.any(state == 1):
        inf = (state == 1).astype(np.float64)
        exposure = np.zeros(n)
        np.add.at(exposure, j, inf[i]); np.add.at(exposure, i, inf[j])
        p_inf = 1.0 - (1.0 - beta) ** exposure
        newly = (state == 0) & (rng.random(n) < p_inf)
        recover = (state == 1) & (rng.random(n) < gamma)
        state[newly] = 1
        state[recover] = 2
        ever |= newly
    return state, ever


def sir_timeseries(edges, n, beta, gamma=1.0, seed=0, n_seed=5):
    """S/I/R counts over time for a single outbreak (the classic epidemic curve)."""
    rng = np.random.default_rng(seed)
    state = np.zeros(n, dtype=np.int8)
    state[rng.choice(n, n_seed, replace=False)] = 1
    i, j = edges[:, 0], edges[:, 1]
    S, I, R = [int((state == 0).sum())], [int((state == 1).sum())], [int((state == 2).sum())]
    while np.any(state == 1):
        inf = (state == 1).astype(np.float64)
        exposure = np.zeros(n)
        np.add.at(exposure, j, inf[i]); np.add.at(exposure, i, inf[j])
        newly = (state == 0) & (rng.random(n) < 1.0 - (1.0 - beta) ** exposure)
        recover = (state == 1) & (rng.random(n) < gamma)
        state[newly] = 1; state[recover] = 2
        S.append(int((state == 0).sum())); I.append(int((state == 1).sum())); R.append(int((state == 2).sum()))
    return np.array(S), np.array(I), np.array(R)


def epidemic_size(edges, n, beta, gamma=1.0, trials=8, seed=0, immune=None):
    """Mean fraction of nodes ever infected over trials (random seed node each time)."""
    rng = np.random.default_rng(seed)
    sizes = []
    for _ in range(trials):
        _, ever = sir(edges, n, beta, gamma, seed=int(rng.integers(1 << 30)), immune=immune)
        sizes.append(ever.mean())
    return float(np.mean(sizes))


def threshold_curve(edges, n, betas, gamma=1.0, trials=8, seed=0):
    return np.array([epidemic_size(edges, n, b, gamma, trials, seed) for b in betas])


def infection_by_degree(edges, n, beta, gamma=1.0, trials=20, seed=0, nbins=8):
    """P(ever infected) as a function of node degree — hubs are super-spreaders/super-receivers."""
    rng = np.random.default_rng(seed)
    deg = degrees(edges, n)
    hit = np.zeros(n)
    for _ in range(trials):
        _, ever = sir(edges, n, beta, gamma, seed=int(rng.integers(1 << 30)))
        hit += ever
    hit /= trials
    edges_d = np.unique(np.quantile(deg, np.linspace(0, 1, nbins + 1)).astype(int))
    centers, probs = [], []
    for a, b in zip(edges_d[:-1], edges_d[1:]):
        m = (deg >= a) & (deg < b) if b > a else (deg == a)
        if m.any():
            centers.append(deg[m].mean()); probs.append(hit[m].mean())
    return np.array(centers), np.array(probs)


def immunize(edges, n, beta, frac, mode="random", gamma=1.0, trials=8, seed=0):
    """Epidemic size when a fraction of nodes are vaccinated (random vs targeted-highest-degree)."""
    rng = np.random.default_rng(seed)
    order = np.argsort(degrees(edges, n))[::-1] if mode == "targeted" else rng.permutation(n)
    immune = set(order[:int(frac * n)].tolist())
    return epidemic_size(edges, n, beta, gamma, trials, seed=seed + 1, immune=immune)
