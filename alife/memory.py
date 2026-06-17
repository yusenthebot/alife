"""Recurrent (memory) brains and the task that proves memory matters.

A feedforward brain is a reflex: its action depends only on what it senses this
instant. A recurrent brain carries a hidden state, so it can act on the past.
To show that buys anything, the world has to hide information the agent needs —
here food sensing periodically BLACKS OUT. During a blackout a reflex forager is
blind and wanders; a forager that remembered where food was can keep going.

Evaluation is a clean, controlled comparison: the SAME recurrent architecture and
genome size for both arms — the only difference is whether the hidden state
persists between steps (memory) or is wiped each step (memoryless). So any
fitness gap is attributable to memory alone.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import brain, sensors
from .brain import RecurrentSpec
from .evolve import EvolveConfig
from .neuro import NeuroConfig, _sigmoid
from .sensors import _sector_proximity


@dataclass(frozen=True)
class Occlusion:
    visible: int = 6      # steps food sensing is on
    blackout: int = 10    # steps it is off (must be bridged by memory)

    @property
    def period(self) -> int:
        return self.visible + self.blackout

    def occluded(self, t: int) -> bool:
        return (t % self.period) >= self.visible


def forage_occluded(brains: np.ndarray, spec: RecurrentSpec, cfg: NeuroConfig, occ: Occlusion,
                    n_food: int, steps: int, seed: int, recurrent: bool) -> np.ndarray:
    """Food eaten per brain under periodic sensor blackout. recurrent=False wipes
    the hidden state each step (memoryless control)."""
    rng = np.random.default_rng(seed)
    world, p, k = cfg.world, brains.shape[0], sensors.K_SECTORS
    layout = rng.uniform([0, 0], world.size, size=(n_food, 2))
    food = np.repeat(layout[None], p, axis=0)
    alive = np.ones((p, n_food), dtype=bool)
    pos = np.repeat(rng.uniform([0, 0], world.size, size=(1, 2)), p, axis=0)
    heading = np.full(p, rng.uniform(0, 2 * np.pi))
    hidden = np.zeros((p, spec.n_hidden))
    fitness = np.zeros(p)
    regrow_p = cfg.food_regrow / n_food
    rows = np.arange(p)

    for t in range(steps):
        rel = food - pos[:, None, :]
        if world.toroidal:
            rel -= world.size * np.round(rel / world.size)
        dist = np.sqrt(np.einsum("pfk,pfk->pf", rel, rel))
        dist_v = np.where(alive, dist, np.inf)
        food_ch = _sector_proximity(rel, dist_v, heading, cfg.sense_range, k)
        if occ.occluded(t):
            food_ch = np.zeros_like(food_ch)               # blackout: senses go dark
        x = np.concatenate([food_ch, np.zeros((p, k)), np.full((p, 1), 0.5)], axis=1)

        if not recurrent:
            hidden = np.zeros_like(hidden)                  # memoryless control
        out, hidden = brain.forward_recurrent(brains, spec, x, hidden)
        heading = (heading + np.tanh(out[:, 0]) * cfg.max_turn) % (2 * np.pi)
        speed = _sigmoid(out[:, 1]) * cfg.max_speed
        pos = world.wrap(pos + np.stack([np.cos(heading), np.sin(heading)], axis=1) * speed[:, None])

        rel = food - pos[:, None, :]
        if world.toroidal:
            rel -= world.size * np.round(rel / world.size)
        d2 = np.where(alive, np.einsum("pfk,pfk->pf", rel, rel), np.inf)
        nearest = d2.argmin(1)
        ate = d2[rows, nearest] < cfg.eat_radius ** 2
        fitness += ate
        alive[rows[ate], nearest[ate]] = False
        revive = (~alive) & (rng.random((p, n_food)) < regrow_p)
        if revive.any():
            food[revive] = rng.uniform([0, 0], world.size, size=(int(revive.sum()), 2))
            alive[revive] = True
    return fitness


def _food_away_from(rng, world, nest, n, exclude: float) -> np.ndarray:
    """Sample n food positions all at least `exclude` from the nest (toroidal),
    so foraging forces leaving home-sight — making memory essential."""
    out = []
    while len(out) < n:
        c = rng.uniform([0, 0], world.size, size=(n, 2))
        d = c - nest
        d -= world.size * np.round(d / world.size)
        out.extend(c[(d * d).sum(1) >= exclude ** 2].tolist())
    return np.array(out[:n])


def nest_forage(brains: np.ndarray, spec: RecurrentSpec, cfg: NeuroConfig, n_food: int,
                steps: int, seed: int, recurrent: bool, nest_radius: float = 14.0,
                nest_sense: float = 20.0) -> np.ndarray:
    """Central-place foraging: eat food (carry it), then DEPOSIT it at the nest
    (world center) to score. The nest is only sensed within sense_range — so once
    a forager wanders out to distant food, it is blind to home and must REMEMBER
    the way back. A reactive policy can only graze the ring it can see the nest
    from; memory unlocks the whole world. Returns food deposited per brain."""
    rng = np.random.default_rng(seed)
    world, p, k = cfg.world, brains.shape[0], sensors.K_SECTORS
    nest = world.size / 2.0
    layout = _food_away_from(rng, world, nest, n_food, exclude=55.0)
    food = np.repeat(layout[None], p, axis=0)
    alive = np.ones((p, n_food), dtype=bool)
    pos = np.repeat(nest[None], p, axis=0).astype(float)
    heading = np.full(p, rng.uniform(0, 2 * np.pi))
    hidden = np.zeros((p, spec.n_hidden))
    carry = np.zeros(p)
    deposited = np.zeros(p)
    carry_cap = 4.0
    regrow_p = cfg.food_regrow / n_food
    rows = np.arange(p)

    for _ in range(steps):
        rel = food - pos[:, None, :]
        if world.toroidal:
            rel -= world.size * np.round(rel / world.size)
        dist = np.sqrt(np.einsum("pfk,pfk->pf", rel, rel))
        food_ch = _sector_proximity(rel, np.where(alive, dist, np.inf), heading, cfg.sense_range, k)
        nrel = (nest[None] - pos)
        if world.toroidal:
            nrel -= world.size * np.round(nrel / world.size)
        ndist = np.sqrt((nrel * nrel).sum(1))
        nest_ch = _sector_proximity(nrel[:, None, :], ndist[:, None], heading, nest_sense, k)
        x = np.concatenate([food_ch, nest_ch, (carry / carry_cap)[:, None]], axis=1)

        if not recurrent:
            hidden = np.zeros_like(hidden)
        out, hidden = brain.forward_recurrent(brains, spec, x, hidden)
        heading = (heading + np.tanh(out[:, 0]) * cfg.max_turn) % (2 * np.pi)
        speed = _sigmoid(out[:, 1]) * cfg.max_speed
        pos = world.wrap(pos + np.stack([np.cos(heading), np.sin(heading)], axis=1) * speed[:, None])

        # eat (pick up) if room to carry
        rel = food - pos[:, None, :]
        if world.toroidal:
            rel -= world.size * np.round(rel / world.size)
        d2 = np.where(alive, np.einsum("pfk,pfk->pf", rel, rel), np.inf)
        nearest = d2.argmin(1)
        ate = (d2[rows, nearest] < cfg.eat_radius ** 2) & (carry < carry_cap)
        carry += ate
        alive[rows[ate], nearest[ate]] = False
        # deposit at nest
        nrel = nest[None] - pos
        if world.toroidal:
            nrel -= world.size * np.round(nrel / world.size)
        home = (nrel * nrel).sum(1) < nest_radius ** 2
        deposited += np.where(home, carry, 0.0)
        carry = np.where(home, 0.0, carry)
        revive = (~alive) & (rng.random((p, n_food)) < regrow_p)
        if revive.any():
            food[revive] = _food_away_from(rng, world, nest, int(revive.sum()), exclude=55.0)
            alive[revive] = True
    return deposited


def evolve_task(eval_fn, spec, cfg, ec, recurrent: bool, seed: int = 0, **kw):
    """Generic GA over a fitness function eval_fn(brains, spec, cfg, n_food, steps, seed, recurrent, **kw)."""
    rng = np.random.default_rng(seed)
    brains = brain.random_brains(ec.pop, spec, rng)
    n_elite = max(1, int(ec.pop * ec.elite_frac))
    history = []
    for g in range(ec.generations):
        fit = eval_fn(brains, spec, cfg, ec.n_food, ec.eval_steps, 1000 + g, recurrent, **kw)
        history.append((g, float(fit.mean()), float(fit.max())))
        elite = brains[np.argsort(fit)[::-1][:n_elite]]
        parents = elite[rng.integers(0, n_elite, ec.pop - n_elite)]
        brains = np.vstack([elite, brain.mutate_brains(parents, rng, ec.mut_rate, ec.mut_sigma)])
    return brains, np.array(history)


def evolve_mem(spec: RecurrentSpec, cfg: NeuroConfig, ec: EvolveConfig, occ: Occlusion,
               recurrent: bool, seed: int = 0):
    """GA over recurrent brains under occluded foraging. Returns (brains, history)."""
    rng = np.random.default_rng(seed)
    brains = brain.random_brains(ec.pop, spec, rng)
    n_elite = max(1, int(ec.pop * ec.elite_frac))
    history = []
    for g in range(ec.generations):
        fit = forage_occluded(brains, spec, cfg, occ, ec.n_food, ec.eval_steps,
                              seed=1000 + g, recurrent=recurrent)
        history.append((g, float(fit.mean()), float(fit.max())))
        elite = brains[np.argsort(fit)[::-1][:n_elite]]
        parents = elite[rng.integers(0, n_elite, ec.pop - n_elite)]
        brains = np.vstack([elite, brain.mutate_brains(parents, rng, ec.mut_rate, ec.mut_sigma)])
    return brains, np.array(history)
