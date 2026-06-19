"""R138 — Turing patterns on a sphere: how an animal gets its spots on a curved, closed body.

A leopard's coat is a Turing pattern, but real animals are not flat sheets — the pattern forms on a
curved, closed surface, and the geometry talks back. Here the Gray-Scott reaction-diffusion system runs
on the surface of a sphere (an icosphere mesh, so there is no coordinate pole singularity and the
resolution is near-uniform). The same chemistry that makes spots on a plane makes spots on the ball, but
the CLOSED topology quantises them: there is no boundary, the pattern must wrap around and join up, and
the number of spots is set by the ratio of the sphere's size to the intrinsic Turing wavelength — shrink
the wavelength (less diffusion) and the ball grows more, smaller spots.

Mesh: an icosahedron subdivided `subdiv` times and projected to the unit sphere (vertex count 10*4^n+2).
Diffusion uses the random-walk graph Laplacian (Lap u = mean(neighbours) - u), whose eigenvalues lie in
[-2, 0] so the standard explicit Gray-Scott step is stable. numpy + scipy.sparse.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components

_ICO_V = np.array([
    [-1, 1.618033988749895, 0], [1, 1.618033988749895, 0], [-1, -1.618033988749895, 0],
    [1, -1.618033988749895, 0], [0, -1, 1.618033988749895], [0, 1, 1.618033988749895],
    [0, -1, -1.618033988749895], [0, 1, -1.618033988749895], [1.618033988749895, 0, -1],
    [1.618033988749895, 0, 1], [-1.618033988749895, 0, -1], [-1.618033988749895, 0, 1]], float)
_ICO_F = np.array([
    [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11], [1, 5, 9], [5, 11, 4], [11, 10, 2],
    [10, 7, 6], [7, 1, 8], [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9], [4, 9, 5],
    [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]])


def icosphere(subdiv: int):
    """Unit-sphere geodesic mesh: icosahedron subdivided `subdiv` times. Returns vertices, faces."""
    V = _ICO_V / np.linalg.norm(_ICO_V, axis=1, keepdims=True)
    F = _ICO_F.copy()
    for _ in range(subdiv):
        cache = {}
        Vl = list(V)
        newF = []

        def mid(a, b):
            key = (min(a, b), max(a, b))
            if key in cache:
                return cache[key]
            m = V[a] + V[b]
            m /= np.linalg.norm(m)
            Vl.append(m)
            cache[key] = len(Vl) - 1
            return cache[key]

        for a, b, c in F:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            newF += [[a, ab, ca], [b, bc, ab], [c, ca, bc], [ab, bc, ca]]
        V = np.array(Vl)
        F = np.array(newF)
    return V, F


def build_laplacian(V, F):
    """Random-walk graph Laplacian (Lap u = mean(neighbours) - u) and the adjacency matrix."""
    edges = set()
    for a, b, c in F:
        for i, j in ((a, b), (b, c), (c, a)):
            edges.add((min(i, j), max(i, j)))
    e = np.array(list(edges))
    n = len(V)
    rows = np.concatenate([e[:, 0], e[:, 1]])
    cols = np.concatenate([e[:, 1], e[:, 0]])
    A = sparse.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)).tocsr()
    deg = np.asarray(A.sum(1)).ravel()
    L = sparse.diags(1.0 / deg) @ A - sparse.eye(n)
    return L.tocsr(), A


@dataclass(frozen=True)
class TuringSphereConfig:
    subdiv: int = 5
    Du: float = 0.16
    Dv: float = 0.08
    F: float = 0.0367      # mitosis/spots regime by default
    k: float = 0.0649
    steps: int = 12000
    n_seeds: int = 12
    seed_radius: float = 0.12
    seed: int = 0


def run(cfg: TuringSphereConfig):
    """Run Gray-Scott on the icosphere. Returns u, v fields, mesh, adjacency."""
    V, Fc = icosphere(cfg.subdiv)
    L, A = build_laplacian(V, Fc)
    n = len(V)
    rng = np.random.default_rng(cfg.seed)
    u = np.ones(n)
    v = np.zeros(n)
    for _ in range(cfg.n_seeds):
        c = rng.integers(n)
        m = np.linalg.norm(V - V[c], axis=1) < cfg.seed_radius
        u[m] = 0.5
        v[m] = 0.25
    for _ in range(cfg.steps):
        uvv = u * v * v
        u = u + (cfg.Du * (L @ u) - uvv + cfg.F * (1.0 - u))
        v = v + (cfg.Dv * (L @ v) + uvv - (cfg.F + cfg.k) * v)
    return {"u": u, "v": v, "V": V, "F": Fc, "A": A}


def count_spots(v, A, thresh: float = 0.2) -> int:
    """Number of connected high-concentration domains (pattern features) on the mesh."""
    hi = v > thresh
    if hi.sum() == 0:
        return 0
    n, _ = connected_components(A[hi][:, hi], directed=False)
    return int(n)
