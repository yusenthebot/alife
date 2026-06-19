"""R107 — The Olami-Feder-Christensen earthquake model: self-organized criticality with loss.

Earthquakes obey the Gutenberg-Richter law: their sizes are power-law distributed over many decades,
with no characteristic scale. Olami, Feder & Christensen (1992) reproduced this from a spring-block
fault model. A grid of "stress" values is loaded uniformly until some block reaches threshold; it
then SLIPS — resetting to zero and transferring a fraction alpha of its stress to each of its four
neighbours, which may slip in turn, an avalanche (the earthquake). The crucial twist versus the R74
abelian sandpile: the redistribution is NON-CONSERVATIVE (4*alpha < 1 loses stress), and yet
self-organized criticality — a power-law of earthquake sizes — survives. Lower the conservation level
and the catalogue shifts from big system-spanning ruptures toward small ones, the dissipation control
that shows criticality is tuned by how much stress each slip keeps in the fault.

Pure numpy; open boundaries (edge stress is lost). Zero-velocity (instantaneous) loading limit.
"""

from __future__ import annotations

import numpy as np

THRESH = 1.0


def simulate(L=48, alpha=0.22, n_quakes=4000, seed=0, warmup=1000):
    """Drive-and-relax OFC dynamics. Returns avalanche (earthquake) sizes after a warmup transient."""
    rng = np.random.default_rng(seed)
    F = rng.uniform(0, THRESH, (L, L))
    sizes = []
    total = n_quakes + warmup
    for q in range(total):
        F += THRESH - F.max()                                # load until the max site hits threshold
        size = 0
        while True:
            over = F >= THRESH
            n = int(over.sum())
            if n == 0:
                break
            size += n
            give = alpha * F * over                          # each toppling site gives alpha*F to each neighbour
            F[over] = 0.0
            F[1:, :] += give[:-1, :]                         # to the site below (from above) ... open edges drop
            F[:-1, :] += give[1:, :]
            F[:, 1:] += give[:, :-1]
            F[:, :-1] += give[:, 1:]
        if q >= warmup:
            sizes.append(size)
    return np.asarray(sizes)


def size_distribution(sizes, nbins=22):
    """Log-binned probability density of earthquake sizes (power law => straight on log-log)."""
    sizes = sizes[sizes > 0]
    bins = np.unique(np.round(np.logspace(0, np.log10(sizes.max() + 1), nbins)).astype(int))
    hist, edges = np.histogram(sizes, bins=bins)
    centers = np.sqrt(edges[:-1] * edges[1:])
    width = np.diff(edges)
    dens = hist / (width * sizes.size)
    keep = hist > 0
    return centers[keep], dens[keep]


def gr_exponent(sizes, smin=2, smax_frac=0.3):
    """Gutenberg-Richter exponent tau: P(s) ~ s^-tau, fit on log-log over the scaling range."""
    cx, cy = size_distribution(sizes)
    smax = max(smin + 1, smax_frac * cx.max())
    m = (cx >= smin) & (cx <= smax)
    if m.sum() < 3:
        return 0.0
    return float(-np.polyfit(np.log(cx[m]), np.log(cy[m]), 1)[0])


def big_quake_fraction(sizes, L):
    """Fraction of released stress in 'large' earthquakes (>= L sites) — falls as alpha drops."""
    sizes = np.asarray(sizes)
    return float(sizes[sizes >= L].sum() / max(sizes.sum(), 1))
