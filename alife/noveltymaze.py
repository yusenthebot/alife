"""R30 — novelty search beats the objective on a deceptive maze.

The famous Lehman & Stanley (2011) result. The goal sits just above a U-shaped
trap whose mouth faces the start. Rewarding progress toward the goal (minimizing
distance) drives creatures straight into the trap and pins them at the dead-end
wall — the objective is *deceptive*. Rewarding pure behavioral novelty (end up
somewhere no one has been, with NO knowledge of the goal) instead explores the
whole maze and stumbles out around the trap to the goal.

Same controller, same arena, same mutation — only the selection pressure differs:
"reach the goal" fails; "be different" succeeds.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from alife.brain import BrainSpec, forward, mutate_brains, random_brains

N_IN = 6   # [sin(phase), cos(phase), vx, vy, wall_dx, wall_dy]
N_OUT = 2


def _trap_walls():
    """Boxes (cx, cy, hw, hh): a U opening downward toward the start, goal above it."""
    return ((-13.0, 9.0, 2.0, 16.0),    # left arm
            (13.0, 9.0, 2.0, 16.0),     # right arm
            (0.0, 25.0, 15.0, 2.0))     # top bar (closes the U)


@dataclass(frozen=True)
class MazeConfig:
    steps: int = 140
    dt: float = 1.0
    max_speed: float = 1.0
    period: float = 24.0
    n_hidden: int = 12
    reach: float = 50.0
    start: tuple = (0.0, -38.0)
    goal: tuple = (0.0, 34.0)
    goal_radius: float = 6.0
    pop: int = 200
    generations: int = 250
    k: int = 15            # novelty = mean distance to k nearest prior behaviors
    mut_rate: float = 0.3
    mut_sigma: float = 0.5
    walls: tuple = field(default_factory=_trap_walls)


def _spec(cfg: MazeConfig) -> BrainSpec:
    return BrainSpec(N_IN, cfg.n_hidden, N_OUT)


def _closest_points(pos: np.ndarray, boxes: np.ndarray):
    """For each creature, vector to nearest box surface, scaled by proximity. (B,2)."""
    cx, cy, hw, hh = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    px = np.clip(pos[:, None, 0], cx - hw, cx + hw)   # (B,K) closest x on each box
    py = np.clip(pos[:, None, 1], cy - hh, cy + hh)
    dx = px - pos[:, None, 0]; dy = py - pos[:, None, 1]
    dist = np.sqrt(dx * dx + dy * dy)                  # (B,K)
    k = np.argmin(dist, axis=1)
    b = np.arange(pos.shape[0])
    nd = dist[b, k] + 1e-9
    prox = 1.0 / (1.0 + nd)
    return np.stack([dx[b, k] / nd * prox, dy[b, k] / nd * prox], axis=1)


def _resolve(pos: np.ndarray, boxes: np.ndarray) -> np.ndarray:
    """Push any creature inside a box out along the min-penetration axis."""
    for k in range(boxes.shape[0]):
        cx, cy, hw, hh = boxes[k]
        dx = pos[:, 0] - cx; dy = pos[:, 1] - cy
        inside = (np.abs(dx) < hw) & (np.abs(dy) < hh)
        if not np.any(inside):
            continue
        pen_x = hw - np.abs(dx); pen_y = hh - np.abs(dy)
        push_x = inside & (pen_x <= pen_y)
        push_y = inside & (pen_x > pen_y)
        pos[push_x, 0] = cx + np.sign(dx[push_x]) * hw
        pos[push_y, 1] = cy + np.sign(dy[push_y]) * hh
    return pos


def simulate(w: np.ndarray, cfg: MazeConfig):
    """Rollout from the start. -> (end_xy:(B,2), min_dist_to_goal:(B,))."""
    spec = _spec(cfg)
    boxes = np.array(cfg.walls, dtype=float)
    goal = np.array(cfg.goal)
    B = w.shape[0]
    pos = np.tile(cfg.start, (B, 1)).astype(float)
    vel = np.zeros((B, 2))
    mind = np.full(B, np.inf)
    for t in range(cfg.steps):
        ph = 2 * np.pi * t / cfg.period
        clk = np.tile([np.sin(ph), np.cos(ph)], (B, 1))
        sense = _closest_points(pos, boxes)
        x = np.concatenate([clk, vel, sense], axis=1)
        acc = np.tanh(forward(w, spec, x))
        vel = vel + acc * cfg.dt
        spd = np.linalg.norm(vel, axis=1, keepdims=True)
        vel = np.where(spd > cfg.max_speed, vel / spd * cfg.max_speed, vel)
        pos = _resolve(np.clip(pos + vel * cfg.dt, -cfg.reach, cfg.reach), boxes)
        mind = np.minimum(mind, np.linalg.norm(pos - goal, axis=1))
    return pos, mind


def _novelty(behaviors: np.ndarray, reference: np.ndarray, k: int) -> np.ndarray:
    """Mean distance from each behavior to its k nearest neighbors in `reference`."""
    d = np.linalg.norm(behaviors[:, None, :] - reference[None, :, :], axis=2)
    kk = min(k, reference.shape[0])
    nn = np.sort(d, axis=1)[:, :kk]
    return nn.mean(axis=1)


def _evolve(cfg: MazeConfig, novelty: bool, seed: int = 0):
    rng = np.random.default_rng(seed)
    spec = _spec(cfg)
    w = random_brains(cfg.pop, spec, rng)
    archive = np.empty((0, 2))
    best_dist_hist = []
    reached_gen = None
    final_beh = None
    for g in range(cfg.generations):
        beh, mind = simulate(w, cfg)
        final_beh = beh
        best_dist_hist.append(float(mind.min()))
        if reached_gen is None and mind.min() <= cfg.goal_radius:
            reached_gen = g
        if novelty:
            ref = np.vstack([archive, beh]) if archive.size else beh
            score = _novelty(beh, ref, cfg.k)
            # grow the archive with a sample of this generation's behaviors
            take = rng.choice(cfg.pop, size=max(1, cfg.pop // 20), replace=False)
            archive = np.vstack([archive, beh[take]])
        else:
            # objective: minimize distance from the FINAL position to the goal.
            # (Scoring the final position, not the trajectory min, is what makes the
            # trap deceptive: ending at the dead-end wall is a strong local optimum.)
            score = -np.linalg.norm(beh - np.array(cfg.goal), axis=1)
        order = np.argsort(score)[::-1]
        elite = w[order[: max(1, cfg.pop // 10)]]
        parents = w[order[: max(2, cfg.pop // 3)]]
        kids = mutate_brains(parents[rng.integers(0, parents.shape[0], cfg.pop - elite.shape[0])],
                             rng, cfg.mut_rate, cfg.mut_sigma)
        w = np.vstack([elite, kids])
    return {
        "best_dist": np.array(best_dist_hist),
        "reached_gen": reached_gen,
        "final_behaviors": final_beh,
        "archive": archive,
        "final_pop": w,
    }


def novelty_search(cfg: MazeConfig, seed: int = 0):
    return _evolve(cfg, novelty=True, seed=seed)


def objective_search(cfg: MazeConfig, seed: int = 0):
    return _evolve(cfg, novelty=False, seed=seed)


def trajectory(genome: np.ndarray, cfg: MazeConfig) -> np.ndarray:
    spec = _spec(cfg)
    boxes = np.array(cfg.walls, dtype=float)
    w = genome[None, :]
    pos = np.array([cfg.start], dtype=float)
    vel = np.zeros((1, 2))
    traj = [pos[0].copy()]
    for t in range(cfg.steps):
        ph = 2 * np.pi * t / cfg.period
        sense = _closest_points(pos, boxes)
        x = np.concatenate([np.tile([np.sin(ph), np.cos(ph)], (1, 1)), vel, sense], axis=1)
        acc = np.tanh(forward(w, spec, x))
        vel = vel + acc * cfg.dt
        spd = np.linalg.norm(vel, axis=1, keepdims=True)
        vel = np.where(spd > cfg.max_speed, vel / spd * cfg.max_speed, vel)
        pos = _resolve(np.clip(pos + vel * cfg.dt, -cfg.reach, cfg.reach), boxes)
        traj.append(pos[0].copy())
    return np.array(traj)


def reached(result, cfg: MazeConfig) -> bool:
    return result["reached_gen"] is not None
