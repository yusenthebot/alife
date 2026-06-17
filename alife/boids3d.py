"""Vectorized 3D Boids — Reynolds flocking lifted into three dimensions.

The three rules (separation, alignment, cohesion) are identical to the 2D
version; only the vectors gain a z-component. A boundary push keeps the flock
inside the arena. The result is a 3D murmuration: the same emergent order as R1,
now wheeling through volume.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .boids import _limit, _limit_speed, _set_mag
from .world3d import World3D


@dataclass(frozen=True)
class Boid3DParams:
    perception: float = 16.0
    separation: float = 6.0
    w_sep: float = 1.8
    w_ali: float = 1.05
    w_coh: float = 0.95
    w_bound: float = 1.4
    max_speed: float = 2.4
    min_speed: float = 0.8
    max_force: float = 0.3
    margin: float = 18.0


def _steer(desired_dir: np.ndarray, vel: np.ndarray, p: Boid3DParams) -> np.ndarray:
    return _limit(_set_mag(desired_dir, p.max_speed) - vel, p.max_force)


def step(world: World3D, p: Boid3DParams, pos: np.ndarray, vel: np.ndarray):
    n = pos.shape[0]
    diff = world.pairwise_delta(pos)                       # (N, N, 3)
    dist2 = np.einsum("ijk,ijk->ij", diff, diff)
    idx = np.arange(n)
    dist2[idx, idx] = np.inf
    perceived = dist2 < p.perception ** 2
    close = dist2 < p.separation ** 2
    cnt = perceived.sum(1, keepdims=True)
    has_n = cnt[:, 0] > 0
    has_close = close.any(1)

    coh = (diff * perceived[..., None]).sum(1) / np.maximum(cnt, 1)
    avg_vel = (vel[None] * perceived[..., None]).sum(1) / np.maximum(cnt, 1)
    weight = np.where(close, 1.0 / np.maximum(np.sqrt(dist2), 1e-6), 0.0)
    sep = -(diff * weight[..., None]).sum(1)

    accel = (p.w_coh * _steer(coh, vel, p) * has_n[:, None]
             + p.w_ali * _steer(avg_vel, vel, p) * has_n[:, None]
             + p.w_sep * _steer(sep, vel, p) * has_close[:, None]
             + p.w_bound * world.boundary_push(pos, p.margin, p.max_force))

    vel2 = _limit_speed(vel + accel, p.min_speed, p.max_speed)
    pos2 = world.clamp(pos + vel2)
    return pos2, vel2


def spawn(world: World3D, n: int, p: Boid3DParams, rng: np.random.Generator):
    pos = rng.uniform(world.size * 0.25, world.size * 0.75, size=(n, 3))
    d = rng.normal(size=(n, 3))
    d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
    return pos, d * 0.5 * (p.min_speed + p.max_speed)


def order_parameter(vel: np.ndarray) -> float:
    u = vel / np.maximum(np.linalg.norm(vel, axis=1, keepdims=True), 1e-9)
    return float(np.linalg.norm(u.mean(axis=0)))
