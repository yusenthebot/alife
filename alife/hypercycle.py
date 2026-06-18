"""R63 — Hypercycles (Eigen-Schuster): cooperation among replicators, its parasite, and
the spatial rescue.

R44 showed a single replicator can hold only ~1/mutation-rate bits before the error
catastrophe. Eigen & Schuster's answer: couple several replicators in a catalytic CYCLE
— species 1 helps 2 helps 3 … helps n helps 1 — so the whole loop maintains far more
information than any member could alone. Three classic results:

  1. WELL-MIXED dynamics (replicator equation, simplex-preserving): a hypercycle of n>=5
     members settles into a permanent LIMIT CYCLE — all members coexist forever, taking
     turns dominating. Independent (uncoupled) replicators instead show competitive
     exclusion: only the fittest survives. Cooperation buys coexistence.
  2. The PARASITE (Maynard Smith's critique): a short-circuit species that takes catalysis
     from a member but gives nothing back invades the well-mixed hypercycle and collapses
     it — a fatal flaw for the well-mixed story.
  3. The SPATIAL hypercycle (Boerlijst-Hogeweg): on a 2D lattice the cyclic catalytic CA
     self-organises into rotating SPIRAL WAVES, and those waves hold a stable spatial
     coexistence of all members (no spatial competitive exclusion).

Honest negative: Boerlijst-Hogeweg's further claim — that the spirals also EXPEL the
parasite that kills the well-mixed cycle — was NOT reproduced here. With non-obligate
catalysis the parasite self-sustains and invades spatially too; an obligate-catalysis
variant that should expel it was too fragile (it drove the whole system extinct). The
parasite-vs-space rescue is left as a tuning frontier; what this round verifies is the
limit cycle, the exclusion contrast, the well-mixed parasite collapse, and the spirals.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# ----------------------------------------------------------------------------- well-mixed

def replicator_hypercycle(n: int, steps: int = 20000, dt: float = 0.02,
                          k: float = 1.0, x0=None, seed: int = 0,
                          parasite_k: float = 0.0, parasite_host: int = 0):
    """Replicator dynamics of a catalytic cycle (i is catalysed by i-1, cyclically).

    dx_i/dt = x_i (k * x_{i-1} - phi),  phi chosen so the simplex sum is conserved.
    Optional parasite (last component) is catalysed by `parasite_host` but catalyses no one.
    Returns traj array (steps+1, m) where m = n (+1 if parasite)."""
    rng = np.random.default_rng(seed)
    has_par = parasite_k > 0.0
    m = n + (1 if has_par else 0)
    x = np.asarray(x0, float).copy() if x0 is not None else (np.ones(m) / m + 0.01 * rng.random(m))
    x /= x.sum()
    traj = np.empty((steps + 1, m))
    traj[0] = x
    for t in range(steps):
        cat = k * x[np.arange(n) - 1]                 # x_{i-1} cyclic, for cycle members
        growth = np.empty(m)
        growth[:n] = x[:n] * cat
        if has_par:
            growth[n] = x[n] * parasite_k * x[parasite_host]   # parasite fed by its host
        phi = growth.sum()                            # mean fitness -> keeps sum=1
        x = x + dt * (growth - x * phi)
        x = np.clip(x, 0.0, None)
        x /= x.sum()
        traj[t + 1] = x
    return traj


def replicator_independent(n: int, steps: int = 20000, dt: float = 0.02,
                           k=None, x0=None, seed: int = 0):
    """Control: uncoupled replicators dx_i/dt = x_i(k_i - phi). Competitive exclusion —
    only the largest k_i survives."""
    rng = np.random.default_rng(seed)
    k = np.asarray(k, float) if k is not None else (1.0 + 0.1 * rng.random(n))
    x = np.asarray(x0, float).copy() if x0 is not None else (np.ones(n) / n + 0.01 * rng.random(n))
    x /= x.sum()
    traj = np.empty((steps + 1, n))
    traj[0] = x
    for t in range(steps):
        phi = (x * k).sum()
        x = x + dt * x * (k - phi)
        x = np.clip(x, 0.0, None); x /= x.sum()
        traj[t + 1] = x
    return traj


def survivors(traj, thresh: float = 1e-3) -> int:
    """How many components are still present at the end (above threshold)."""
    return int((traj[-1] > thresh).sum())


def persistent(traj, tail: float = 0.4, thresh: float = 1e-3) -> int:
    """How many components persist across the tail — peak above threshold (the right test
    for a LIMIT CYCLE, where members are near zero only momentarily in their trough)."""
    s = int(len(traj) * (1 - tail))
    return int((traj[s:].max(axis=0) > thresh).sum())


def amplitude(traj, tail: float = 0.5) -> float:
    """Peak-to-peak oscillation of the cycle members over the last `tail` of the run
    (≈0 => settled to a fixed point; large => limit cycle)."""
    s = int(len(traj) * (1 - tail))
    seg = traj[s:]
    return float((seg.max(axis=0) - seg.min(axis=0)).max())


# ----------------------------------------------------------------------------- spatial

@dataclass(frozen=True)
class SpatialConfig:
    n: int = 5              # cyclic species (>=5 -> oscillatory medium -> spirals)
    size: int = 200
    death: float = 0.06     # per-step death probability of an occupied site
    cat: float = 2.0        # catalytic boost: colonisation weight of i = #nbr_i * (1 + cat * #nbr_{i-1})
    empty_w: float = 0.3    # baseline weight to stay empty (tunes occupancy)


EMPTY = -1


def _moore_counts(state, s: int):
    """Count Moore-neighbourhood (8) cells equal to species s, on a torus."""
    a = (state == s).astype(np.float64)
    return sum(np.roll(np.roll(a, dy, 0), dx, 1)
               for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0))


def spatial_hypercycle(cfg: SpatialConfig, steps: int, seed: int = 0,
                       parasite: bool = False, parasite_host: int = 0,
                       record_every: int = 0):
    """Boerlijst-Hogeweg cyclic catalytic CA on a torus -> rotating SPIRAL WAVES.

    Each cell is EMPTY or one of n cyclic species (optionally a parasite = species n).
    Each step: occupied cells die with prob `death`; empty cells are colonised by species
    i with weight (#neighbours_i) * (1 + cat * #neighbours_{i-1}) — i.e. a species spreads
    where it is present AND its catalyst i-1 is present. The parasite is colonised via its
    host but catalyses no one. The cyclic coupling makes an oscillatory medium that rolls
    up into spirals."""
    rng = np.random.default_rng(seed)
    n, N = cfg.n, cfg.size
    m = n + (1 if parasite else 0)
    state = rng.integers(-1, m, (N, N))               # random species / empty seed (parasite seeded too, so its
    #                                                   absence later is genuine expulsion, not never-present)
    snaps = {}
    for t in range(steps):
        counts = [_moore_counts(state, s) for s in range(m)]
        # death
        occ = state >= 0
        died = occ & (rng.random((N, N)) < cfg.death)
        nxt = state.copy()
        nxt[died] = EMPTY
        # colonisation weights for currently-empty cells
        empty = state == EMPTY
        W = np.empty((m + 1, N, N))
        for i in range(n):
            W[i] = counts[i] * (1.0 + cfg.cat * counts[(i - 1) % n])   # spread where present, boosted by catalyst
        if parasite:
            W[n] = counts[n] * (1.0 + cfg.cat * counts[parasite_host])
        W[m] = cfg.empty_w                            # stay-empty option
        probs = W / W.sum(axis=0, keepdims=True)
        cum = np.cumsum(probs, axis=0)
        u = rng.random((N, N))
        choice = (u[None, :, :] > cum).sum(axis=0)    # 0..m ; m means stay empty
        col = empty & (choice < m)
        nxt[col] = choice[col]
        state = nxt
        if record_every and (t % record_every == 0 or t == steps - 1):
            snaps[t] = state.copy()
    return {"state": state, "snaps": snaps, "n": n, "has_par": parasite}


def area_fractions(state, n: int):
    return np.array([(state == i).mean() for i in range(n)])


def spatial_structure(state, n: int) -> float:
    """Local heterogeneity: fraction of Moore-neighbours that differ from the centre,
    averaged over occupied cells. ~0 => uniform domains; high => fine wave fronts."""
    occ = state >= 0
    if occ.sum() == 0:
        return 0.0
    diff = sum((np.roll(np.roll(state, dy, 0), dx, 1) != state).astype(float)
               for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0)) / 8.0
    return float(diff[occ].mean())


def rgb_field(state, n: int):
    """Colour each species a distinct hue (empty = black) -> an image of the spiral field."""
    import matplotlib.colors as mcolors
    hues = np.linspace(0, 1, n, endpoint=False)
    img = np.zeros(state.shape + (3,))
    for i in range(n):
        img[state == i] = mcolors.hsv_to_rgb((hues[i], 0.85, 1.0))
    if state.max() >= n:                              # parasite drawn white
        img[state == n] = (1.0, 1.0, 1.0)
    return img
