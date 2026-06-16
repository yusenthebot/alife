"""Quantitative measures of collective behavior.

Flocking is an *emergent* property — it is not in any single boid, only in the
group. These scalars let us watch it appear in the data, not just on screen:
the order parameter is the standard physics observable for a flocking phase
transition (≈0 disordered, →1 aligned).
"""

from __future__ import annotations

import numpy as np

from .world import World


def order_parameter(vel: np.ndarray) -> float:
    """Polarization φ = |mean unit velocity| ∈ [0, 1]. Vicsek order parameter."""
    units = vel / np.maximum(np.linalg.norm(vel, axis=1, keepdims=True), 1e-9)
    return float(np.linalg.norm(units.mean(axis=0)))


def rotation_order(world: World, pos: np.ndarray, vel: np.ndarray) -> float:
    """Milling measure: normalized angular momentum about the swarm centroid.

    High when the flock circles a common center (a torus/mill), low otherwise.
    """
    centroid = pos.mean(axis=0)
    r = pos - centroid
    if world.toroidal:
        size = world.size
        r -= size * np.round(r / size)
    r_norm = np.maximum(np.linalg.norm(r, axis=1), 1e-9)
    v_unit = vel / np.maximum(np.linalg.norm(vel, axis=1, keepdims=True), 1e-9)
    cross = r[:, 0] * v_unit[:, 1] - r[:, 1] * v_unit[:, 0]
    return float(np.abs((cross / r_norm).mean()))


def mean_neighbor_distance(world: World, pos: np.ndarray) -> float:
    """Average nearest-neighbor distance — how tightly packed the swarm is."""
    d = world.pairwise_delta(pos)
    dist = np.sqrt(np.einsum("ijk,ijk->ij", d, d))
    np.fill_diagonal(dist, np.inf)
    return float(dist.min(axis=1).mean())


def cluster_count(world: World, pos: np.ndarray, radius: float) -> int:
    """Number of connected groups, linking boids within `radius` (union-find)."""
    d = world.pairwise_delta(pos)
    dist2 = np.einsum("ijk,ijk->ij", d, d)
    n = pos.shape[0]
    parent = list(range(n))

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    rows, cols = np.where(np.triu(dist2 < radius ** 2, k=1))
    for i, j in zip(rows.tolist(), cols.tolist()):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj
    return len({find(i) for i in range(n)})
