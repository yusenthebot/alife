"""R122 — The dielectric-breakdown model: one knob from compact blobs to lightning needles.

Mineral dendrites, electrodeposits, lightning, viscous fingers and DLA clusters are all Laplacian
GROWTH: a cluster grows into the gradient of a harmonic field (an electric potential, a pressure, a
concentration). R78's DLA is the random-walker realisation of one special case. Niemeyer, Pietronero &
Wiesmann (1984) gave the deterministic, field-based generalisation — the dielectric-breakdown model —
with a single exponent eta that DLA hides:

  solve Laplace's equation around the cluster (phi=0 on the cluster, phi=1 far away), then add a new
  cell on the perimeter with probability proportional to the local field to the power eta:  p ~ phi^eta.

eta sweeps the whole morphology zoo: eta=0 ignores the field and fills compactly (fractal dimension
D -> 2, Eden-like); eta=1 reproduces DLA (D ~ 1.7); large eta over-rewards the strongest tip, so the
cluster collapses to sparse, lightning-like NEEDLES (D -> 1). The field itself is the explanation —
protruding tips screen the fjords, concentrating the gradient and hence the growth, and eta sets how
ruthlessly that advantage compounds.

Each step solves the Laplace field on the free region with a sparse direct solver (a precomputed
5-point Laplacian, boolean-restricted to the free cells). Pure numpy/scipy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve

_LAP_CACHE = {}


@dataclass(frozen=True)
class DBMConfig:
    M: int = 121           # grid size
    eta: float = 1.0       # growth exponent: 0=compact, 1=DLA, large=needles
    target: int = 800      # cluster size to grow to
    batch: int = 4         # cells added per Laplace solve (speed vs accuracy)
    seed: int = 0


def _laplacian(M):
    if M not in _LAP_CACHE:
        T = sp.diags([-1.0, 2.0, -1.0], [-1, 0, 1], shape=(M, M))
        I = sp.identity(M)
        _LAP_CACHE[M] = (sp.kron(I, T) + sp.kron(T, I)).tocsr()
    return _LAP_CACHE[M]


def solve_field(cluster):
    """Harmonic potential: phi=0 on the cluster, phi=1 on the outer ring, Laplace's eq. between."""
    M = cluster.shape[0]
    L = _laplacian(M)
    ring = np.zeros((M, M), bool)
    ring[0, :] = ring[-1, :] = ring[:, 0] = ring[:, -1] = True
    fixed = cluster | ring
    val = np.where(cluster, 0.0, 1.0)              # ring (not cluster) -> 1
    free = (~fixed).ravel()
    fi = np.where(free)[0]
    ci = np.where(~free)[0]
    A = L[fi][:, fi]
    b = -L[fi][:, ci] @ val.ravel()[ci]
    phi = val.ravel().copy()
    phi[fi] = spsolve(A.tocsc(), b)
    return phi.reshape(M, M)


def _perimeter(cluster):
    per = np.zeros_like(cluster)
    for d in (1, -1):
        per |= np.roll(cluster, d, 0)
        per |= np.roll(cluster, d, 1)
    per &= ~cluster
    per[0, :] = per[-1, :] = per[:, 0] = per[:, -1] = False
    return per


def grow(cfg: DBMConfig):
    """Grow a DBM cluster from a central seed. Returns the cluster, the final field, and mass."""
    rng = np.random.default_rng(cfg.seed)
    M = cfg.M
    cluster = np.zeros((M, M), bool)
    cluster[M // 2, M // 2] = True
    phi = None
    while cluster.sum() < cfg.target:
        phi = solve_field(cluster)
        per = _perimeter(cluster)
        ci, cj = np.where(per)
        if ci.size == 0:
            break
        w = np.clip(phi[ci, cj], 0.0, None) ** cfg.eta
        s = w.sum()
        if s <= 0:
            break
        w = w / s
        k = min(cfg.batch, ci.size)
        pick = rng.choice(ci.size, k, replace=False, p=w)
        cluster[ci[pick], cj[pick]] = True
        if cluster[2, :].any() or cluster[-3, :].any() or cluster[:, 2].any() or cluster[:, -3].any():
            break                                  # reached the boundary
    return {"cluster": cluster, "phi": phi if phi is not None else solve_field(cluster),
            "mass": int(cluster.sum())}


def fractal_dimension(cluster, n=14):
    """Radius-mass scaling exponent D: mass(<R) ~ R^D (D=2 compact, ~1.7 DLA, ->1 needles)."""
    M = cluster.shape[0]
    c = M // 2
    ci, cj = np.where(cluster)
    if ci.size < 20:
        return 0.0
    r = np.hypot(ci - c, cj - c)
    Rs = np.linspace(3.0, r.max() * 0.9, n)
    mass = np.array([(r <= R).sum() for R in Rs])
    good = mass > 0
    return float(np.polyfit(np.log(Rs[good]), np.log(mass[good]), 1)[0])


def dimension_curve(etas, cfg: DBMConfig):
    """Fractal dimension vs eta: monotonically decreasing (compact -> fractal -> needle)."""
    from dataclasses import replace
    return np.asarray(etas, float), np.array([fractal_dimension(grow(replace(cfg, eta=float(e)))["cluster"])
                                              for e in etas])
