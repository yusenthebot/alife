"""R106 — Surface growth and the KPZ universality class.

Drop particles onto a line and a growing interface forms — but *how* it roughens depends on a single
rule. If each particle simply stacks where it lands (random deposition), columns are independent and
the surface width grows forever as w ~ t^{1/2}, pure uncorrelated noise. Let a particle instead stick
on FIRST lateral contact (ballistic deposition) and neighbouring columns become correlated: the width
now grows as w ~ t^{β} with the anomalous Kardar-Parisi-Zhang exponent β ≈ 1/3, then SATURATES at a
value set by system size, w_sat ~ L^{α} with α ≈ 1/2. KPZ is one of the deepest results in
non-equilibrium physics — the same universality governs burning fronts, bacterial colonies, growing
crystals and coffee-ring edges. Here it falls out of one sticking rule, and a random-deposition
control recovers the trivial 1/2 to prove the lateral correlation is what bends the exponent.

Pure numpy/CPU; periodic 1D substrate.
"""

from __future__ import annotations

import numpy as np


def random_deposition(L=256, layers=2000, seed=0, record_every=1):
    """Each particle stacks on its own column (columns independent) -> w ~ t^{1/2}."""
    rng = np.random.default_rng(seed)
    h = np.zeros(L)
    ts, ws = [], []
    for layer in range(1, layers + 1):
        cols = rng.integers(0, L, L)                          # L particles this layer, random columns
        np.add.at(h, cols, 1.0)
        if layer % record_every == 0:
            ts.append(layer); ws.append(float(h.std()))
    return {"h": h, "t": np.asarray(ts, float), "w": np.asarray(ws)}


def ballistic_deposition(L=256, layers=2000, seed=0, record_every=1):
    """Particle sticks on first lateral contact: h[i] -> max(h[i-1], h[i]+1, h[i+1]) -> KPZ roughening."""
    rng = np.random.default_rng(seed)
    h = np.zeros(L)
    ts, ws = [], []
    drops = layers * L
    cols = rng.integers(0, L, drops)                          # pre-draw all target columns
    for d in range(drops):
        i = cols[d]
        h[i] = max(h[i - 1], h[i] + 1.0, h[(i + 1) % L])      # i-1 wraps via negative index
        if (d + 1) % (L * record_every) == 0:
            ts.append((d + 1) / L); ws.append(float(h.std()))
    return {"h": h, "t": np.asarray(ts, float), "w": np.asarray(ws)}


def growth_exponent(t, w, t0=20.0, hi_frac=0.9):
    """Fit beta = slope of log w vs log t over the growth regime (skip the early transient, stop
    before any saturation). Single realisations are noisy (~+-0.1); average over seeds for KPZ 1/3."""
    a = int(np.searchsorted(t, t0))
    b = max(a + 4, int(len(t) * hi_frac))
    return float(np.polyfit(np.log(t[a:b]), np.log(w[a:b]), 1)[0])


def mean_growth_exponent(model, L=1000, layers=1200, seeds=4, **kw):
    """Seed-averaged growth exponent (KPZ ballistic ~ 1/3; random ~ 1/2)."""
    fn = ballistic_deposition if model == "ballistic" else random_deposition
    betas = []
    for s in range(seeds):
        r = fn(L=L, layers=layers, seed=s)
        betas.append(growth_exponent(r["t"], r["w"], **kw))
    return float(np.mean(betas)), float(np.std(betas))


def saturation_width(result, frac=0.4):
    """Mean width over the late (saturated) portion."""
    w = result["w"]
    return float(w[int((1 - frac) * len(w)):].mean())


def roughness_exponent(Ls=(32, 64, 128, 256), seed=0):
    """Fit alpha = slope of log(w_sat) vs log(L): the self-affine roughness exponent (KPZ ~ 1/2)."""
    ws = []
    for L in Ls:
        r = ballistic_deposition(int(L), layers=max(600, 8 * int(L)), seed=seed)  # run to saturation
        ws.append(saturation_width(r))
    Ls = np.asarray(Ls, float); ws = np.asarray(ws)
    alpha = float(np.polyfit(np.log(Ls), np.log(ws), 1)[0])
    return Ls, ws, alpha
