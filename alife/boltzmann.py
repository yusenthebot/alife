"""R81 — Restricted Boltzmann machine: a neural network that learns to dream (Hinton).

The third face of neural computation in this project. R69's Hopfield net RECALLED stored memories;
R73's reservoir PREDICTED a time series; an RBM is GENERATIVE — it learns the probability
distribution behind a dataset and then dreams new samples from it. Visible units (the image) and
hidden units (features) are coupled by symmetric weights defining an energy E(v,h) = -vᵀWh - bᵀv -
cᵀh; the network is trained by contrastive divergence so its Boltzmann distribution matches the
data. We train on "bars and stripes" — images that are either all horizontal bars OR all vertical
stripes — and the trained RBM, run as a Gibbs-sampling chain from noise, dreams VALID bars/stripes
it was never shown, while its hidden weights become bar/stripe detectors. An untrained net dreams
only noise. Learning a distribution, not memorising patterns.

Pure numpy/CPU; contrastive divergence (CD-1).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))


def bars_and_stripes(n: int):
    """All valid n×n bars-and-stripes images, flattened to (P, n*n) of 0/1.
    Each row independently on/off (horizontal bars) OR each column on/off (vertical stripes)."""
    pats = set()
    for k in range(1 << n):
        bits = np.array([(k >> i) & 1 for i in range(n)])
        rows = np.tile(bits[:, None], (1, n))          # horizontal bars
        cols = np.tile(bits[None, :], (n, 1))          # vertical stripes
        pats.add(tuple(rows.ravel().tolist()))
        pats.add(tuple(cols.ravel().tolist()))
    return np.array(sorted(pats), dtype=np.float64)


@dataclass
class RBM:
    W: np.ndarray        # (n_vis, n_hid)
    b: np.ndarray        # visible bias
    c: np.ndarray        # hidden bias


def init_rbm(n_vis, n_hid, rng):
    return RBM(0.01 * rng.standard_normal((n_vis, n_hid)), np.zeros(n_vis), np.zeros(n_hid))


def _h_given_v(rbm, v):
    return _sigmoid(v @ rbm.W + rbm.c)


def _v_given_h(rbm, h):
    return _sigmoid(h @ rbm.W.T + rbm.b)


def train(data, n_hid=16, epochs=3000, lr=0.1, batch=None, seed=0):
    """Contrastive divergence (CD-1). Returns the trained RBM and the reconstruction-error trace."""
    rng = np.random.default_rng(seed)
    n_vis = data.shape[1]
    rbm = init_rbm(n_vis, n_hid, rng)
    batch = batch or len(data)
    err = []
    for ep in range(epochs):
        idx = rng.integers(0, len(data), batch)
        v0 = data[idx]
        ph0 = _h_given_v(rbm, v0)                       # positive phase
        h0 = (rng.random(ph0.shape) < ph0).astype(float)
        pv1 = _v_given_h(rbm, h0)                        # negative phase (reconstruct)
        v1 = (rng.random(pv1.shape) < pv1).astype(float)
        ph1 = _h_given_v(rbm, v1)
        rbm.W += lr * (v0.T @ ph0 - v1.T @ ph1) / batch
        rbm.b += lr * (v0 - v1).mean(0)
        rbm.c += lr * (ph0 - ph1).mean(0)
        if ep % 20 == 0:
            err.append(float(np.mean((v0 - pv1) ** 2)))
    return rbm, np.array(err)


def gibbs_sample(rbm, n_samples, steps=400, seed=0, start=None):
    """Run Gibbs chains from random (or given) starts; return final visible samples (binary)."""
    rng = np.random.default_rng(seed)
    n_vis = len(rbm.b)
    v = (rng.random((n_samples, n_vis)) < 0.5).astype(float) if start is None else start.copy()
    for _ in range(steps):
        ph = _h_given_v(rbm, v)
        h = (rng.random(ph.shape) < ph).astype(float)
        pv = _v_given_h(rbm, h)
        v = (rng.random(pv.shape) < pv).astype(float)
    return v


def is_valid_bas(img):
    """True if a flattened n×n image is valid bars-and-stripes (all rows uniform OR all cols)."""
    n = int(round(np.sqrt(len(img))))
    g = img.reshape(n, n)
    rows_uniform = np.all(g == g[:, :1])               # every row constant -> horizontal bars
    cols_uniform = np.all(g == g[:1, :])               # every column constant -> vertical stripes
    return bool(rows_uniform or cols_uniform)


def valid_fraction(samples):
    return float(np.mean([is_valid_bas(s) for s in samples]))
