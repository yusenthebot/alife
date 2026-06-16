"""The living ecosystem: movement + energy + feeding + reproduction + death.

This is where evolution actually happens. Each creature moves by its own
genome (Round-1 flocking rules, now per-individual, plus a heritable pull toward
food), spends energy to live and move, eats food to refill, splits into a
mutated offspring when rich, and dies when it runs out. Nobody is told to be
fit — the genomes that happen to find food and reproduce simply become more
common. Population size is dynamic; the state arrays grow and shrink each tick.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import genome as gn
from .boids import _limit, _limit_speed, _set_mag
from .world import World


@dataclass(frozen=True)
class EcoConfig:
    world: World = field(default_factory=lambda: World(220.0, 220.0, toroidal=True))
    n0: int = 260                # initial population
    pop_cap: int = 1400          # memory + ecological ceiling
    food_cap: int = 620          # standing food
    food_regrow: int = 10        # new food spawned per step (up to cap)
    food_value: float = 17.0     # energy per food item
    eat_radius: float = 2.4
    e_start: float = 45.0
    e_repro: float = 85.0        # energy needed to split
    e_max: float = 160.0
    base_cost: float = 0.045     # energy/step just to exist
    move_cost: float = 0.075     # energy/step per (metabolism * speed)
    max_age: int = 2600
    mutation: gn.MutationConfig = field(default_factory=gn.MutationConfig)


def _steer(desired_dir: np.ndarray, vel: np.ndarray, max_speed: np.ndarray, max_force: np.ndarray) -> np.ndarray:
    return _limit(_set_mag(desired_dir, max_speed) - vel, max_force)


class Ecosystem:
    def __init__(self, cfg: EcoConfig, seed: int = 0) -> None:
        self.cfg = cfg
        self.rng = np.random.default_rng(seed)
        w = cfg.world
        n = cfg.n0
        self.pos = self.rng.uniform([0, 0], w.size, size=(n, 2))
        ang = self.rng.uniform(0, 2 * np.pi, n)
        self.vel = np.stack([np.cos(ang), np.sin(ang)], axis=1)
        self.energy = np.full(n, float(cfg.e_start))
        self.dna = gn.random_genomes(n, self.rng)
        self.generation = np.zeros(n, dtype=int)
        self.age = np.zeros(n, dtype=int)
        self.food = self.rng.uniform([0, 0], w.size, size=(cfg.food_cap, 2))
        self.births = 0
        self.deaths = 0

    # ---- behavior -----------------------------------------------------------
    def _accel(self) -> np.ndarray:
        w, dna, pos, vel = self.cfg.world, self.dna, self.pos, self.vel
        n = pos.shape[0]
        perc = dna[:, gn.PERCEPTION]
        perc2 = (perc ** 2)[:, None]
        sep2 = ((0.4 * perc) ** 2)[:, None]
        max_speed = gn.column(dna, gn.MAX_SPEED)
        max_force = 0.13 * max_speed

        diff = w.pairwise_delta(pos)
        dist2 = np.einsum("ijk,ijk->ij", diff, diff)
        dist2[np.arange(n), np.arange(n)] = np.inf
        perceived = dist2 < perc2
        close = dist2 < sep2
        cnt = perceived.sum(1, keepdims=True)
        has_n = cnt[:, 0] > 0
        has_close = close.any(1)

        coh = (diff * perceived[..., None]).sum(1) / np.maximum(cnt, 1)
        avg_vel = (vel[None] * perceived[..., None]).sum(1) / np.maximum(cnt, 1)
        weight = np.where(close, 1.0 / np.maximum(np.sqrt(dist2), 1e-6), 0.0)
        sep = -(diff * weight[..., None]).sum(1)

        coh_s = _steer(coh, vel, max_speed, max_force) * has_n[:, None]
        ali_s = _steer(avg_vel, vel, max_speed, max_force) * has_n[:, None]
        sep_s = _steer(sep, vel, max_speed, max_force) * has_close[:, None]

        food_s = np.zeros_like(vel)
        if self.food.shape[0]:
            fd = w.delta_to(pos, self.food)
            fdist2 = np.einsum("nfk,nfk->nf", fd, fd)
            nearest = fdist2.argmin(1)
            rows = np.arange(n)
            food_vec = fd[rows, nearest]
            in_range = fdist2[rows, nearest] < perc2[:, 0]
            food_s = _steer(food_vec * in_range[:, None], vel, max_speed, max_force)

        return (
            gn.column(dna, gn.W_COH) * coh_s
            + gn.column(dna, gn.W_ALI) * ali_s
            + gn.column(dna, gn.W_SEP) * sep_s
            + gn.column(dna, gn.W_FOOD) * food_s
        )

    # ---- one tick -----------------------------------------------------------
    def step(self) -> None:
        cfg = self.cfg
        if self.pos.shape[0] == 0:
            self._regrow_food()
            return

        max_speed = gn.column(self.dna, gn.MAX_SPEED)
        self.vel = _limit_speed(self.vel + self._accel(), 0.25 * max_speed, max_speed)
        self.pos = cfg.world.wrap(self.pos + self.vel)

        speed = np.linalg.norm(self.vel, axis=1)
        metab = self.dna[:, gn.METABOLISM]
        self.energy -= cfg.base_cost + cfg.move_cost * metab * speed

        self._eat()
        self.energy = np.minimum(self.energy, cfg.e_max)
        self.age += 1

        self._cull()
        self._reproduce()
        self._regrow_food()

    def _eat(self) -> None:
        if self.food.shape[0] == 0 or self.pos.shape[0] == 0:
            return
        fd = self.cfg.world.delta_to(self.pos, self.food)
        fd2 = np.einsum("nfk,nfk->nf", fd, fd)
        eaten = fd2.min(0) < self.cfg.eat_radius ** 2          # (F,)
        if not eaten.any():
            return
        eater = fd2.argmin(0)                                   # (F,)
        np.add.at(self.energy, eater[eaten], self.cfg.food_value)
        self.food = self.food[~eaten]

    def _cull(self) -> None:
        alive = (self.energy > 0.0) & (self.age < self.cfg.max_age)
        self.deaths += int((~alive).sum())
        if alive.all():
            return
        self.pos, self.vel = self.pos[alive], self.vel[alive]
        self.energy, self.dna = self.energy[alive], self.dna[alive]
        self.generation, self.age = self.generation[alive], self.age[alive]

    def _reproduce(self) -> None:
        cfg = self.cfg
        ready = self.energy >= cfg.e_repro
        room = cfg.pop_cap - self.pos.shape[0]
        idx = np.where(ready)[0]
        if idx.size == 0 or room <= 0:
            return
        if idx.size > room:
            idx = self.rng.choice(idx, size=room, replace=False)

        self.energy[idx] *= 0.5
        child_dna = gn.mutate(self.dna[idx], cfg.mutation, self.rng)
        offset = self.rng.normal(0.0, 1.5, size=(idx.size, 2))
        child_pos = cfg.world.wrap(self.pos[idx] + offset)
        ang = self.rng.uniform(0, 2 * np.pi, idx.size)
        child_vel = np.stack([np.cos(ang), np.sin(ang)], axis=1)

        self.pos = np.vstack([self.pos, child_pos])
        self.vel = np.vstack([self.vel, child_vel])
        self.energy = np.concatenate([self.energy, self.energy[idx].copy()])
        self.dna = np.vstack([self.dna, child_dna])
        self.generation = np.concatenate([self.generation, self.generation[idx] + 1])
        self.age = np.concatenate([self.age, np.zeros(idx.size, dtype=int)])
        self.births += idx.size

    def _regrow_food(self) -> None:
        cfg = self.cfg
        need = min(cfg.food_regrow, cfg.food_cap - self.food.shape[0])
        if need > 0:
            new = self.rng.uniform([0, 0], cfg.world.size, size=(need, 2))
            self.food = np.vstack([self.food, new]) if self.food.shape[0] else new

    # ---- observation --------------------------------------------------------
    def snapshot(self) -> dict[str, float]:
        n = self.pos.shape[0]
        out: dict[str, float] = {
            "population": float(n),
            "food": float(self.food.shape[0]),
            "mean_energy": float(self.energy.mean()) if n else 0.0,
            "max_gen": float(self.generation.max()) if n else 0.0,
        }
        for i, name in enumerate(gn.TRAIT_NAMES):
            out[f"trait_{name}"] = float(self.dna[:, i].mean()) if n else 0.0
        return out
