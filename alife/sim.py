"""Simulation driver: steps the swarm, records metrics, optionally renders.

Keeps state in plain arrays and yields per-step metrics so callers (CLI, tests)
decide what to do with them. Rendering is injected, not assumed, so the same
loop serves headless test runs and frame capture.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import boids, metrics
from .boids import BoidParams
from .render import Renderer
from .world import World


@dataclass(frozen=True)
class SimConfig:
    n: int = 600
    steps: int = 400
    seed: int = 0
    world: World = field(default_factory=World)
    params: BoidParams = field(default_factory=BoidParams)


@dataclass
class SimResult:
    metrics: dict[str, np.ndarray]   # name -> (steps,) time series
    frames: list[np.ndarray]         # rendered RGB frames (empty if not rendering)
    pos: np.ndarray                  # final positions
    vel: np.ndarray                  # final velocities


def _measure(world: World, pos: np.ndarray, vel: np.ndarray, params: BoidParams) -> dict[str, float]:
    return {
        "order": metrics.order_parameter(vel),
        "rotation": metrics.rotation_order(world, pos, vel),
        "nn_dist": metrics.mean_neighbor_distance(world, pos),
        "clusters": float(metrics.cluster_count(world, pos, params.perception)),
    }


def run(cfg: SimConfig, renderer: Renderer | None = None, capture_every: int = 1) -> SimResult:
    rng = np.random.default_rng(cfg.seed)
    pos, vel = boids.spawn(cfg.world, cfg.n, cfg.params, rng)

    series: dict[str, list[float]] = {}
    frames: list[np.ndarray] = []
    for t in range(cfg.steps):
        m = _measure(cfg.world, pos, vel, cfg.params)
        for key, value in m.items():
            series.setdefault(key, []).append(value)
        if renderer is not None and t % capture_every == 0:
            frames.append(renderer.frame(pos, vel))
        pos, vel = boids.step(cfg.world, cfg.params, pos, vel)

    return SimResult(
        metrics={k: np.asarray(v) for k, v in series.items()},
        frames=frames,
        pos=pos,
        vel=vel,
    )
