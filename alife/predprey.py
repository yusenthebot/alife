"""Continuous predator–prey ecology — Lotka–Volterra population cycles.

Round 4 evolved hunting and fleeing inside fixed-length tournaments. Here the two
species live continuously in one world with full lifecycles: prey graze plants
and breed, predators eat prey and breed, predators starve when prey grow scarce.
Coupling those rates is what produces the textbook signature — predator and prey
populations rising and falling out of phase, the predators' peak lagging the
prey's. Seed it with the R4-evolved brains and the cycles are driven by real
evolved hunt/flee behavior, not scripted motion.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import brain, sensors
from .brain import BrainSpec
from .coevo import _move, _sense_set, spec
from .world import World


@dataclass(frozen=True)
class PredPreyConfig:
    world: World = field(default_factory=lambda: World(300.0, 300.0, toroidal=True))
    # plants (abundant -> prey can recover quickly = stabilizes cycles)
    food_cap: int = 720
    food_regrow: int = 26
    food_value: float = 28.0
    eat_radius: float = 2.6
    # prey (r-strategist: cheap, breeds fast, hardy)
    n_prey0: int = 360
    prey_cap: int = 2000
    prey_e_start: float = 50.0
    prey_e_repro: float = 70.0
    prey_e_max: float = 110.0
    prey_base_cost: float = 0.05
    prey_move_cost: float = 0.04
    prey_speed: float = 2.9
    prey_turn: float = 0.6
    max_age_prey: int = 1600
    # predator (weak conversion + handling time + fast starvation -> self-limiting)
    n_pred0: int = 18
    pred_cap: int = 600
    pred_e_start: float = 140.0
    pred_e_repro: float = 200.0       # MUST be < e_max or predators can never breed
    pred_e_max: float = 250.0         # modest hoard -> starves ~1 cycle after prey crash
    pred_base_cost: float = 0.50      # starves fast without prey
    pred_move_cost: float = 0.05
    pred_speed: float = 3.1
    pred_turn: float = 0.4
    catch_radius: float = 2.6
    prey_energy_value: float = 42.0   # a catch is modest energy (low conversion)
    pred_handling: int = 35           # digestion cooldown: Type-II functional response (key stabilizer)
    max_age_pred: int = 2400
    # shared
    sense_range: float = 34.0
    mut_rate: float = 0.12
    mut_sigma: float = 0.18


class PredPreyEcosystem:
    def __init__(self, cfg: PredPreyConfig, prey_brains=None, pred_brains=None, seed: int = 0):
        self.cfg = cfg
        self.rng = np.random.default_rng(seed)
        self.spec = spec()
        w = cfg.world
        self.food = self.rng.uniform([0, 0], w.size, size=(cfg.food_cap, 2))
        self.prey = self._init_species(cfg.n_prey0, cfg.prey_e_start, prey_brains)
        self.pred = self._init_species(cfg.n_pred0, cfg.pred_e_start, pred_brains)

    def _init_species(self, n, e_start, brains) -> dict:
        w = self.cfg.world
        if brains is None:
            b = brain.random_brains(n, self.spec, self.rng)
        else:
            b = brains[self.rng.integers(0, brains.shape[0], n)].copy()
        return {"pos": self.rng.uniform([0, 0], w.size, size=(n, 2)),
                "head": self.rng.uniform(0, 2 * np.pi, n),
                "vel": np.zeros((n, 2)),
                "energy": np.full(n, float(e_start)),
                "brains": b,
                "age": np.zeros(n, dtype=int),
                "cooldown": np.zeros(n, dtype=int)}  # predator digestion timer

    def _vel(self, sp: dict) -> np.ndarray:
        return np.stack([np.cos(sp["head"]), np.sin(sp["head"])], axis=1)

    def step(self) -> None:
        cfg, w, k = self.cfg, self.cfg.world, sensors.K_SECTORS
        prey, pred = self.prey, self.pred

        # ---- movement (evolved brains) ----
        if prey["pos"].shape[0]:
            food_ch = _sense_set(w, prey["pos"], prey["head"], self.food, None, cfg.sense_range, k)
            pred_ch = _sense_set(w, prey["pos"], prey["head"], pred["pos"], None, cfg.sense_range, k)
            prey["pos"], prey["head"], prey["vel"] = _move(
                w, prey["pos"], prey["head"], prey["brains"], self.spec,
                cfg.prey_speed, cfg.prey_turn, k, food_ch, pred_ch)
        if pred["pos"].shape[0]:
            prey_ch = _sense_set(w, pred["pos"], pred["head"], prey["pos"], None, cfg.sense_range, k)
            pred["pos"], pred["head"], pred["vel"] = _move(
                w, pred["pos"], pred["head"], pred["brains"], self.spec,
                cfg.pred_speed, cfg.pred_turn, k, prey_ch, np.zeros((pred["pos"].shape[0], k)))

        self._graze()
        pred["cooldown"] = np.maximum(pred["cooldown"] - 1, 0)
        self._catch()

        # ---- metabolism, cap, age ----
        prey["energy"] = np.minimum(prey["energy"] - (cfg.prey_base_cost
                          + cfg.prey_move_cost * np.linalg.norm(prey["vel"], axis=1)), cfg.prey_e_max)
        pred["energy"] = np.minimum(pred["energy"] - (cfg.pred_base_cost
                          + cfg.pred_move_cost * np.linalg.norm(pred["vel"], axis=1)), cfg.pred_e_max)
        prey["age"] += 1
        pred["age"] += 1

        # ---- death ----
        self._mask(prey, (prey["energy"] > 0) & (prey["age"] < cfg.max_age_prey))
        self._mask(pred, (pred["energy"] > 0) & (pred["age"] < cfg.max_age_pred))

        # ---- reproduction ----
        self._reproduce(prey, cfg.prey_e_repro, cfg.prey_cap)
        self._reproduce(pred, cfg.pred_e_repro, cfg.pred_cap)

        # ---- plants regrow ----
        need = min(cfg.food_regrow, cfg.food_cap - self.food.shape[0])
        if need > 0:
            new = self.rng.uniform([0, 0], w.size, size=(need, 2))
            self.food = np.vstack([self.food, new]) if self.food.shape[0] else new

    def _graze(self) -> None:
        cfg, w, prey = self.cfg, self.cfg.world, self.prey
        if not (prey["pos"].shape[0] and self.food.shape[0]):
            return
        fr = w.delta_to(prey["pos"], self.food)
        fd2 = np.einsum("nfk,nfk->nf", fr, fr)
        eaten = fd2.min(0) < cfg.eat_radius ** 2
        if eaten.any():
            np.add.at(prey["energy"], fd2.argmin(0)[eaten], cfg.food_value)
            self.food = self.food[~eaten]

    def _catch(self) -> None:
        """Predators eat their nearest prey if in range and not digesting."""
        cfg, w, prey, pred = self.cfg, self.cfg.world, self.prey, self.pred
        if not (pred["pos"].shape[0] and prey["pos"].shape[0]):
            return
        pr = w.delta_to(pred["pos"], prey["pos"])
        pd2 = np.einsum("pmk,pmk->pm", pr, pr)
        prey_alive = np.ones(prey["pos"].shape[0], dtype=bool)
        nearest = pd2.argmin(1)
        can = (pd2[np.arange(pred["pos"].shape[0]), nearest] < cfg.catch_radius ** 2) & (pred["cooldown"] == 0)
        for p in np.where(can)[0]:
            tgt = nearest[p]
            if prey_alive[tgt]:
                prey_alive[tgt] = False
                pred["energy"][p] += cfg.prey_energy_value
                pred["cooldown"][p] = cfg.pred_handling
        if not prey_alive.all():
            self._mask(prey, prey_alive)

    def _mask(self, sp: dict, keep: np.ndarray) -> None:
        if keep.all():
            return
        for key in ("pos", "head", "vel", "energy", "brains", "age", "cooldown"):
            sp[key] = sp[key][keep]

    def _reproduce(self, sp: dict, e_repro: float, cap: int) -> None:
        idx = np.where(sp["energy"] >= e_repro)[0]
        room = cap - sp["pos"].shape[0]
        if idx.size == 0 or room <= 0:
            return
        if idx.size > room:
            idx = self.rng.choice(idx, size=room, replace=False)
        sp["energy"][idx] *= 0.5
        w = self.cfg.world
        kids = brain.mutate_brains(sp["brains"][idx], self.rng, self.cfg.mut_rate, self.cfg.mut_sigma)
        sp["pos"] = np.vstack([sp["pos"], w.wrap(sp["pos"][idx] + self.rng.normal(0, 1.5, (idx.size, 2)))])
        sp["head"] = np.concatenate([sp["head"], self.rng.uniform(0, 2 * np.pi, idx.size)])
        sp["vel"] = np.vstack([sp["vel"], np.zeros((idx.size, 2))])
        sp["energy"] = np.concatenate([sp["energy"], sp["energy"][idx].copy()])
        sp["brains"] = np.vstack([sp["brains"], kids])
        sp["age"] = np.concatenate([sp["age"], np.zeros(idx.size, dtype=int)])
        sp["cooldown"] = np.concatenate([sp["cooldown"], np.zeros(idx.size, dtype=int)])

    def snapshot(self) -> dict[str, float]:
        return {"prey": float(self.prey["pos"].shape[0]),
                "pred": float(self.pred["pos"].shape[0]),
                "food": float(self.food.shape[0]),
                "prey_energy": float(self.prey["energy"].mean()) if self.prey["pos"].shape[0] else 0.0,
                "pred_energy": float(self.pred["energy"].mean()) if self.pred["pos"].shape[0] else 0.0}
