"""The brain: a tiny feed-forward neural network whose weights ARE the genome.

In Round 2 a creature's behavior was a fixed set of rules with seven evolved
knobs. Here the rules are gone — each creature carries a flat vector of network
weights, and its every move is the output of a forward pass over its own
sensors. The weights are inherited and mutated like any genome; there is no
backprop and no training signal. Competent behavior, if it appears, was *evolved*
by natural selection, not taught.

Layout of the weight vector: [W1 | b1 | W2 | b2], one row per creature, so a
whole population is one matmul.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

W_CLIP = 6.0  # weights live in [-W_CLIP, W_CLIP]


@dataclass(frozen=True)
class BrainSpec:
    n_in: int
    n_hidden: int = 8
    n_out: int = 2

    @property
    def n_weights(self) -> int:
        return (self.n_in + 1) * self.n_hidden + (self.n_hidden + 1) * self.n_out


def random_brains(n: int, spec: BrainSpec, rng: np.random.Generator) -> np.ndarray:
    """Random networks — the disordered start that selection has to work from."""
    return rng.normal(0.0, 1.0, size=(n, spec.n_weights))


def mutate_brains(w: np.ndarray, rng: np.random.Generator, rate: float = 0.2, sigma: float = 0.35) -> np.ndarray:
    """Heritable variation: jitter a fraction of weights, clamp. Pure."""
    noise = rng.normal(0.0, sigma, size=w.shape) * (rng.random(w.shape) < rate)
    return np.clip(w + noise, -W_CLIP, W_CLIP)


def forward(w: np.ndarray, spec: BrainSpec, x: np.ndarray) -> np.ndarray:
    """Batched forward pass. w:(N,W), x:(N,n_in) -> raw outputs (N,n_out)."""
    n, i, h, o = w.shape[0], spec.n_in, spec.n_hidden, spec.n_out
    c = 0
    w1 = w[:, c : c + i * h].reshape(n, i, h); c += i * h
    b1 = w[:, c : c + h]; c += h
    w2 = w[:, c : c + h * o].reshape(n, h, o); c += h * o
    b2 = w[:, c : c + o]
    hidden = np.tanh(np.einsum("ni,nih->nh", x, w1) + b1)
    return np.einsum("nh,nho->no", hidden, w2) + b2
