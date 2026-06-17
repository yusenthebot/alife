"""Predator–prey co-evolution in 3D — an aerial arms race.

R4's co-evolutionary GA on R8's 3D substrate. Two brain populations evolve at
once in a 3D volume: prey sense food and predators (in their own body frame) and
flee while foraging; predators sense prey and pursue in 3D. Carries R4's hard-won
lessons: a dense pursuit reward so predators get a gradient, prey made more agile
than predators so evasion can pay, and progress measured against the FINAL evolved
opponent (de-confounded) so both sides' escalation is visible despite the Red Queen.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import brain
from .brain import BrainSpec
from .evolve3d import _body_frame
from .world3d import World3D

N_IN = 8     # target-A body-dir(3)*prox + prox, target-B body-dir(3)*prox + prox
N_OUT = 3


def spec() -> BrainSpec:
    return BrainSpec(n_in=N_IN, n_hidden=10, n_out=N_OUT)


@dataclass(frozen=True)
class Coevo3DConfig:
    world: World3D = field(default_factory=lambda: World3D(size=130.0))
    n_prey: int = 170
    n_pred: int = 50
    n_food: int = 280
    episode_steps: int = 320
    generations: int = 50
    elite_frac: float = 0.35
    mut_rate: float = 0.22
    mut_sigma: float = 0.3
    prey_speed: float = 2.5
    pred_speed: float = 2.8
    prey_force: float = 0.5      # prey more agile (can juke in 3D)
    pred_force: float = 0.32
    min_speed: float = 0.7
    sense_range: float = 36.0
    eat_radius: float = 3.0      # prey eats food
    catch_radius: float = 3.4    # predator catches prey
    survival_weight: float = 14.0
    catch_weight: float = 6.0
    pursuit_weight: float = 4.0
    food_regrow: int = 9


def _limit_speed(v, lo, hi):
    n = np.linalg.norm(v, axis=1, keepdims=True)
    return np.where(n > 1e-9, v / np.maximum(n, 1e-9) * np.clip(n, lo, hi), v)


def _sense(world, pos, right, up, fwd, targets, alive, sense_range):
    """Body-frame sensing of the nearest target: (P,4) = [bx,by,bz]*prox, prox."""
    p = pos.shape[0]
    if targets.shape[0] == 0:
        return np.zeros((p, 4))
    rel = targets[None, :, :] - pos[:, None, :]
    d2 = np.einsum("pmk,pmk->pm", rel, rel)
    if alive is not None:
        d2 = np.where(alive[None, :], d2, np.inf)
    nearest = rel[np.arange(p), d2.argmin(1)]
    dist = np.sqrt(d2.min(1))
    unit = nearest / np.maximum(np.linalg.norm(nearest, axis=1, keepdims=True), 1e-9)
    prox = np.where(dist < sense_range, 1.0 - dist / sense_range, 0.0)
    return np.stack([(unit * right).sum(1) * prox, (unit * up).sum(1) * prox,
                     (unit * fwd).sum(1) * prox, prox], axis=1)


def _act(out, right, up, fwd, vel, force, lo, hi):
    accel = (right * out[:, 0:1] + up * out[:, 1:2] + fwd * out[:, 2:3]) * force
    return _limit_speed(vel + accel, lo, hi)


def _spawn(rng, world, n, speed):
    pos = rng.uniform(world.size * 0.15, world.size * 0.85, size=(n, 3))
    d = rng.normal(size=(n, 3))
    return pos, d / np.linalg.norm(d, axis=1, keepdims=True) * speed


def episode3d(prey_w, pred_w, cfg, seed, steps=None, record=False):
    rng = np.random.default_rng(seed)
    world, sp = cfg.world, spec()
    n_steps = cfg.episode_steps if steps is None else steps
    npp, npd = prey_w.shape[0], pred_w.shape[0]
    prey_pos, prey_vel = _spawn(rng, world, npp, cfg.prey_speed)
    pred_pos, pred_vel = _spawn(rng, world, npd, cfg.pred_speed)
    food = rng.uniform(0, world.size, size=(cfg.n_food, 3))
    alive = np.ones(npp, dtype=bool)
    food_eaten = np.zeros(npp)
    survived = np.zeros(npp)
    caught = np.zeros(npd)
    pursuit = np.zeros(npd)
    frames = []

    for _ in range(n_steps):
        pr_r, pr_u, pr_f = _body_frame(prey_vel)
        food_s = _sense(world, prey_pos, pr_r, pr_u, pr_f, food, None, cfg.sense_range)
        pred_s = _sense(world, prey_pos, pr_r, pr_u, pr_f, pred_pos, None, cfg.sense_range)
        prey_vel = _act(brain.forward(prey_w, sp, np.concatenate([food_s, pred_s], 1)),
                        pr_r, pr_u, pr_f, prey_vel, cfg.prey_force, cfg.min_speed, cfg.prey_speed)
        prey_pos = world.clamp(prey_pos + prey_vel)

        pd_r, pd_u, pd_f = _body_frame(pred_vel)
        prey_s = _sense(world, pred_pos, pd_r, pd_u, pd_f, prey_pos, alive, cfg.sense_range)
        pred_vel = _act(brain.forward(pred_w, sp, np.concatenate([prey_s, np.zeros((npd, 4))], 1)),
                        pd_r, pd_u, pd_f, pred_vel, cfg.pred_force, cfg.min_speed, cfg.pred_speed)
        pred_pos = world.clamp(pred_pos + pred_vel)

        if food.shape[0]:
            rel = food[None] - prey_pos[:, None, :]
            fd2 = np.where(alive[:, None], np.einsum("nfk,nfk->nf", rel, rel), np.inf)
            hit = fd2.min(0) < cfg.eat_radius ** 2
            if hit.any():
                np.add.at(food_eaten, fd2.argmin(0)[hit], 1.0)
                food = food[~hit]
            need = min(cfg.food_regrow, cfg.n_food - food.shape[0])
            if need > 0:
                food = np.vstack([food, rng.uniform(0, world.size, size=(need, 3))])

        if alive.any():
            pr = prey_pos[None] - pred_pos[:, None, :]
            pd2 = np.where(alive[None, :], np.einsum("pmk,pmk->pm", pr, pr), np.inf)
            nearest = pd2.argmin(1)
            nd = np.sqrt(pd2[np.arange(npd), nearest])
            pursuit += np.where(nd < cfg.sense_range, 1.0 - nd / cfg.sense_range, 0.0)
            for p in np.where(nd < cfg.catch_radius)[0]:
                if alive[nearest[p]]:
                    alive[nearest[p]] = False
                    caught[p] += 1.0
        survived += alive
        if record:
            frames.append({"prey_pos": prey_pos[alive].copy(), "prey_vel": prey_vel[alive].copy(),
                           "pred_pos": pred_pos.copy(), "pred_vel": pred_vel.copy(), "food": food.copy()})

    if record:
        return frames
    prey_fit = food_eaten + cfg.survival_weight * (survived / n_steps)
    pred_fit = cfg.catch_weight * caught + cfg.pursuit_weight * (pursuit / n_steps)
    return prey_fit, pred_fit, {"total_caught": float(caught.sum()),
                                "survival_rate": survived / n_steps}


def _next_gen(w, fit, cfg, rng):
    n = w.shape[0]
    n_elite = max(1, int(n * cfg.elite_frac))
    elite = w[np.argsort(fit)[::-1][:n_elite]]
    parents = elite[rng.integers(0, n_elite, n - n_elite)]
    return np.vstack([elite, brain.mutate_brains(parents, rng, cfg.mut_rate, cfg.mut_sigma)])


def coevolve3d(cfg, seed=0):
    rng = np.random.default_rng(seed)
    sp = spec()
    prey_w = brain.random_brains(cfg.n_prey, sp, rng)
    pred_w = brain.random_brains(cfg.n_pred, sp, rng)
    prey_snaps, pred_snaps, snap_gens = [], [], []
    snap_every = max(1, cfg.generations // 12)
    for g in range(cfg.generations):
        pf, df, _ = episode3d(prey_w, pred_w, cfg, seed=1000 + g)
        if g % snap_every == 0 or g == cfg.generations - 1:
            prey_snaps.append(prey_w.copy()); pred_snaps.append(pred_w.copy()); snap_gens.append(g)
        prey_w = _next_gen(prey_w, pf, cfg, rng)
        pred_w = _next_gen(pred_w, df, cfg, rng)
    return {"prey": prey_w, "pred": pred_w, "prey_snaps": prey_snaps,
            "pred_snaps": pred_snaps, "snap_gens": snap_gens, "spec": sp}


def arms_race_curves3d(result, cfg):
    """Each snapshot vs the FINAL evolved opponent: predators vs final prey ->
    catches; prey vs final predators -> survival. Both rising = arms race."""
    final_prey, final_pred = result["prey"], result["pred"]
    gens, pred_skill, prey_skill = result["snap_gens"], [], []
    for i, g in enumerate(gens):
        _, _, pinfo = episode3d(final_prey, result["pred_snaps"][i], cfg, seed=5000 + g, steps=160)
        _, _, qinfo = episode3d(result["prey_snaps"][i], final_pred, cfg, seed=6000 + g)
        pred_skill.append(pinfo["total_caught"])
        prey_skill.append(float(qinfo["survival_rate"].mean()))
    return np.array(gens), np.array(pred_skill), np.array(prey_skill)
