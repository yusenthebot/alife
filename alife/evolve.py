"""Generational neuroevolution: evolve brains that forage, by selection alone.

The continuous ecosystem (neuro.py) is a beautiful living world, but in-situ it
tends to reward energy-conservation ("sit still") as much as skill, so the
foraging signal is noisy. Here selection is explicit and clean: every generation
each brain forages a fresh field on its own, the best foragers become parents,
their mutated offspring form the next generation. This is natural selection in
its starkest form — differential reproduction by fitness — and it reliably turns
random networks into competent foragers, generation by generation.

Evaluation is batched (every brain in its own private field, no interaction) so a
whole generation is a handful of array ops, not a Python loop over creatures.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import brain, sensors
from .brain import BrainSpec
from .neuro import NeuroConfig, _sigmoid
from .sensors import _sector_proximity


@dataclass(frozen=True)
class EvolveConfig:
    pop: int = 160
    generations: int = 45
    eval_steps: int = 300
    n_food: int = 280
    elite_frac: float = 0.35
    mut_rate: float = 0.22
    mut_sigma: float = 0.3


def batch_forage(brains: np.ndarray, spec: BrainSpec, cfg: NeuroConfig,
                 n_food: int, steps: int, seed: int) -> np.ndarray:
    """Each brain alone in its own (initially identical) food field. Returns
    food eaten per brain — a clean, crowding-free fitness."""
    rng = np.random.default_rng(seed)
    world = cfg.world
    p, k = brains.shape[0], sensors.K_SECTORS
    layout = rng.uniform([0, 0], world.size, size=(n_food, 2))
    food = np.repeat(layout[None], p, axis=0)            # (P, F, 2)
    alive = np.ones((p, n_food), dtype=bool)
    pos = np.repeat(rng.uniform([0, 0], world.size, size=(1, 2)), p, axis=0)
    heading = np.full(p, rng.uniform(0, 2 * np.pi))
    energy = np.full((p, 1), 0.5)                          # constant energy channel
    fitness = np.zeros(p)
    regrow_p = cfg.food_regrow / n_food
    rows = np.arange(p)

    for _ in range(steps):
        rel = food - pos[:, None, :]
        if world.toroidal:
            rel -= world.size * np.round(rel / world.size)
        dist = np.sqrt(np.einsum("pfk,pfk->pf", rel, rel))
        dist_v = np.where(alive, dist, np.inf)
        food_ch = _sector_proximity(rel, dist_v, heading, cfg.sense_range, k)
        x = np.concatenate([food_ch, np.zeros((p, k)), energy], axis=1)

        out = brain.forward(brains, spec, x)
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


def evolve(spec: BrainSpec, cfg: NeuroConfig, ec: EvolveConfig, seed: int = 0):
    """Run the GA. Returns (final_brains, history, gen0_brains).

    history rows: (generation, mean_fitness, max_fitness). A fresh field each
    generation (varying eval seed) forces *general* foraging, not memorizing one
    layout.
    """
    rng = np.random.default_rng(seed)
    brains = brain.random_brains(ec.pop, spec, rng)
    gen0 = brains.copy()
    n_elite = max(1, int(ec.pop * ec.elite_frac))
    history = []

    for g in range(ec.generations):
        fit = batch_forage(brains, spec, cfg, ec.n_food, ec.eval_steps, seed=1000 + g)
        history.append((g, float(fit.mean()), float(fit.max())))
        elite = brains[np.argsort(fit)[::-1][:n_elite]]
        parents = elite[rng.integers(0, n_elite, ec.pop - n_elite)]
        children = brain.mutate_brains(parents, rng, ec.mut_rate, ec.mut_sigma)
        brains = np.vstack([elite, children])

    return brains, np.array(history), gen0
