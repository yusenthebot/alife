"""Evolution in 3D: evolved foraging brains that fly through a volume.

R3's generational GA, lifted into three dimensions. Each creature senses the
nearest food in its OWN body frame (is it left/right, up/down, ahead/behind, and
how close) and outputs a body-frame acceleration (steer + climb/dive + thrust).
The genome is the network's weights; selection (food foraged) turns random 3D
nets into competent 3D foragers — verified on a held-out food field, then flown
through the GPU renderer as a living 3D ecosystem.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import brain
from .brain import BrainSpec
from .world3d import World3D

N_IN = 5    # nearest-food body-dir (3) * proximity, proximity, energy
N_OUT = 3   # body-frame acceleration (right, up, fwd)


@dataclass(frozen=True)
class Forage3DConfig:
    world: World3D = None
    n_food: int = 320
    food_regrow: int = 12
    sense_range: float = 34.0
    eat_radius: float = 3.0
    max_speed: float = 2.6
    min_speed: float = 0.8
    max_force: float = 0.35
    pop: int = 150
    generations: int = 45
    eval_steps: int = 300
    elite_frac: float = 0.35
    mut_rate: float = 0.22
    mut_sigma: float = 0.3


def spec() -> BrainSpec:
    return BrainSpec(n_in=N_IN, n_hidden=10, n_out=N_OUT)


def _body_frame(vel: np.ndarray):
    fwd = vel / np.maximum(np.linalg.norm(vel, axis=1, keepdims=True), 1e-9)
    up_ref = np.tile([0.0, 0.0, 1.0], (fwd.shape[0], 1))
    up_ref[np.abs(fwd[:, 2]) > 0.9] = [0.0, 1.0, 0.0]
    right = np.cross(up_ref, fwd)
    right /= np.maximum(np.linalg.norm(right, axis=1, keepdims=True), 1e-9)
    up = np.cross(fwd, right)
    return right, up, fwd


def _limit_speed(v, lo, hi):
    n = np.linalg.norm(v, axis=1, keepdims=True)
    return np.where(n > 1e-9, v / np.maximum(n, 1e-9) * np.clip(n, lo, hi), v)


def _sense(world, pos, vel, food, alive, cfg):
    """Body-frame sensory vector (P, 5) for the nearest visible food."""
    right, up, fwd = _body_frame(vel)
    rel = food - pos[:, None, :]                         # (P, F, 3)
    d2 = np.where(alive, np.einsum("pfk,pfk->pf", rel, rel), np.inf)
    nearest = rel[np.arange(pos.shape[0]), d2.argmin(1)]  # (P, 3)
    dist = np.sqrt(d2.min(1))
    unit = nearest / np.maximum(np.linalg.norm(nearest, axis=1, keepdims=True), 1e-9)
    prox = np.where(dist < cfg.sense_range, 1.0 - dist / cfg.sense_range, 0.0)
    bx = (unit * right).sum(1) * prox
    by = (unit * up).sum(1) * prox
    bz = (unit * fwd).sum(1) * prox
    return np.stack([bx, by, bz, prox, np.full(pos.shape[0], 0.5)], axis=1), right, up, fwd


def _act(out, right, up, fwd, vel, cfg):
    accel = (right * out[:, 0:1] + up * out[:, 1:2] + fwd * out[:, 2:3]) * cfg.max_force
    return _limit_speed(vel + accel, cfg.min_speed, cfg.max_speed)


def batch_forage3d(brains, sp, cfg, steps, seed, record=False):
    """Each brain alone in its own 3D food field. Returns fitness (P,), or a
    rollout dict if record=True (single brain expected)."""
    rng = np.random.default_rng(seed)
    world = cfg.world
    p = brains.shape[0]
    layout = rng.uniform(0, world.size, size=(cfg.n_food, 3))
    food = np.repeat(layout[None], p, axis=0)
    alive = np.ones((p, cfg.n_food), dtype=bool)
    pos = rng.uniform(world.size * 0.3, world.size * 0.7, size=(p, 3))
    d = rng.normal(size=(p, 3))
    vel = d / np.linalg.norm(d, axis=1, keepdims=True) * cfg.max_speed
    fitness = np.zeros(p)
    regrow_p = cfg.food_regrow / cfg.n_food
    rows = np.arange(p)
    frames = []

    for _ in range(steps):
        x, right, up, fwd = _sense(world, pos, vel, food, alive, cfg)
        vel = _act(brain.forward(brains, sp, x), right, up, fwd, vel, cfg)
        pos = world.clamp(pos + vel)
        rel = food - pos[:, None, :]
        d2 = np.where(alive, np.einsum("pfk,pfk->pf", rel, rel), np.inf)
        nearest = d2.argmin(1)
        ate = d2[rows, nearest] < cfg.eat_radius ** 2
        fitness += ate
        alive[rows[ate], nearest[ate]] = False
        revive = (~alive) & (rng.random((p, cfg.n_food)) < regrow_p)
        if revive.any():
            food[revive] = rng.uniform(0, world.size, size=(int(revive.sum()), 3))
            alive[revive] = True
        if record:
            frames.append({"pos": pos.copy(), "vel": vel.copy(),
                           "food": food[0][alive[0]].copy()})
    return frames if record else fitness


def rollout3d_shared(brains, sp, cfg, steps, seed, capture_every=2):
    """N evolved foragers in ONE shared 3D world with shared food. Records frames
    (pos, vel, food) for the living-ecosystem render."""
    rng = np.random.default_rng(seed)
    world = cfg.world
    n = brains.shape[0]
    food = rng.uniform(0, world.size, size=(cfg.n_food, 3))
    pos = rng.uniform(world.size * 0.2, world.size * 0.8, size=(n, 3))
    d = rng.normal(size=(n, 3))
    vel = d / np.linalg.norm(d, axis=1, keepdims=True) * cfg.max_speed
    frames = []
    for t in range(steps):
        alive = np.ones((n, food.shape[0]), dtype=bool)
        x, right, up, fwd = _sense(world, pos, vel, np.repeat(food[None], n, 0), alive, cfg)
        vel = _act(brain.forward(brains, sp, x), right, up, fwd, vel, cfg)
        pos = world.clamp(pos + vel)
        if food.shape[0]:
            rel = food[None] - pos[:, None, :]
            fd2 = np.einsum("nfk,nfk->nf", rel, rel)
            eaten = fd2.min(0) < cfg.eat_radius ** 2
            if eaten.any():
                food = food[~eaten]
            need = cfg.food_regrow if food.shape[0] < cfg.n_food else 0
            if need:
                food = np.vstack([food, rng.uniform(0, world.size, size=(min(need, cfg.n_food - food.shape[0]), 3))])
        if t % capture_every == 0:
            frames.append({"pos": pos.copy(), "vel": vel.copy(), "food": food.copy()})
    return frames


def evolve3d(cfg, seed=0):
    rng = np.random.default_rng(seed)
    sp = spec()
    brains = brain.random_brains(cfg.pop, sp, rng)
    gen0 = brains.copy()
    n_elite = max(1, int(cfg.pop * cfg.elite_frac))
    hist = []
    for g in range(cfg.generations):
        fit = batch_forage3d(brains, sp, cfg, cfg.eval_steps, seed=1000 + g)
        hist.append((g, float(fit.mean()), float(fit.max())))
        elite = brains[np.argsort(fit)[::-1][:n_elite]]
        parents = elite[rng.integers(0, n_elite, cfg.pop - n_elite)]
        brains = np.vstack([elite, brain.mutate_brains(parents, rng, cfg.mut_rate, cfg.mut_sigma)])
    return brains, np.array(hist), gen0, sp
