"""R61 — Particle Life: life-like structure from an asymmetric force matrix.

A different route to self-organization (Ventrella's "Clusters"; popularised as
Particle Life). Particles come in a few types; a small K x K matrix sets, for every
ordered pair of types, whether one is attracted to or repelled by the other — and
crucially the matrix is ASYMMETRIC (red may chase green while green flees red). Add
a universal hard short-range repulsion (so particles don't collapse) and gentle
friction, and from a random sprinkle the particles knot themselves into membranes,
cells, chasers and wandering aggregates — emergent "organisms" with no genomes and
no fitness, purely from local pairwise rules. Different matrices grow different
artificial biota.

CPU + scipy cKDTree for the neighbour forces (O(N log N)); a few tens of thousands
of particles run comfortably.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree


@dataclass(frozen=True)
class ParticleLifeConfig:
    n: int = 12000
    types: int = 5
    world: float = 1000.0
    r_max: float = 42.0       # interaction radius
    r_inner: float = 12.0     # hard-repulsion radius
    force: float = 0.6        # global force scale
    friction: float = 0.86    # velocity retained per step
    dt: float = 1.0
    steps: int = 600


def random_matrix(types: int, rng) -> np.ndarray:
    """Asymmetric attraction matrix in [-1, 1]."""
    return rng.uniform(-1.0, 1.0, (types, types))


def _profile(d, fij, r_inner, r_max):
    """Force magnitude vs distance: hard repulsion < r_inner, then fij-scaled tent to r_max."""
    f = np.zeros_like(d)
    near = d < r_inner
    f[near] = (d[near] / max(r_inner, 1e-6) - 1.0)            # -1..0 repulsion (always pushes apart)
    mid = (~near) & (d < r_max)
    x = (d[mid] - r_inner) / (r_max - r_inner)               # 0..1
    f[mid] = fij[mid] * (1.0 - np.abs(2.0 * x - 1.0))         # tent peaked mid-range, scaled by matrix
    return f


def run(cfg: ParticleLifeConfig, matrix: np.ndarray, seed: int = 0, record_every: int = 0):
    rng = np.random.default_rng(seed)
    pos = rng.uniform(0, cfg.world, (cfg.n, 2))
    vel = np.zeros((cfg.n, 2))
    typ = rng.integers(0, cfg.types, cfg.n)
    snaps = {}
    clustering = []
    for t in range(cfg.steps):
        tree = cKDTree(pos, boxsize=cfg.world)               # periodic
        pairs = tree.query_pairs(cfg.r_max, output_type="ndarray")
        if len(pairs):
            i, j = pairs[:, 0], pairs[:, 1]
            d = pos[j] - pos[i]
            d -= cfg.world * np.round(d / cfg.world)          # min-image
            dist = np.linalg.norm(d, axis=1) + 1e-9
            u = d / dist[:, None]
            # force on i from j uses matrix[type_i, type_j]; on j from i uses matrix[type_j, type_i]
            fij = matrix[typ[i], typ[j]]
            fji = matrix[typ[j], typ[i]]
            mag_i = _profile(dist, fij, cfg.r_inner, cfg.r_max)
            mag_j = _profile(dist, fji, cfg.r_inner, cfg.r_max)
            acc = np.zeros((cfg.n, 2))
            np.add.at(acc, i, (mag_i)[:, None] * u)
            np.add.at(acc, j, (mag_j)[:, None] * (-u))
            vel += cfg.force * acc * cfg.dt
        vel *= cfg.friction
        pos = np.mod(pos + vel * cfg.dt, cfg.world)
        if record_every and (t % record_every == 0 or t == cfg.steps - 1):
            snaps[t] = (pos.copy(), typ.copy())
            # clustering: mean neighbours within r_inner*1.5 (aggregation vs uniform)
            nn = cKDTree(pos, boxsize=cfg.world).query_ball_point(pos[:200], cfg.r_inner * 1.5)
            clustering.append((t, float(np.mean([len(x) for x in nn]))))
    return {"pos": pos, "typ": typ, "snaps": snaps, "clustering": np.array(clustering, dtype=float),
            "matrix": matrix}


def aggregation(cfg: ParticleLifeConfig, result) -> float:
    """Mean local neighbour count (high => clumped into structures, ~uniform-expectation => gas)."""
    pos = result["pos"]
    nn = cKDTree(pos, boxsize=cfg.world).query_ball_point(pos[:300], cfg.r_inner * 1.5)
    return float(np.mean([len(x) for x in nn]))
