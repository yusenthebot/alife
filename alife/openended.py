"""R28 — open-endedness: illuminate a behavior space (MAP-Elites / quality-diversity).

Every earlier rung engineered a task to reproduce a *known* result. This is the
first rung that asks the opposite question: not "optimize one objective" but
"discover the whole repertoire of qualitatively different things a creature can
do" — including behaviors I never scripted.

A creature is a point in a 2D arena driven by a small neural controller (its
genome = the network weights). From the origin it produces a trajectory. Its
*behavior characterization* is its movement STYLE — (final heading, path
curviness): does it sprint straight, arc, or spiral, and in which direction? Its
*quality* is how far it travelled. MAP-Elites keeps, for every (heading,
curviness) cell, the farthest-reaching controller of that style — so it fills the
behavior space with a diverse repertoire of gaits, from straight sprinters to
loopy wanderers. A plain objective-only GA (maximize displacement) instead
collapses onto a single style (straight, one direction). Coverage of the behavior
grid is the quality-diversity signal.

Mouret & Clune (2015), "Illuminating search spaces by mapping elites."
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from alife.brain import BrainSpec, forward, mutate_brains, random_brains

N_IN = 4   # [sin(phase), cos(phase), vx, vy]
N_OUT = 2  # acceleration (ax, ay)


@dataclass(frozen=True)
class OpenEndedConfig:
    steps: int = 60
    dt: float = 1.0
    max_speed: float = 1.0
    period: float = 20.0     # clock period for the oscillator inputs
    n_hidden: int = 8
    reach: float = 60.0      # max reachable distance (for normalizing quality)
    curv_max: float = 1.2    # behavior axis: max mean heading-change per step (rad)
    grid: int = 30           # behavior grid resolution per axis
    batch: int = 128
    iters: int = 400
    mut_rate: float = 0.3
    mut_sigma: float = 0.5


def _spec(cfg: OpenEndedConfig) -> BrainSpec:
    return BrainSpec(N_IN, cfg.n_hidden, N_OUT)


def simulate(w: np.ndarray, cfg: OpenEndedConfig):
    """Batched rollout. w:(B,W) -> (final_xy:(B,2), displacement:(B,), curviness:(B,)).
    curviness = mean absolute heading change per step (0=straight, large=loopy)."""
    spec = _spec(cfg)
    B = w.shape[0]
    pos = np.zeros((B, 2))
    vel = np.zeros((B, 2))
    turn = np.zeros(B)
    prev = None
    for t in range(cfg.steps):
        ph = 2 * np.pi * t / cfg.period
        clk = np.tile([np.sin(ph), np.cos(ph)], (B, 1))
        x = np.concatenate([clk, vel], axis=1)
        acc = np.tanh(forward(w, spec, x))          # bounded acceleration
        vel = vel + acc * cfg.dt
        spd = np.linalg.norm(vel, axis=1, keepdims=True)
        vel = np.where(spd > cfg.max_speed, vel / spd * cfg.max_speed, vel)
        if prev is not None:
            cross = prev[:, 0] * vel[:, 1] - prev[:, 1] * vel[:, 0]
            dot = prev[:, 0] * vel[:, 0] + prev[:, 1] * vel[:, 1]
            turn += np.abs(np.arctan2(cross, dot))   # heading change this step
        prev = vel.copy()
        pos = pos + vel * cfg.dt
    disp = np.linalg.norm(pos, axis=1)
    curviness = turn / max(1, cfg.steps - 1)
    return pos, disp, curviness


def _cells(pos: np.ndarray, curv: np.ndarray, cfg: OpenEndedConfig) -> np.ndarray:
    """Map (final heading, curviness) to grid-cell flat index."""
    g = cfg.grid
    ang = (np.arctan2(pos[:, 1], pos[:, 0]) + np.pi) / (2 * np.pi)   # [0,1]
    cv = np.clip(curv / cfg.curv_max, 0, 1 - 1e-9)                   # [0,1)
    ai = np.clip((ang * g).astype(int), 0, g - 1)
    ci = np.clip((cv * g).astype(int), 0, g - 1)
    return ai * g + ci


def _quality(disp: np.ndarray, cfg: OpenEndedConfig) -> np.ndarray:
    """Quality = how far it travelled, normalized to [0,1]."""
    return np.clip(disp / cfg.reach, 0, 1)


def map_elites(cfg: OpenEndedConfig, seed: int = 0):
    """Illuminate the end-location grid. Returns (archive, coverage_history).
    archive: dict cell -> (quality, genome, final_xy)."""
    rng = np.random.default_rng(seed)
    spec = _spec(cfg)
    archive: dict[int, tuple] = {}
    coverage = []
    # seed the archive with a random batch
    w = random_brains(cfg.batch, spec, rng)
    for it in range(cfg.iters):
        if archive and it > 0:
            genomes = np.array([archive[c][1] for c in archive])
            idx = rng.integers(0, len(genomes), cfg.batch)
            w = mutate_brains(genomes[idx], rng, cfg.mut_rate, cfg.mut_sigma)
        pos, disp, curv = simulate(w, cfg)
        cells = _cells(pos, curv, cfg)
        qual = _quality(disp, cfg)
        for b in range(cfg.batch):
            c = int(cells[b])
            if c not in archive or qual[b] > archive[c][0]:
                archive[c] = (float(qual[b]), w[b].copy(), pos[b].copy())
        coverage.append(len(archive))
    return archive, np.array(coverage)


def objective_ga(cfg: OpenEndedConfig, seed: int = 0):
    """Plain objective-only GA: maximize displacement. Returns (final_xy of pop,
    coverage_history) — to contrast collapse vs illumination."""
    rng = np.random.default_rng(seed)
    spec = _spec(cfg)
    w = random_brains(cfg.batch, spec, rng)
    coverage = []
    seen: set[int] = set()
    pos = None
    curv = None
    for _ in range(cfg.iters):
        pos, disp, curv = simulate(w, cfg)
        seen.update(int(c) for c in _cells(pos, curv, cfg))
        coverage.append(len(seen))
        order = np.argsort(disp)[::-1]
        elite = w[order[: max(1, cfg.batch // 10)]]
        parents = w[order[: max(2, cfg.batch // 3)]]
        kids = mutate_brains(parents[rng.integers(0, parents.shape[0], cfg.batch - elite.shape[0])],
                             rng, cfg.mut_rate, cfg.mut_sigma)
        w = np.vstack([elite, kids])
    return pos, curv, np.array(coverage)


def archive_trajectory(genome: np.ndarray, cfg: OpenEndedConfig) -> np.ndarray:
    """Replay one archived genome's full path for visualization. (steps+1, 2)."""
    spec = _spec(cfg)
    w = genome[None, :]
    pos = np.zeros((1, 2)); vel = np.zeros((1, 2))
    traj = [pos[0].copy()]
    for t in range(cfg.steps):
        ph = 2 * np.pi * t / cfg.period
        x = np.concatenate([np.tile([np.sin(ph), np.cos(ph)], (1, 1)), vel], axis=1)
        acc = np.tanh(forward(w, spec, x))
        vel = vel + acc * cfg.dt
        spd = np.linalg.norm(vel, axis=1, keepdims=True)
        vel = np.where(spd > cfg.max_speed, vel / spd * cfg.max_speed, vel)
        pos = pos + vel * cfg.dt
        traj.append(pos[0].copy())
    return np.array(traj)
