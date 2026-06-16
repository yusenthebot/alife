"""Vectorized Reynolds Boids.

Three classic local rules — separation, alignment, cohesion — produce global
flocking with no leader and no central control. Everything is computed as
batched numpy over an (N, N) neighbor tensor, so a step is a handful of array
ops rather than a Python loop over agents.

This is the substrate the ecosystem evolves on: in later rounds the fixed
weights below become a per-individual genome, and the hand-written rules become
a neural-network brain. Keeping `step` a pure function of (state, params) makes
that swap local.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .world import World


@dataclass(frozen=True)
class BoidParams:
    perception: float = 14.0   # radius for alignment + cohesion
    separation: float = 5.5    # radius for personal-space repulsion
    w_sep: float = 1.7         # rule weights
    w_ali: float = 1.05
    w_coh: float = 0.95
    max_speed: float = 2.6
    min_speed: float = 0.9
    max_force: float = 0.28    # per-step steering clamp


def _set_mag(v: np.ndarray, mag: float) -> np.ndarray:
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return np.where(n > 1e-9, v / np.maximum(n, 1e-9) * mag, 0.0)


def _limit(v: np.ndarray, mag: float) -> np.ndarray:
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    factor = np.where(n > mag, mag / np.maximum(n, 1e-9), 1.0)
    return v * factor


def _limit_speed(v: np.ndarray, lo: float, hi: float) -> np.ndarray:
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    clamped = np.clip(n, lo, hi)
    return np.where(n > 1e-9, v / np.maximum(n, 1e-9) * clamped, v)


def _steer(desired_dir: np.ndarray, vel: np.ndarray, p: BoidParams) -> np.ndarray:
    """Reynolds steering: accelerate toward a desired velocity, force-limited."""
    desired = _set_mag(desired_dir, p.max_speed)
    return _limit(desired - vel, p.max_force)


def step(world: World, p: BoidParams, pos: np.ndarray, vel: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Advance one tick. Pure: returns new (pos, vel), never mutates inputs."""
    n = pos.shape[0]
    diff = world.pairwise_delta(pos)                 # (N, N, 2): diff[i,j] = j - i
    dist2 = np.einsum("ijk,ijk->ij", diff, diff)     # (N, N)
    idx = np.arange(n)
    dist2[idx, idx] = np.inf                          # exclude self

    perceived = dist2 < p.perception ** 2
    close = dist2 < p.separation ** 2
    cnt = perceived.sum(1, keepdims=True)
    has_n = cnt[:, 0] > 0
    has_close = close.any(1)

    # Cohesion: head toward the local centroid (mean relative offset).
    coh = (diff * perceived[..., None]).sum(1) / np.maximum(cnt, 1)
    # Alignment: match the mean heading of perceived neighbors.
    avg_vel = (vel[None] * perceived[..., None]).sum(1) / np.maximum(cnt, 1)
    # Separation: push away from crowding neighbors, stronger the closer they are.
    dist = np.sqrt(dist2)
    weight = np.where(close, 1.0 / np.maximum(dist, 1e-6), 0.0)
    sep = -(diff * weight[..., None]).sum(1)

    coh_s = _steer(coh, vel, p) * has_n[:, None]
    ali_s = _steer(avg_vel, vel, p) * has_n[:, None]
    sep_s = _steer(sep, vel, p) * has_close[:, None]

    accel = p.w_coh * coh_s + p.w_ali * ali_s + p.w_sep * sep_s
    vel2 = _limit_speed(vel + accel, p.min_speed, p.max_speed)
    pos2 = world.wrap(pos + vel2)
    return pos2, vel2


def spawn(world: World, n: int, p: BoidParams, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Random initial swarm: uniform positions, random headings at cruise speed."""
    pos = rng.uniform([0, 0], world.size, size=(n, 2))
    angle = rng.uniform(0, 2 * np.pi, size=n)
    speed = 0.5 * (p.min_speed + p.max_speed)
    vel = np.stack([np.cos(angle), np.sin(angle)], axis=1) * speed
    return pos, vel
