"""R126 — How the leopard gets its spots (and why a spotted body can have a striped tail).

R92 (gierermeinhardt) made Turing spots but left Murray's famous geometry rule as a recorded honest
NEGATIVE: a spotted body with a striped tail would not reproduce — the Gierer-Meinhardt saturation made
a narrowed domain go blank instead of striping. This round resolves it with a different reaction-
diffusion system, Gray-Scott, and isolates the mechanism Murray (1981) actually proposed: the SAME
chemistry, but DOMAIN GEOMETRY selects the pattern.

A Turing system has an intrinsic wavelength. On a WIDE 2D sheet the unstable modes point every which
way and interfere into a lattice of SPOTS. Squeeze the domain into a narrow strip and the transverse
direction can no longer hold a full wavelength, so only modes along the strip survive — the spots are
forced to merge into transverse STRIPES. Narrow it below one wavelength and no pattern fits at all
(blank). Hence Murray's asymmetry, visible at a glance: a wide (spotted) body can taper into a narrow
(striped) tail, but a striped (narrow) body can never widen into spots it never had — you see leopards
with striped tails, never the reverse.

This module runs Gray-Scott in a spot-forming regime on (a) strips of decreasing WIDTH to show
spots -> stripes -> blank, and (b) a tapering body+tail domain (no-flux mask). The pattern type is read
by eye and scored by a control-validated blob metric. Pure numpy/CPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

# Gray-Scott spot-forming regime (leopard spots); narrowing the domain forces stripes
SPOT_FK = (0.030, 0.062)


@dataclass(frozen=True)
class CoatConfig:
    Du: float = 0.16
    Dv: float = 0.08
    F: float = 0.030
    k: float = 0.062
    dt: float = 1.0
    steps: int = 10000
    seed: int = 0


def _lap(a):
    return np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1) - 4.0 * a


def _masked_lap(a, m):
    lap = np.zeros_like(a)
    for d, ax in ((1, 0), (-1, 0), (1, 1), (-1, 1)):
        lap += (np.roll(a, d, ax) - a) * np.roll(m, d, ax)     # only in-domain neighbours (no-flux)
    return lap * m


def body_tail_mask(H, W, body_w, tail_w, body_frac=0.42):
    """A creature outline: a wide body that tapers to a narrow tail (for the no-flux domain)."""
    m = np.zeros((H, W), bool)
    cy, bx = H // 2, int(W * body_frac)
    for x in range(W):
        w = body_w if x < bx else max(tail_w, body_w - (body_w - tail_w) * (x - bx) / (W - bx))
        m[int(cy - w / 2):int(cy + w / 2 + 1), x] = True
    return m


def _seed(u, v, H, W, rng, cx_frac=0.2):
    cy, cx = H // 2, int(W * cx_frac)
    r = 12
    v[max(0, cy - r):cy + r, max(0, cx - r):cx + r] = 0.25     # contiguous activator block
    u[max(0, cy - r):cy + r, max(0, cx - r):cx + r] = 0.5


def run_strip(cfg: CoatConfig, H=120, W=120):
    """Gray-Scott on a full H x W rectangle (no-flux via roll on a non-wrapping interior)."""
    rng = np.random.default_rng(cfg.seed)
    u = np.ones((H, W)) + 0.02 * rng.standard_normal((H, W))
    v = np.zeros((H, W))
    _seed(u, v, H, W, rng)
    for _ in range(cfg.steps):
        uvv = u * v * v
        u = u + cfg.dt * (cfg.Du * _lap(u) - uvv + cfg.F * (1 - u))
        v = v + cfg.dt * (cfg.Dv * _lap(v) + uvv - (cfg.F + cfg.k) * v)
    return v


def run_shape(cfg: CoatConfig, mask):
    """Gray-Scott on an arbitrary no-flux masked domain (the tapering creature)."""
    rng = np.random.default_rng(cfg.seed)
    H, W = mask.shape
    u = np.ones((H, W)) + 0.02 * rng.standard_normal((H, W)) * mask
    v = np.zeros((H, W))
    _seed(u, v, H, W, rng)
    for _ in range(cfg.steps):
        uvv = u * v * v
        u = u + cfg.dt * (cfg.Du * _masked_lap(u, mask) - uvv + cfg.F * (1 - u)) * mask
        v = v + cfg.dt * (cfg.Dv * _masked_lap(v, mask) + uvv - (cfg.F + cfg.k) * v) * mask
    return v * mask


def n_spots(v, thresh=0.2) -> int:
    """Number of connected pattern components (a control-validated blob counter)."""
    lbl, n = ndimage.label(v > thresh)
    return int(n)


def mean_blob_elongation(v, thresh=0.2) -> float:
    """Mean component elongation = (bounding-box long side / short side). Spots ~1, stripes >> 1."""
    lbl, n = ndimage.label(v > thresh)
    if n == 0:
        return 0.0
    el = []
    for s in ndimage.find_objects(lbl):
        h = s[0].stop - s[0].start
        w = s[1].stop - s[1].start
        el.append(max(h, w) / max(1, min(h, w)))
    return float(np.mean(el))


def pattern_type(v, thresh=0.2) -> str:
    """Classify: 'blank' (no pattern), 'stripes' (few, elongated), or 'spots' (many, compact)."""
    n = n_spots(v, thresh)
    if n <= 1:
        return "blank"
    return "stripes" if mean_blob_elongation(v, thresh) > 2.2 else "spots"
