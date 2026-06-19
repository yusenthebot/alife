"""R129 — Chladni figures: sand finds the silence on a singing plate.

Bow a metal plate and sprinkle sand on it: the grains dance, then settle into a sharp, symmetric figure
of curves and loops. Chladni (1787) made the standing-wave patterns of a vibrating plate visible this
way — and the figures change with pitch. The reason is simple: the plate vibrates in a normal MODE, a
standing wave with NODAL LINES where the surface never moves; a bouncing grain drifts off the shaking
antinodes and comes to rest exactly on those motionless nodes, so the sand draws the mode's zero set.

We model a square plate by its membrane normal modes (analytic), phi_{m,n} = sin(m pi x) sin(n pi y),
with frequency proportional to sqrt(m^2 + n^2). Crucially (m,n) and (n,m) are DEGENERATE — same
frequency — so the plate is free to vibrate in any combination phi_{m,n} +/- phi_{n,m}, and those
combinations give the rich diagonal Chladni figures (not just a grid). Then we let grains SELF-ASSEMBLE:
each drifts down the gradient of the squared amplitude phi^2 (away from antinodes) with a little noise,
and they pile up on the nodal set |phi|=0 — the figure emerges before your eyes. Pure numpy/scipy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ChladniConfig:
    m: int = 3
    n: int = 2
    c: float = -1.0           # degenerate-mode mix sign: phi_{m,n} + c*phi_{n,m}
    N: int = 300              # field resolution
    ngrain: int = 5000
    steps: int = 500
    mu: float = 0.0008        # drift rate toward nodes
    noise: float = 0.004
    seed: int = 0


def eigenfrequency(m, n) -> float:
    """Square-membrane modal frequency (units of pi*c/L): proportional to sqrt(m^2+n^2)."""
    return float(np.sqrt(m * m + n * n))


def mode_field(cfg: ChladniConfig):
    """The (degenerate) standing-wave amplitude phi_{m,n} + c*phi_{n,m} on the unit square."""
    x = np.linspace(0.0, 1.0, cfg.N)
    X, Y = np.meshgrid(x, x)
    phi = np.sin(cfg.m * np.pi * X) * np.sin(cfg.n * np.pi * Y)
    if cfg.m != cfg.n:
        phi = phi + cfg.c * np.sin(cfg.n * np.pi * X) * np.sin(cfg.m * np.pi * Y)
    return phi


def _phi_at(phi, p):
    N = phi.shape[0]
    ix = np.clip((p[:, 0] * (N - 1)).astype(int), 0, N - 1)
    iy = np.clip((p[:, 1] * (N - 1)).astype(int), 0, N - 1)
    return phi[iy, ix]


def assemble_sand(cfg: ChladniConfig, phi=None, record_every: int = 0):
    """Grains drift down grad(phi^2) (away from antinodes) + noise -> settle on the nodal lines."""
    if phi is None:
        phi = mode_field(cfg)
    N = phi.shape[0]
    rng = np.random.default_rng(cfg.seed)
    p = rng.uniform(0.02, 0.98, (cfg.ngrain, 2))
    gy, gx = np.gradient(phi ** 2)
    snaps = []
    for t in range(cfg.steps):
        ix = np.clip((p[:, 0] * (N - 1)).astype(int), 0, N - 1)
        iy = np.clip((p[:, 1] * (N - 1)).astype(int), 0, N - 1)
        p[:, 0] -= cfg.mu * gx[iy, ix] * N
        p[:, 1] -= cfg.mu * gy[iy, ix] * N
        p += cfg.noise * rng.standard_normal(p.shape)
        p = np.clip(p, 0.01, 0.99)
        if record_every and (t % record_every == 0 or t == cfg.steps - 1):
            snaps.append(p.copy())
    return {"pos": p, "phi": phi, "snaps": snaps}


def node_amplitude(phi, pos) -> float:
    """Mean |phi| at the grain positions (small => grains sit on the nodes)."""
    return float(np.abs(_phi_at(phi, pos)).mean())


def nodal_line_count(cfg: ChladniConfig) -> int:
    """Number of interior horizontal + vertical nodal lines of the base mode sin(m pi x)sin(n pi y)."""
    return (cfg.m - 1) + (cfg.n - 1)


def is_symmetric_combo(cfg: ChladniConfig) -> bool:
    """The + combination is symmetric under x<->y; the - combination is antisymmetric."""
    phi = mode_field(cfg)
    if cfg.c > 0:
        return bool(np.allclose(phi, phi.T, atol=1e-9))
    return bool(np.allclose(phi, -phi.T, atol=1e-9))
