"""R69 — Hopfield networks: memory as an energy landscape, and its breaking point.

The project's earlier brains were feed-forward or recurrent CONTROLLERS (R3/R6/R26). A Hopfield
net is a different idea of computation: a fully-connected network of +/-1 neurons whose symmetric
weights carve an ENERGY LANDSCAPE, and the patterns you store become its valleys. Released from a
corrupted or partial cue, the network slides downhill (each neuron flips to lower the energy) and
settles into the nearest stored memory — content-addressable, error-correcting recall that emerges
from purely local updates, with a global Lyapunov function guaranteeing it always converges.

Three results: (1) pattern completion — recall a clean memory from a noisy/occluded cue; (2) the
energy decreases monotonically to an attractor; (3) the famous CAPACITY phase transition — store
more than ~0.138 N patterns and recall collapses catastrophically (Amit-Gutfreund-Sompolinsky).
Pure numpy/CPU.
"""

from __future__ import annotations

import numpy as np


def store_hebbian(patterns: np.ndarray) -> np.ndarray:
    """Hebbian (outer-product) weights for P patterns (P,N) of +/-1. W symmetric, zero diagonal."""
    P, N = patterns.shape
    W = (patterns.T @ patterns) / N
    np.fill_diagonal(W, 0.0)
    return W


def energy(W: np.ndarray, s: np.ndarray) -> float:
    """E = -1/2 s^T W s — the Lyapunov function that async updates never increase."""
    return float(-0.5 * s @ W @ s)


def recall(W: np.ndarray, s0: np.ndarray, steps: int = 30, mode: str = "async", seed: int = 0):
    """Run the dynamics s_i <- sign(sum_j W_ij s_j) to a fixed point.
    async = one random neuron per micro-step (guarantees energy descent); sync = all at once.
    Returns (final state, energy trace, snapshots per sweep)."""
    rng = np.random.default_rng(seed)
    s = s0.copy().astype(np.int8)
    N = len(s)
    etrace = [energy(W, s)]
    snaps = [s.copy()]
    for _ in range(steps):
        if mode == "async":
            for i in rng.permutation(N):
                h = W[i] @ s
                s[i] = 1 if h >= 0 else -1
        else:
            h = W @ s
            s = np.where(h >= 0, 1, -1).astype(np.int8)
        etrace.append(energy(W, s))
        snaps.append(s.copy())
        if np.array_equal(snaps[-1], snaps[-2]):       # converged to a fixed point
            break
    return s, np.array(etrace), snaps


def overlap(a: np.ndarray, b: np.ndarray) -> float:
    """Normalised overlap in [-1,1]; 1 = identical, -1 = the inverse pattern (also an attractor)."""
    return float(np.mean(a * b))


def corrupt(pattern: np.ndarray, flip_frac: float, rng) -> np.ndarray:
    """Flip a fraction of the bits (noise) to make a degraded cue."""
    s = pattern.copy()
    idx = rng.choice(len(s), int(flip_frac * len(s)), replace=False)
    s[idx] *= -1
    return s


def occlude(pattern: np.ndarray, frac: float) -> np.ndarray:
    """Blank the last `frac` of the bits to -1 (a partial cue, for pattern completion)."""
    s = pattern.copy()
    s[int((1 - frac) * len(s)):] = -1
    return s


def capacity_curve(N: int, alphas, trials: int = 6, flip_frac: float = 0.05, seed: int = 0):
    """Mean recall quality (best |overlap| with the stored pattern) vs load alpha = P/N.
    Drops sharply near alpha_c ~ 0.138 (Amit-Gutfreund-Sompolinsky)."""
    rng = np.random.default_rng(seed)
    out = []
    for a in alphas:
        P = max(1, int(a * N))
        scores = []
        for _ in range(trials):
            pats = rng.choice([-1, 1], (P, N)).astype(np.int8)
            W = store_hebbian(pats)
            for mu in rng.choice(P, min(P, 5), replace=False):       # sample some stored patterns
                cue = corrupt(pats[mu], flip_frac, rng)
                s, _, _ = recall(W, cue, steps=20, seed=int(rng.integers(1 << 30)))
                scores.append(abs(overlap(s, pats[mu])))             # |.|: the inverse counts as recalled
        out.append(float(np.mean(scores)))
    return np.array(list(alphas), float), np.array(out)


def demo_patterns(size: int = 14):
    """A handful of BALANCED, near-orthogonal recognisable patterns for the recall demo.
    (Hopfield recall is clean for balanced/near-orthogonal patterns; sparse correlated images
    like letters share too much background, causing crosstalk and spurious states — so we use
    geometric patterns that are ~50% on and mutually near-orthogonal.)"""
    H = W = size
    yy, xx = np.mgrid[0:H, 0:W]
    cx = cy = (size - 1) / 2
    pats = np.array([
        np.where(xx < W / 2, 1, -1).flatten(),                              # left / right
        np.where(yy < H / 2, 1, -1).flatten(),                              # top / bottom
        np.where((xx + yy) % 2 == 0, 1, -1).flatten(),                      # checkerboard
        np.where(((xx - cx) ** 2 + (yy - cy) ** 2) < (size * size) / 8, 1, -1).flatten(),  # disk
        np.where(((xx // 3) + (yy // 3)) % 2 == 0, 1, -1).flatten(),        # coarse blocks
    ], dtype=np.int8)
    return pats, (H, W)
