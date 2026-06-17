"""R29 — open-ended navigation: quality-diversity in an obstacle field.

R28 illuminated movement *styles* in empty space. Here the arena has walls, the
creature SENSES the nearest obstacle, and its behavior characterization is simply
where it ends up. MAP-Elites now has to discover trajectories that weave around
obstacles to reach every part of the arena — including the cells in the "shadow"
directly behind an obstacle, which a straight-line objective can never reach. The
coverage map literally takes the shape of the obstacle field: quality-diversity
discovers the routes; objective-only search collapses onto one.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from alife.brain import BrainSpec, forward, mutate_brains, random_brains

N_IN = 6   # [sin(phase), cos(phase), vx, vy, obstacle_dx, obstacle_dy]
N_OUT = 2  # acceleration


def _default_obstacles():
    # (cx, cy, r) — a triangular ring of pillars around a clear origin, where
    # creatures spawn; they must navigate out and around to fill the arena.
    return ((0.0, 30.0, 12.0), (30.0, -16.0, 12.0), (-30.0, -16.0, 12.0),
            (0.0, -34.0, 9.0))


@dataclass(frozen=True)
class NavConfig:
    steps: int = 70
    dt: float = 1.0
    max_speed: float = 1.0
    period: float = 22.0
    n_hidden: int = 10
    reach: float = 55.0
    grid: int = 30
    batch: int = 128
    iters: int = 500
    mut_rate: float = 0.3
    mut_sigma: float = 0.5
    obstacles: tuple = field(default_factory=_default_obstacles)


def _spec(cfg: NavConfig) -> BrainSpec:
    return BrainSpec(N_IN, cfg.n_hidden, N_OUT)


def _obstacle_sense(pos: np.ndarray, obs: np.ndarray):
    """For each creature, unit vector to nearest obstacle surface scaled by proximity.
    pos:(B,2), obs:(K,3) -> sense:(B,2), and a collision-resolved position helper."""
    d = pos[:, None, :] - obs[None, :, :2]           # (B,K,2) creature - center
    dist = np.linalg.norm(d, axis=2)                  # (B,K)
    surf = dist - obs[None, :, 2]                      # distance to surface
    k = np.argmin(surf, axis=1)                        # nearest obstacle per creature
    b = np.arange(pos.shape[0])
    near_d = d[b, k]                                   # (B,2) vector from center
    near_dist = dist[b, k] + 1e-9
    prox = 1.0 / (1.0 + np.maximum(surf[b, k], 0.0))   # 1 near, ->0 far
    sense = -(near_d / near_dist[:, None]) * prox[:, None]  # points TOWARD obstacle
    return sense


def _resolve_collisions(pos: np.ndarray, obs: np.ndarray) -> np.ndarray:
    """Push any creature inside an obstacle out to its surface (slide)."""
    for k in range(obs.shape[0]):
        c = obs[k, :2]; r = obs[k, 2]
        d = pos - c
        dist = np.linalg.norm(d, axis=1)
        inside = dist < r
        if np.any(inside):
            safe = np.maximum(dist[inside], 1e-9)
            pos[inside] = c + d[inside] / safe[:, None] * r
    return pos


def simulate(w: np.ndarray, cfg: NavConfig):
    """Batched rollout with sensing + collisions. -> (final_xy, displacement, path_len)."""
    spec = _spec(cfg)
    obs = np.array(cfg.obstacles, dtype=float)
    B = w.shape[0]
    pos = np.zeros((B, 2)); vel = np.zeros((B, 2)); path = np.zeros(B)
    for t in range(cfg.steps):
        ph = 2 * np.pi * t / cfg.period
        clk = np.tile([np.sin(ph), np.cos(ph)], (B, 1))
        sense = _obstacle_sense(pos, obs)
        x = np.concatenate([clk, vel, sense], axis=1)
        acc = np.tanh(forward(w, spec, x))
        vel = vel + acc * cfg.dt
        spd = np.linalg.norm(vel, axis=1, keepdims=True)
        vel = np.where(spd > cfg.max_speed, vel / spd * cfg.max_speed, vel)
        new = pos + vel * cfg.dt
        new = _resolve_collisions(new, obs)
        path += np.linalg.norm(new - pos, axis=1)
        pos = new
    disp = np.linalg.norm(pos, axis=1)
    return pos, disp, path


def _cells(pos: np.ndarray, cfg: NavConfig) -> np.ndarray:
    g = cfg.grid
    norm = (pos + cfg.reach) / (2 * cfg.reach)
    ij = np.clip((norm * g).astype(int), 0, g - 1)
    return ij[:, 0] * g + ij[:, 1]


def _quality(disp: np.ndarray, path: np.ndarray) -> np.ndarray:
    return disp / (path + 1e-9)        # efficiency: how directly it reached the cell


def reachable_mask(cfg: NavConfig) -> np.ndarray:
    """Grid cells whose centers are not inside an obstacle (the navigable space)."""
    g = cfg.grid
    centers = (np.arange(g) + 0.5) / g * (2 * cfg.reach) - cfg.reach
    gx, gy = np.meshgrid(centers, centers, indexing="ij")
    free = np.ones((g, g), dtype=bool)
    for cx, cy, r in cfg.obstacles:
        free &= (gx - cx) ** 2 + (gy - cy) ** 2 > r ** 2
    return free


def map_elites(cfg: NavConfig, seed: int = 0):
    rng = np.random.default_rng(seed)
    spec = _spec(cfg)
    archive: dict[int, tuple] = {}
    coverage = []
    w = random_brains(cfg.batch, spec, rng)
    for it in range(cfg.iters):
        if archive and it > 0:
            genomes = np.array([archive[c][1] for c in archive])
            w = mutate_brains(genomes[rng.integers(0, len(genomes), cfg.batch)],
                              rng, cfg.mut_rate, cfg.mut_sigma)
        pos, disp, path = simulate(w, cfg)
        cells = _cells(pos, cfg)
        qual = _quality(disp, path)
        for b in range(cfg.batch):
            c = int(cells[b])
            if c not in archive or qual[b] > archive[c][0]:
                archive[c] = (float(qual[b]), w[b].copy(), pos[b].copy())
        coverage.append(len(archive))
    return archive, np.array(coverage)


def objective_ga(cfg: NavConfig, seed: int = 0):
    rng = np.random.default_rng(seed)
    spec = _spec(cfg)
    w = random_brains(cfg.batch, spec, rng)
    coverage = []; seen: set[int] = set(); pos = None
    for _ in range(cfg.iters):
        pos, disp, path = simulate(w, cfg)
        seen.update(int(c) for c in _cells(pos, cfg))
        coverage.append(len(seen))
        order = np.argsort(disp)[::-1]
        elite = w[order[: max(1, cfg.batch // 10)]]
        parents = w[order[: max(2, cfg.batch // 3)]]
        kids = mutate_brains(parents[rng.integers(0, parents.shape[0], cfg.batch - elite.shape[0])],
                             rng, cfg.mut_rate, cfg.mut_sigma)
        w = np.vstack([elite, kids])
    return pos, np.array(coverage)


def archive_trajectory(genome: np.ndarray, cfg: NavConfig) -> np.ndarray:
    spec = _spec(cfg)
    obs = np.array(cfg.obstacles, dtype=float)
    w = genome[None, :]
    pos = np.zeros((1, 2)); vel = np.zeros((1, 2))
    traj = [pos[0].copy()]
    for t in range(cfg.steps):
        ph = 2 * np.pi * t / cfg.period
        sense = _obstacle_sense(pos, obs)
        x = np.concatenate([np.tile([np.sin(ph), np.cos(ph)], (1, 1)), vel, sense], axis=1)
        acc = np.tanh(forward(w, spec, x))
        vel = vel + acc * cfg.dt
        spd = np.linalg.norm(vel, axis=1, keepdims=True)
        vel = np.where(spd > cfg.max_speed, vel / spd * cfg.max_speed, vel)
        pos = _resolve_collisions(pos + vel * cfg.dt, obs)
        traj.append(pos[0].copy())
    return np.array(traj)
