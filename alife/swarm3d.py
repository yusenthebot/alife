"""Large-scale 3D flocking via a spatial index (breaks the O(N²) ceiling).

The earlier boids compute a full (N,N) neighbor tensor — fine to ~2k agents,
hopeless beyond. Here a KD-tree returns only the pairs actually within
perception range, so the cost scales ~O(N log N) and tens of thousands of
creatures flock in real-ish time. Same Reynolds rules (separation · alignment ·
cohesion) + boundary push; the emergent order is identical, the murmuration just
gets vast and dense.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree

from .boids import _limit, _limit_speed, _set_mag
from .world3d import World3D


@dataclass(frozen=True)
class Swarm3DParams:
    perception: float = 9.0
    separation: float = 4.0
    w_sep: float = 1.8
    w_ali: float = 1.05
    w_coh: float = 0.95
    w_bound: float = 1.4
    max_speed: float = 2.2
    min_speed: float = 0.8
    max_force: float = 0.3
    margin: float = 14.0


def step(world: World3D, p: Swarm3DParams, pos: np.ndarray, vel: np.ndarray):
    n = pos.shape[0]
    tree = cKDTree(pos)
    pairs = tree.query_pairs(p.perception, output_type="ndarray")  # (M,2), i<j

    sum_pos = np.zeros((n, 3))
    sum_vel = np.zeros((n, 3))
    cnt = np.zeros((n, 1))
    sep = np.zeros((n, 3))

    if pairs.shape[0]:
        i, j = pairs[:, 0], pairs[:, 1]
        d = pos[j] - pos[i]                                # i -> j
        dist = np.maximum(np.linalg.norm(d, axis=1), 1e-6)
        np.add.at(sum_pos, i, pos[j]); np.add.at(sum_pos, j, pos[i])
        np.add.at(sum_vel, i, vel[j]); np.add.at(sum_vel, j, vel[i])
        np.add.at(cnt, i, 1.0); np.add.at(cnt, j, 1.0)
        close = dist < p.separation
        if close.any():
            ic, jc = i[close], j[close]
            push = (d[close] / dist[close, None] ** 2)
            np.add.at(sep, ic, -push); np.add.at(sep, jc, push)

    has = (cnt[:, 0] > 0)
    centroid = np.where(cnt > 0, sum_pos / np.maximum(cnt, 1), pos)
    coh = _limit(_set_mag(centroid - pos, p.max_speed) - vel, p.max_force) * has[:, None]
    ali = _limit(_set_mag(sum_vel, p.max_speed) - vel, p.max_force) * has[:, None]
    sep_s = _limit(_set_mag(sep, p.max_speed) - vel, p.max_force)
    bound = world.boundary_push(pos, p.margin, p.max_force)

    accel = p.w_coh * coh + p.w_ali * ali + p.w_sep * sep_s + p.w_bound * bound
    vel2 = _limit_speed(vel + accel, p.min_speed, p.max_speed)
    return world.clamp(pos + vel2), vel2


def spawn(world: World3D, n: int, p: Swarm3DParams, rng: np.random.Generator):
    pos = rng.uniform(world.size * 0.2, world.size * 0.8, size=(n, 3))
    d = rng.normal(size=(n, 3))
    return pos, d / np.linalg.norm(d, axis=1, keepdims=True) * 0.5 * (p.min_speed + p.max_speed)


def order_parameter(vel: np.ndarray) -> float:
    u = vel / np.maximum(np.linalg.norm(vel, axis=1, keepdims=True), 1e-9)
    return float(np.linalg.norm(u.mean(axis=0)))
