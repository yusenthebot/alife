"""R71 — Bak-Sneppen co-evolution: self-organized criticality and punctuated equilibrium.

A new dimension for the project: CRITICALITY. Bak & Sneppen (1993) model an ecosystem as a
ring of species, each with a fitness in [0,1]. The least-fit species goes extinct and is
replaced — and because species are coupled, its two neighbours are dragged down too (a
mutation/extinction event ripples). Run this simplest possible rule and the ecosystem TUNES
ITSELF, with no parameter to set, to a critical state:

  * the global minimum fitness creeps up to a self-organized threshold f_c ≈ 0.667, above
    which almost all species sit and below which activity churns;
  * activity comes in AVALANCHES whose sizes follow a POWER LAW (the signature of self-
    organized criticality — scale-free, no characteristic size);
  * evolution proceeds by PUNCTUATED EQUILIBRIUM — long stasis where the minimum barely
    moves, broken by sudden bursts that sweep through many species (Gould-Eldredge, emergent).

No tuning, no fitness function imposed from outside — criticality is the attractor of the
dynamics itself. Pure numpy/CPU.
"""

from __future__ import annotations

import numpy as np

F_C_1D = 0.667          # known self-organized critical threshold for the 1D nearest-neighbour model


def run(n: int = 400, steps: int = 400_000, seed: int = 0, record_min: bool = True,
        track_activity: bool = False):
    """Run the Bak-Sneppen dynamics. Each step: the minimum-fitness species and its two ring
    neighbours get fresh random fitnesses. Returns fitnesses, the min-fitness time series, the
    index mutated each step, and (optionally) a coarse space-time activity record."""
    rng = np.random.default_rng(seed)
    f = rng.random(n)
    min_trace = np.empty(steps) if record_min else None
    mutated = np.empty(steps, dtype=np.int32)
    for t in range(steps):
        i = int(np.argmin(f))
        if record_min:
            min_trace[t] = f[i]                         # the SELECTED minimum (before replacement)
        mutated[t] = i
        f[i] = rng.random()
        f[(i - 1) % n] = rng.random()
        f[(i + 1) % n] = rng.random()
    return {"f": f, "min_trace": min_trace, "mutated": mutated, "n": n}


def avalanche_sizes(min_trace: np.ndarray, f0: float):
    """f0-avalanches: a maximal run of consecutive steps whose global-min fitness is below f0.
    Their sizes are power-law distributed when f0 is near the critical threshold."""
    below = min_trace < f0
    sizes = []
    run_len = 0
    for b in below:
        if b:
            run_len += 1
        elif run_len:
            sizes.append(run_len); run_len = 0
    if run_len:
        sizes.append(run_len)
    return np.array(sizes)


def power_law_fit(sizes: np.ndarray, smin: int = 1, smax: int = None):
    """Log-log slope of the avalanche size distribution (the SOC exponent ~ -1 to -1.1).
    Returns (size_centers, pdf, slope)."""
    sizes = sizes[sizes >= smin]
    if smax:
        sizes = sizes[sizes <= smax]
    if len(sizes) < 10:
        return np.array([]), np.array([]), float("nan")
    bins = np.unique(np.round(np.logspace(0, np.log10(sizes.max()), 24)).astype(int))
    hist, edges = np.histogram(sizes, bins=bins, density=True)
    centers = np.sqrt(edges[:-1] * edges[1:])
    ok = hist > 0
    centers, hist = centers[ok], hist[ok]
    slope = np.polyfit(np.log10(centers), np.log10(hist), 1)[0]
    return centers, hist, float(slope)


def activity_spacetime(n: int, steps: int, seed: int = 0, window: int = None):
    """A space-time record of where mutations happen (downsampled). Bursts of spatially-
    localized activity = avalanches; long quiet stretches = stasis (punctuated equilibrium)."""
    r = run(n, steps, seed, record_min=True)
    mutated = r["mutated"]
    window = window or max(1, steps // 600)
    rows = steps // window
    grid = np.zeros((rows, n))
    for t in range(rows * window):
        grid[t // window, mutated[t]] += 1.0
    return grid, r["min_trace"]


def threshold_estimate(min_trace: np.ndarray, burn: float = 0.5) -> float:
    """Self-organized critical threshold f_c: the selected minima are ~uniform on [0, f_c] in
    steady state, so f_c is their upper edge — estimated as a near-max percentile."""
    s = min_trace[int(len(min_trace) * burn):]
    return float(np.percentile(s, 99.9))
