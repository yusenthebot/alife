"""R111 — Spatial rock-paper-scissors: mobility and the loss of biodiversity.

Three species in cyclic competition — A beats B beats C beats A — cannot settle: each is checked by
the one it loses to. In a WELL-MIXED population (R39) this gives neutral cycles. On a LATTICE there is
a sharp control parameter. Reichenbach, Mobilia & Frey (Nature 2007) showed that MOBILITY (how fast
individuals hop/mix) decides survival: at low mobility the three species self-organise into rotating
SPIRAL WAVES and coexist indefinitely; raise the mobility and the spiral wavelength grows until it
exceeds the system, the spirals merge, and biodiversity collapses to a single survivor. Movement —
the very thing that seems to help — homogenises the ecosystem to death past a threshold.

Lattice with cyclic predation + reproduction (reaction) and pair EXCHANGE (mobility = diffusion
sweeps per reaction step); vectorised, CPU.
"""

from __future__ import annotations

import numpy as np

_DIJ = np.array([(1, 0), (-1, 0), (0, 1), (0, -1)])


def _prey(s):
    return (s % 3) + 1                                        # A(1)->B(2)->C(3)->A(1)


def init(L=128, seed=0):
    return np.random.default_rng(seed).integers(0, 4, (L, L)).astype(np.int8)


def reaction_step(grid, rng, actor_frac=0.3):
    """Cyclic predation + reproduction over a random actor batch (no movement)."""
    L = grid.shape[0]
    n = int(actor_frac * L * L)
    ai = rng.integers(0, L, n); aj = rng.integers(0, L, n)
    d = rng.integers(0, 4, n)
    bi = (ai + _DIJ[d, 0]) % L; bj = (aj + _DIJ[d, 1]) % L
    A = grid[ai, aj]; B = grid[bi, bj]
    pred = (A > 0) & (B == _prey(A))
    grid[bi[pred], bj[pred]] = 0
    repro = (A > 0) & (B == 0)
    grid[bi[repro], bj[repro]] = A[repro]
    return grid


def diffuse_sweep(grid, rng):
    """One conservative mixing sweep: non-overlapping adjacent ('domino') pairs swap with prob 1/2,
    along a random axis+offset. Each cell is in at most one pair, so species counts are conserved."""
    L = grid.shape[0]
    axis = int(rng.integers(2)); offset = int(rng.integers(2))
    idx = np.arange(offset, L - 1, 2)                          # left members of each domino pair
    if idx.size == 0:
        return grid
    if axis == 1:
        a = grid[:, idx]; b = grid[:, idx + 1]
        sw = rng.random(a.shape) < 0.5
        grid[:, idx] = np.where(sw, b, a); grid[:, idx + 1] = np.where(sw, a, b)
    else:
        a = grid[idx, :]; b = grid[idx + 1, :]
        sw = rng.random(a.shape) < 0.5
        grid[idx, :] = np.where(sw, b, a); grid[idx + 1, :] = np.where(sw, a, b)
    return grid


def run(L=128, mobility=2.0, steps=500, seed=0, record_every=0):
    """Each generation = one reaction step + `mobility` diffusion sweeps (fractional allowed).
    Returns final grid, per-species fractions over time, and snapshots."""
    rng = np.random.default_rng(seed)
    grid = init(L, seed)
    whole = int(mobility); frac = mobility - whole
    fracs, snaps = [], {}
    for t in range(steps):
        reaction_step(grid, rng)
        for _ in range(whole):
            diffuse_sweep(grid, rng)
        if frac > 0 and rng.random() < frac:
            diffuse_sweep(grid, rng)
        fracs.append([float((grid == s).mean()) for s in (1, 2, 3)])
        if record_every and (t % record_every == 0 or t == steps - 1):
            snaps[t] = grid.copy()
    return {"grid": grid, "fracs": np.asarray(fracs), "snaps": snaps}


def n_survivors(result, thresh=0.02):
    """Species still present at the end (3 = biodiversity, 1 = collapse)."""
    return int((result["fracs"][-1] > thresh).sum())


def survival_curve(mobilities, L=96, steps=600, seed=0, reps=2):
    """Surviving-species count vs mobility (3 → 1 above the critical mobility)."""
    rng = np.random.default_rng(seed)
    out = []
    for m in mobilities:
        out.append(float(np.mean([n_survivors(run(L, float(m), steps, seed=int(rng.integers(1 << 30))))
                                  for _ in range(reps)])))
    return np.asarray(mobilities, float), np.asarray(out)
