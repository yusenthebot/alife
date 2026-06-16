"""NeuroEcosystem: creatures whose movement comes from an evolved brain.

The ecology of Round 2 is kept verbatim — energy, feeding, energy-split
reproduction with mutation, starvation death, food regrowth — but the controller
is replaced. Each creature senses its surroundings egocentrically, runs a
forward pass through its own network, and acts (turn + thrust). The genome is the
network's weights. Body parameters (top speed, metabolism, sense range) are
FIXED and identical for everyone, so anything the population gets better at is
attributable to the evolving brain, not to evolving the body.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import brain, sensors
from .brain import BrainSpec
from .world import World


@dataclass(frozen=True)
class NeuroConfig:
    world: World = field(default_factory=lambda: World(220.0, 220.0, toroidal=True))
    n0: int = 300
    pop_cap: int = 1200             # high: ecology (food) should cap the pop, not this
    food_cap: int = 340             # scarce — foraging skill must matter (strong selection regime)
    food_regrow: int = 7            # slow regrow => sustained scarcity
    food_value: float = 26.0        # a find is worth real energy
    eat_radius: float = 2.6
    e_start: float = 60.0
    e_repro: float = 90.0
    e_max: float = 105.0            # can't hoard energy => must keep foraging
    base_cost: float = 0.11         # existence costs => idlers starve
    move_cost: float = 0.05
    max_age: int = 1600             # mortality => continual turnover => continual selection
    # fixed body
    max_speed: float = 3.0
    metabolism: float = 1.0
    sense_range: float = 32.0
    max_turn: float = 0.45          # radians per step
    hidden: int = 8
    mut_rate: float = 0.2
    mut_sigma: float = 0.35


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def forage_assay(brains: np.ndarray, spec: BrainSpec, cfg: NeuroConfig,
                 steps: int = 300, seed: int = 9999) -> np.ndarray:
    """Controlled fitness test: each brain alone in an IDENTICAL food field.

    Same seed for every brain => same food layout and start, so the only variable
    is the network. Returns food eaten per brain — the clean measure of whether
    evolution produced competent foragers, with no population confounds.
    """
    return np.array([solo_run(brains[k : k + 1], spec, cfg, steps, seed)["eaten"]
                     for k in range(brains.shape[0])], dtype=float)


def solo_run(w: np.ndarray, spec: BrainSpec, cfg: NeuroConfig, steps: int = 300,
             seed: int = 9999) -> dict:
    """Run ONE brain alone in a fixed food field; trace its path and behavior.

    Returns eaten count, mean alignment-to-nearest-food (clean, uncrowded), the
    position trajectory, and the food layout — everything needed to both score
    and *draw* what the brain does.
    """
    world = cfg.world
    w = np.atleast_2d(w)
    rng = np.random.default_rng(seed)
    food0 = rng.uniform([0, 0], world.size, size=(cfg.food_cap, 2))
    food = food0.copy()
    pos = rng.uniform([0, 0], world.size, size=(1, 2))
    heading = rng.uniform(0, 2 * np.pi, 1)
    energy = np.array([cfg.e_repro * 0.5])
    eaten, aligns, traj = 0, [], []
    for _ in range(steps):
        d = np.stack([np.cos(heading), np.sin(heading)], axis=1)
        x = sensors.sense(world, pos, d, energy, food, cfg.sense_range, cfg.e_repro)
        out = brain.forward(w, spec, x)
        heading = (heading + np.tanh(out[:, 0]) * cfg.max_turn) % (2 * np.pi)
        speed = _sigmoid(out[:, 1]) * cfg.max_speed
        vel = np.stack([np.cos(heading), np.sin(heading)], axis=1) * speed[:, None]
        pos = world.wrap(pos + vel)
        traj.append(pos[0].copy())
        if food.shape[0]:
            fr = world.delta_to(pos, food)
            fd2 = np.einsum("nfk,nfk->nf", fr, fr)
            nrst = fr[0, fd2[0].argmin()]
            if fd2[0].min() < cfg.sense_range ** 2 and speed[0] > 1e-6:
                nf = nrst / max(np.linalg.norm(nrst), 1e-9)
                aligns.append(float(vel[0] @ nf / max(np.linalg.norm(vel[0]), 1e-9)))
            hit = fd2[0] < cfg.eat_radius ** 2
            eaten += int(hit.sum())
            food = food[~hit]
        need = min(cfg.food_regrow, cfg.food_cap - food.shape[0])
        if need > 0:
            food = np.vstack([food, rng.uniform([0, 0], world.size, size=(need, 2))])
    return {"eaten": eaten, "alignment": float(np.mean(aligns)) if aligns else 0.0,
            "traj": np.array(traj), "food": food0}


class NeuroEcosystem:
    def __init__(self, cfg: NeuroConfig, seed: int = 0) -> None:
        self.cfg = cfg
        self.rng = np.random.default_rng(seed)
        self.spec = BrainSpec(n_in=sensors.n_inputs(), n_hidden=cfg.hidden, n_out=2)
        w = cfg.world
        n = cfg.n0
        self.pos = self.rng.uniform([0, 0], w.size, size=(n, 2))
        self.heading = self.rng.uniform(0, 2 * np.pi, n)
        self.energy = np.full(n, float(cfg.e_start))
        self.brains = brain.random_brains(n, self.spec, self.rng)
        self.generation = np.zeros(n, dtype=int)
        self.age = np.zeros(n, dtype=int)
        self.food = self.rng.uniform([0, 0], w.size, size=(cfg.food_cap, 2))
        self.vel = np.zeros((n, 2))
        self.births = 0
        self.deaths = 0
        self.eaten_last = 0

    def _direction(self) -> np.ndarray:
        return np.stack([np.cos(self.heading), np.sin(self.heading)], axis=1)

    def step(self) -> None:
        cfg = self.cfg
        if self.pos.shape[0] == 0:
            self._regrow_food()
            return

        x = sensors.sense(cfg.world, self.pos, self._direction(), self.energy,
                          self.food, cfg.sense_range, cfg.e_repro)
        out = brain.forward(self.brains, self.spec, x)
        self.heading = (self.heading + np.tanh(out[:, 0]) * cfg.max_turn) % (2 * np.pi)
        speed = _sigmoid(out[:, 1]) * cfg.max_speed
        self.vel = self._direction() * speed[:, None]
        self.pos = cfg.world.wrap(self.pos + self.vel)

        self.energy -= cfg.base_cost + cfg.move_cost * cfg.metabolism * speed
        self._eat()
        self.energy = np.minimum(self.energy, cfg.e_max)
        self.age += 1
        self._cull()
        self._reproduce()
        self._regrow_food()

    def _eat(self) -> None:
        if self.food.shape[0] == 0 or self.pos.shape[0] == 0:
            return
        fr = self.cfg.world.delta_to(self.pos, self.food)
        fd2 = np.einsum("nfk,nfk->nf", fr, fr)
        eaten = fd2.min(0) < self.cfg.eat_radius ** 2
        self.eaten_last = int(eaten.sum())
        if not eaten.any():
            return
        np.add.at(self.energy, fd2.argmin(0)[eaten], self.cfg.food_value)
        self.food = self.food[~eaten]

    def _cull(self) -> None:
        alive = (self.energy > 0.0) & (self.age < self.cfg.max_age)
        self.deaths += int((~alive).sum())
        if alive.all():
            return
        self.pos, self.heading, self.vel = self.pos[alive], self.heading[alive], self.vel[alive]
        self.energy, self.brains = self.energy[alive], self.brains[alive]
        self.generation, self.age = self.generation[alive], self.age[alive]

    def _reproduce(self) -> None:
        cfg = self.cfg
        idx = np.where(self.energy >= cfg.e_repro)[0]
        room = cfg.pop_cap - self.pos.shape[0]
        if idx.size == 0 or room <= 0:
            return
        if idx.size > room:
            idx = self.rng.choice(idx, size=room, replace=False)
        self.energy[idx] *= 0.5
        child_brains = brain.mutate_brains(self.brains[idx], self.rng, cfg.mut_rate, cfg.mut_sigma)
        offset = self.rng.normal(0.0, 1.5, size=(idx.size, 2))
        self.pos = np.vstack([self.pos, cfg.world.wrap(self.pos[idx] + offset)])
        self.heading = np.concatenate([self.heading, self.rng.uniform(0, 2 * np.pi, idx.size)])
        self.vel = np.vstack([self.vel, np.zeros((idx.size, 2))])
        self.energy = np.concatenate([self.energy, self.energy[idx].copy()])
        self.brains = np.vstack([self.brains, child_brains])
        self.generation = np.concatenate([self.generation, self.generation[idx] + 1])
        self.age = np.concatenate([self.age, np.zeros(idx.size, dtype=int)])
        self.births += idx.size

    def _regrow_food(self) -> None:
        cfg = self.cfg
        need = min(cfg.food_regrow, cfg.food_cap - self.food.shape[0])
        if need > 0:
            new = self.rng.uniform([0, 0], cfg.world.size, size=(need, 2))
            self.food = np.vstack([self.food, new]) if self.food.shape[0] else new

    def food_alignment(self) -> float:
        """Behavioral readout: among creatures that can SEE food, how well does
        their motion point at the nearest visible food?

        +1 = straight at it, 0 = random, <0 = away. Restricted to creatures with
        food inside sense_range — the ones actually making a foraging decision;
        a creature that can't see food can't be expected to steer toward it.
        Measured in situ, with no bearing on selection.
        """
        if self.pos.shape[0] == 0 or self.food.shape[0] == 0:
            return 0.0
        fr = self.cfg.world.delta_to(self.pos, self.food)
        fd2 = np.einsum("nfk,nfk->nf", fr, fr)
        amin = fd2.argmin(1)
        nearest = fr[np.arange(fr.shape[0]), amin]
        visible = fd2[np.arange(fr.shape[0]), amin] < self.cfg.sense_range ** 2
        if not visible.any():
            return 0.0
        nf = nearest / np.maximum(np.linalg.norm(nearest, axis=1, keepdims=True), 1e-9)
        sp = np.maximum(np.linalg.norm(self.vel, axis=1, keepdims=True), 1e-9)
        return float((self.vel / sp * nf).sum(1)[visible].mean())

    def assay_brains(self, which: np.ndarray, steps: int = 300, assay_seed: int = 9999) -> np.ndarray:
        return forage_assay(which, self.spec, self.cfg, steps, assay_seed)

    def snapshot(self) -> dict[str, float]:
        n = self.pos.shape[0]
        return {
            "population": float(n),
            "food": float(self.food.shape[0]),
            "mean_energy": float(self.energy.mean()) if n else 0.0,
            "max_gen": float(self.generation.max()) if n else 0.0,
            "eaten": float(self.eaten_last),
            "food_alignment": self.food_alignment(),
        }
