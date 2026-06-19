"""R92 — Turing animal coats: the Gierer-Meinhardt activator-inhibitor.

R45 (Gray-Scott) selects patterns by feed/kill rates. This round builds the OTHER canonical Turing
system — Gierer & Meinhardt (1972) — stated in its own terms: a slowly-diffusing ACTIVATOR that
autocatalyses itself locally, and a fast-diffusing INHIBITOR it switches on that suppresses it at a
distance. That "short-range activation, long-range inhibition" is the textbook recipe for biological
pattern, and it produces leopard-style spots with an INTRINSIC WAVELENGTH: the pattern doesn't care
how big the animal is, so the number of spots scales with the area of the coat (small domain → few
spots, large domain → many, at constant spacing). Domain geometry then sets how those spots are
arranged.

HONEST NEGATIVE (recorded, not faked): the famous Murray spots-vs-stripes-by-geometry result (a
spotted body with a striped tail) did NOT reproduce in this spot-regime parameterization — narrowing
the domain reduces rows of spots and a sub-wavelength tail goes blank rather than forming clean
transverse stripes, and the saturation term here suppresses the pattern instead of striping it.
Clean GM stripes need a different parameter regime; left as a frontier.

Activator a, inhibitor h on a bounded (zero-flux) domain; explicit Euler, 5-point Laplacian. CPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage


@dataclass(frozen=True)
class GMConfig:
    Da: float = 0.04         # activator diffusion (short range)
    Dh: float = 1.0          # inhibitor diffusion (long range) — Dh >> Da is the Turing condition
    rho: float = 0.04        # activator production scale
    mu_a: float = 0.06       # activator decay
    mu_h: float = 0.12       # inhibitor decay
    a0: float = 0.01         # small basal activator production (keeps h>0, stabilises)
    kappa: float = 0.0       # activator saturation: 0 -> spots, >0 -> stripes
    dt: float = 0.2
    steps: int = 6000


def _lap(a):
    """5-point Laplacian with zero-flux (Neumann) boundaries via edge padding."""
    p = np.pad(a, 1, mode="edge")
    return p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:] - 4.0 * a


def gm_step(a, h, cfg, mask=None):
    """One Gierer-Meinhardt update. Optional mask (bool) restricts the active domain."""
    react_a = cfg.rho * (a * a / (h * (1.0 + cfg.kappa * a * a))) - cfg.mu_a * a + cfg.a0
    react_h = cfg.rho * (a * a) - cfg.mu_h * h
    a = a + cfg.dt * (cfg.Da * _lap(a) + react_a)
    h = h + cfg.dt * (cfg.Dh * _lap(h) + react_h)
    a = np.clip(a, 0.0, 1e3)
    h = np.clip(h, 1e-6, 1e3)
    if mask is not None:
        a = np.where(mask, a, 0.0)
        h = np.where(mask, h, 1.0)
    return a, h


def run(shape, cfg=GMConfig(), seed=0, mask=None, return_h=False):
    """Seed near the homogeneous steady state with small noise; evolve to a Turing pattern.
    Returns the activator field (or (activator, inhibitor) if return_h)."""
    rng = np.random.default_rng(seed)
    a = 1.0 + 0.05 * rng.standard_normal(shape)
    h = 1.0 + 0.05 * rng.standard_normal(shape)
    if mask is not None:
        a = np.where(mask, a, 0.0)
        h = np.where(mask, h, 1.0)
    for _ in range(cfg.steps):
        a, h = gm_step(a, h, cfg, mask)
    return (a, h) if return_h else a


def _binary(a, mask=None):
    """Threshold the activator into pattern spots/stripes (above-mean = pattern)."""
    if mask is None:
        thr = a.mean()
        return a > thr
    thr = a[mask].mean()
    return (a > thr) & mask


def count_spots(a, mask=None):
    """Number of connected activator blobs (Turing pattern elements)."""
    b = _binary(a, mask)
    _, n = ndimage.label(b)
    return int(n)


def stripe_index(a, mask=None):
    """Mean elongation (major/minor axis) of pattern components: ~1 = spots, >>1 = stripes."""
    b = _binary(a, mask)
    lbl, n = ndimage.label(b)
    if n == 0:
        return 0.0
    elong = []
    for i in range(1, n + 1):
        ys, xs = np.where(lbl == i)
        if len(xs) < 8:
            continue
        c = np.cov(np.vstack([xs, ys]))
        ev = np.linalg.eigvalsh(c)
        ev = np.clip(ev, 1e-9, None)
        elong.append(np.sqrt(ev[-1] / ev[0]))
    return float(np.mean(elong)) if elong else 1.0
