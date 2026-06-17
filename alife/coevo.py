"""Predator–prey co-evolution by a generational GA — an evolutionary arms race.

Two brain populations evolve at once in a shared world: prey sense food and
predators (forage, flee) and predators sense prey (hunt). Each is selected on a
fitness the OTHER species shapes — prey on food eaten + time survived, predators
on prey caught — so improvement in one is pressure on the other. That is the Red
Queen: both must keep evolving just to hold their ground.

The trap with co-evolution is that absolute fitness is confounded (both sides
move), so progress is measured against FIXED naive opponents: current predators
vs generation-0 prey, and current prey vs generation-0 predators. Both rising is
the signature of a real arms race, not noise.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import brain, sensors
from .brain import BrainSpec
from .neuro import _sigmoid
from .sensors import _sector_proximity
from .world import World


@dataclass(frozen=True)
class CoevoConfig:
    world: World = field(default_factory=lambda: World(200.0, 200.0, toroidal=True))
    n_prey: int = 170
    n_pred: int = 50
    n_food: int = 260
    episode_steps: int = 320
    generations: int = 55
    elite_frac: float = 0.35
    mut_rate: float = 0.22
    mut_sigma: float = 0.3
    prey_speed: float = 2.9       # prey slightly slower but much more agile
    pred_speed: float = 3.1       # predators only a touch faster (~7%)
    prey_turn: float = 0.60       # prey can juke hard
    pred_turn: float = 0.40
    sense_range: float = 34.0
    eat_radius: float = 2.6       # prey eats food
    catch_radius: float = 2.8     # predator must really get on top of prey
    survival_weight: float = 14.0  # how much surviving the episode is worth to prey
    catch_weight: float = 6.0      # value of a catch to a predator
    pursuit_weight: float = 4.0    # dense reward: closing distance on prey (bootstraps hunting)
    food_regrow: int = 8


def spec() -> BrainSpec:
    return BrainSpec(n_in=sensors.n_inputs(), n_hidden=8, n_out=2)


def _sense_set(world: World, pos: np.ndarray, heading: np.ndarray, targets: np.ndarray,
               alive: np.ndarray | None, rng_range: float, k: int) -> np.ndarray:
    if targets.shape[0] == 0:
        return np.zeros((pos.shape[0], k))
    rel = world.delta_to(pos, targets)
    dist = np.sqrt(np.einsum("nmk,nmk->nm", rel, rel))
    if alive is not None:
        dist = np.where(alive[None, :], dist, np.inf)
    return _sector_proximity(rel, dist, heading, rng_range, k)


def _move(world, pos, heading, w, sp, top_speed, top_turn, k, chan_a, chan_b):
    """Returns (new_pos, new_heading, velocity). velocity is the pre-wrap
    displacement, so its norm is the true step length (correct movement cost)."""
    x = np.concatenate([chan_a, chan_b, np.full((pos.shape[0], 1), 0.5)], axis=1)
    out = brain.forward(w, sp, x)
    heading = (heading + np.tanh(out[:, 0]) * top_turn) % (2 * np.pi)
    speed = _sigmoid(out[:, 1]) * top_speed
    d = np.stack([np.cos(heading), np.sin(heading)], axis=1)
    vel = d * speed[:, None]
    return world.wrap(pos + vel), heading, vel


def episode(prey_w: np.ndarray, pred_w: np.ndarray, cfg: CoevoConfig, seed: int, steps: int | None = None):
    """Run one shared episode; return (prey_fitness, pred_fitness, info)."""
    rng = np.random.default_rng(seed)
    n_steps = cfg.episode_steps if steps is None else steps
    world, sp, k = cfg.world, spec(), sensors.K_SECTORS
    npp, npd = prey_w.shape[0], pred_w.shape[0]
    prey_pos = rng.uniform([0, 0], world.size, size=(npp, 2))
    pred_pos = rng.uniform([0, 0], world.size, size=(npd, 2))
    prey_head = rng.uniform(0, 2 * np.pi, npp)
    pred_head = rng.uniform(0, 2 * np.pi, npd)
    food = rng.uniform([0, 0], world.size, size=(cfg.n_food, 2))
    alive = np.ones(npp, dtype=bool)
    food_eaten = np.zeros(npp)
    survived = np.zeros(npp)
    caught = np.zeros(npd)
    pursuit = np.zeros(npd)        # dense closing-distance reward for predators

    for _ in range(n_steps):
        # prey act (forage + flee)
        food_ch = _sense_set(world, prey_pos, prey_head, food, None, cfg.sense_range, k)
        pred_ch = _sense_set(world, prey_pos, prey_head, pred_pos, None, cfg.sense_range, k)
        prey_pos, prey_head, _ = _move(world, prey_pos, prey_head, prey_w, sp,
                                    cfg.prey_speed, cfg.prey_turn, k, food_ch, pred_ch)
        # predators act (hunt)
        prey_ch = _sense_set(world, pred_pos, pred_head, prey_pos, alive, cfg.sense_range, k)
        pred_pos, pred_head, _ = _move(world, pred_pos, pred_head, pred_w, sp,
                                    cfg.pred_speed, cfg.pred_turn, k, prey_ch, np.zeros((npd, k)))

        # prey eat food (alive only)
        if food.shape[0]:
            fr = world.delta_to(prey_pos, food)
            fd2 = np.where(alive[:, None], np.einsum("nfk,nfk->nf", fr, fr), np.inf)
            hit = fd2.min(0) < cfg.eat_radius ** 2
            if hit.any():
                np.add.at(food_eaten, fd2.argmin(0)[hit], 1.0)
                food = food[~hit]
            need = min(cfg.food_regrow, cfg.n_food - food.shape[0])
            if need > 0:
                food = np.vstack([food, rng.uniform([0, 0], world.size, size=(need, 2))])

        # predators catch prey (each predator catches its nearest in range)
        if alive.any():
            pr = world.delta_to(pred_pos, prey_pos)
            pd2 = np.where(alive[None, :], np.einsum("pmk,pmk->pm", pr, pr), np.inf)
            nearest = pd2.argmin(1)
            nd = np.sqrt(pd2[np.arange(npd), nearest])
            pursuit += np.where(nd < cfg.sense_range, 1.0 - nd / cfg.sense_range, 0.0)
            can = nd < cfg.catch_radius
            for p in np.where(can)[0]:
                tgt = nearest[p]
                if alive[tgt]:
                    alive[tgt] = False
                    caught[p] += 1.0
        survived += alive

    prey_fitness = food_eaten + cfg.survival_weight * (survived / n_steps)
    pred_fitness = cfg.catch_weight * caught + cfg.pursuit_weight * (pursuit / n_steps)
    info = {"caught": caught, "survival_rate": survived / n_steps,
            "food": food_eaten, "total_caught": float(caught.sum())}
    return prey_fitness, pred_fitness, info


def rollout(prey_w, pred_w, cfg: CoevoConfig, seed: int, steps: int, capture_every: int = 2):
    """Run a shared episode and record per-frame state for rendering.

    Returns a list of dicts: prey_pos, prey_vel, pred_pos, pred_vel, food (only
    living prey included)."""
    rng = np.random.default_rng(seed)
    world, sp, k = cfg.world, spec(), sensors.K_SECTORS
    npp, npd = prey_w.shape[0], pred_w.shape[0]
    prey_pos = rng.uniform([0, 0], world.size, size=(npp, 2))
    pred_pos = rng.uniform([0, 0], world.size, size=(npd, 2))
    prey_head = rng.uniform(0, 2 * np.pi, npp)
    pred_head = rng.uniform(0, 2 * np.pi, npd)
    food = rng.uniform([0, 0], world.size, size=(cfg.n_food, 2))
    alive = np.ones(npp, dtype=bool)
    frames = []

    for t in range(steps):
        food_ch = _sense_set(world, prey_pos, prey_head, food, None, cfg.sense_range, k)
        pred_ch = _sense_set(world, prey_pos, prey_head, pred_pos, None, cfg.sense_range, k)
        prey_pos, prey_head, _ = _move(world, prey_pos, prey_head, prey_w, sp,
                                    cfg.prey_speed, cfg.prey_turn, k, food_ch, pred_ch)
        prey_ch = _sense_set(world, pred_pos, pred_head, prey_pos, alive, cfg.sense_range, k)
        pred_pos, pred_head, _ = _move(world, pred_pos, pred_head, pred_w, sp,
                                    cfg.pred_speed, cfg.pred_turn, k, prey_ch, np.zeros((npd, k)))
        if food.shape[0]:
            fr = world.delta_to(prey_pos, food)
            fd2 = np.where(alive[:, None], np.einsum("nfk,nfk->nf", fr, fr), np.inf)
            hit = fd2.min(0) < cfg.eat_radius ** 2
            if hit.any():
                food = food[~hit]
            need = min(cfg.food_regrow, cfg.n_food - food.shape[0])
            if need > 0:
                food = np.vstack([food, rng.uniform([0, 0], world.size, size=(need, 2))])
        if alive.any():
            pr = world.delta_to(pred_pos, prey_pos)
            pd2 = np.where(alive[None, :], np.einsum("pmk,pmk->pm", pr, pr), np.inf)
            nearest = pd2.argmin(1)
            for p in np.where(pd2[np.arange(npd), nearest] < cfg.catch_radius ** 2)[0]:
                alive[nearest[p]] = False
        if t % capture_every == 0:
            pv = np.stack([np.cos(prey_head), np.sin(prey_head)], 1)[alive]
            dv = np.stack([np.cos(pred_head), np.sin(pred_head)], 1)
            frames.append({"prey_pos": prey_pos[alive].copy(), "prey_vel": pv,
                           "pred_pos": pred_pos.copy(), "pred_vel": dv, "food": food.copy()})
    return frames


def _next_gen(w: np.ndarray, fit: np.ndarray, cfg: CoevoConfig, rng) -> np.ndarray:
    n = w.shape[0]
    n_elite = max(1, int(n * cfg.elite_frac))
    elite = w[np.argsort(fit)[::-1][:n_elite]]
    parents = elite[rng.integers(0, n_elite, n - n_elite)]
    return np.vstack([elite, brain.mutate_brains(parents, rng, cfg.mut_rate, cfg.mut_sigma)])


def coevolve(cfg: CoevoConfig, seed: int = 0):
    """Run the arms race. Returns dict with evolved brains, gen-0 brains, and
    histories including progress vs FIXED naive opponents."""
    rng = np.random.default_rng(seed)
    sp = spec()
    prey_w = brain.random_brains(cfg.n_prey, sp, rng)
    pred_w = brain.random_brains(cfg.n_pred, sp, rng)
    naive_prey, naive_pred = prey_w.copy(), pred_w.copy()
    hist = []                    # gen, prey_fit, pred_fit (coupled, Red-Queen view)
    prey_snaps, pred_snaps, snap_gens = [], [], []
    snap_every = max(1, cfg.generations // 12)

    for g in range(cfg.generations):
        pf, df, info = episode(prey_w, pred_w, cfg, seed=1000 + g)
        hist.append((g, float(pf.mean()), float(df.mean()), info["total_caught"]))
        if g % snap_every == 0 or g == cfg.generations - 1:
            prey_snaps.append(prey_w.copy()); pred_snaps.append(pred_w.copy()); snap_gens.append(g)
        prey_w = _next_gen(prey_w, pf, cfg, rng)
        pred_w = _next_gen(pred_w, df, cfg, rng)

    return {"prey": prey_w, "pred": pred_w, "naive_prey": naive_prey, "naive_pred": naive_pred,
            "hist": np.array(hist), "prey_snaps": prey_snaps, "pred_snaps": pred_snaps,
            "snap_gens": snap_gens, "spec": sp}


def arms_race_curves(result: dict, cfg: CoevoConfig):
    """De-confounded escalation: test every snapshot against the FINAL (hardest)
    opponent. Predators vs final prey -> catches; prey vs final predators ->
    survival. Both rising over generations = a genuine arms race."""
    final_prey, final_pred = result["prey"], result["pred"]
    gens = result["snap_gens"]
    pred_skill, prey_skill = [], []
    for i, g in enumerate(gens):
        _, _, pinfo = episode(final_prey, result["pred_snaps"][i], cfg, seed=5000 + g, steps=140)
        _, _, qinfo = episode(result["prey_snaps"][i], final_pred, cfg, seed=6000 + g)
        pred_skill.append(pinfo["total_caught"])
        prey_skill.append(float(qinfo["survival_rate"].mean()))
    return np.array(gens), np.array(pred_skill), np.array(prey_skill)
