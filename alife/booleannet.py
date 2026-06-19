"""R94 — Kauffman random Boolean networks: order, chaos, and the edge between.

Stuart Kauffman's NK Boolean network is a toy genome: N genes, each switched on/off by a random
Boolean function of K other genes, all updated in lockstep. Run it and the network falls into a
cyclic ATTRACTOR — Kauffman's metaphor for a cell type (one genome, many stable expression patterns).
The striking result is a phase transition in CONNECTIVITY: for K=1 the network is ORDERED (a flipped
gene heals, attractors are short), for K>=3 it is CHAOTIC (a single flip avalanches across the
network), and K=2 sits exactly at the critical "edge of chaos". The cleanest diagnostic is the
Derrida curve: how the difference between two trajectories grows in one step. Its slope at the origin
is ~K/2 for unbiased rules, so it crosses 1 — neither shrinking nor growing — precisely at K=2.

Distinct from R76 (NK fitness *landscapes*, static): this is the NK network's *dynamics*. Pure numpy.
"""

from __future__ import annotations

import numpy as np


def make_network(n, k, seed=0, bias=0.5):
    """Random Boolean net: each node has k random inputs and a random 2^k-entry truth table."""
    rng = np.random.default_rng(seed)
    inputs = rng.integers(0, n, size=(n, k))
    rules = (rng.random((n, 1 << k)) < bias).astype(np.int8)   # truth table per node
    pow2 = (1 << np.arange(k)).astype(np.int64)
    return {"inputs": inputs, "rules": rules, "pow2": pow2, "n": n, "k": k}


def step(state, net):
    """Synchronous update: each node looks up its truth table by its inputs' current bits."""
    in_bits = state[net["inputs"]]                          # (n, k)
    idx = (in_bits * net["pow2"]).sum(axis=1)               # row index into each truth table
    return net["rules"][np.arange(net["n"]), idx]


def _hamming(a, b):
    return int(np.count_nonzero(a != b))


def derrida_point(net, d_frac, trials=40, seed=0):
    """Average normalized Hamming distance ONE step after starting a fraction d_frac apart."""
    rng = np.random.default_rng(seed)
    n = net["n"]
    out = []
    for _ in range(trials):
        s = (rng.random(n) < 0.5).astype(np.int8)
        t = s.copy()
        flip = rng.choice(n, max(1, int(d_frac * n)), replace=False)
        t[flip] ^= 1
        out.append(_hamming(step(s, net), step(t, net)) / n)
    return float(np.mean(out))


def derrida_curve(net, xs=None, trials=40, seed=0):
    """The Derrida map y(x): output distance vs input distance (averaged over random pairs)."""
    xs = np.asarray(xs) if xs is not None else np.linspace(0.01, 0.5, 12)
    ys = [derrida_point(net, float(x), trials, seed + i) for i, x in enumerate(xs)]
    return xs, np.asarray(ys)


def derrida_slope(net, trials=200, seed=0):
    """Sensitivity = slope of the Derrida map at small distance (<1 ordered, 1 critical, >1 chaotic)."""
    x = 1.0 / net["n"]                                       # a single flipped bit
    y = derrida_point(net, x, trials, seed)
    return y / x


def damage_spread(net, steps=40, seed=0):
    """Hamming distance over time between a trajectory and a one-bit-flipped copy (normalized)."""
    rng = np.random.default_rng(seed)
    n = net["n"]
    s = (rng.random(n) < 0.5).astype(np.int8)
    t = s.copy()
    t[rng.integers(n)] ^= 1
    dist = [_hamming(s, t) / n]
    for _ in range(steps):
        s, t = step(s, net), step(t, net)
        dist.append(_hamming(s, t) / n)
    return np.asarray(dist)


def attractor_length(net, state=None, max_steps=2000, seed=0):
    """Iterate to an attractor; return (cycle_length, transient_length)."""
    rng = np.random.default_rng(seed)
    s = state if state is not None else (rng.random(net["n"]) < 0.5).astype(np.int8)
    seen = {}
    hist = []
    for t in range(max_steps):
        key = s.tobytes()
        if key in seen:
            return t - seen[key], seen[key]                 # cycle length, transient
        seen[key] = t
        hist.append(s)
        s = step(s, net)
    return -1, max_steps                                     # didn't close (chaotic/long)


def count_attractors(net, n_init=60, max_steps=2000, seed=0):
    """Distinct attractors ('cell types') reached from random initial states."""
    rng = np.random.default_rng(seed)
    cycles = set()
    lengths = []
    for _ in range(n_init):
        s = (rng.random(net["n"]) < 0.5).astype(np.int8)
        clen, _ = attractor_length(net, s, max_steps, seed=int(rng.integers(1 << 30)))
        if clen <= 0:
            lengths.append(max_steps)
            continue
        # canonical signature: walk the cycle, take the min state bytes as id
        states = []
        for _ in range(clen):
            states.append(s.tobytes()); s = step(s, net)
        cycles.add(min(states))
        lengths.append(clen)
    return len(cycles), float(np.median(lengths))
