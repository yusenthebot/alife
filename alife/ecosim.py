"""R33 — the capstone: one living world where foraging behavior evolves in situ.

This is the integration the whole project was building toward. Brained creatures
live in a 2D world: they sense the nearest food, move (which costs energy), eat
(which gains it), reproduce when they have enough energy (the child inherits a
mutated brain), and die when they run out. Nothing is a generational GA — there
are no fitness evaluations, no truncation, no elitism. There is only life and
death. Selection is *in situ*.

R3's hard lesson was that in-situ selection on brains is too noisy when the
population pins at an arbitrary cap and food is dense (eating becomes
opportunistic and skill stops mattering). The fix here is a strictly
energy-limited ecology: food is scarce, moving costs energy, and reproduction is
expensive — so only creatures that actually find food leave descendants. Under
that pressure, directed foraging should evolve on its own, and you can watch it
happen generation by generation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from alife.brain import BrainSpec, forward

N_IN = 4    # [food_ahead, food_left, food_proximity, energy]
N_OUT = 2   # [turn, thrust]


@dataclass(frozen=True)
class EcoConfig:
    world: float = 100.0          # torus side length
    max_pop: int = 700            # generous cap so FOOD, not the cap, limits the population
    n_hidden: int = 6
    init_pop: int = 120
    food_max: int = 160           # scarce -> directed foraging is strongly selected
    food_spawn: int = 2           # pellets added per step
    food_energy: float = 26.0
    eat_radius: float = 2.5
    max_speed: float = 1.4
    max_turn: float = 0.6         # radians per step
    base_cost: float = 0.10       # metabolism per step
    move_cost: float = 0.12       # extra cost per unit speed
    e_start: float = 30.0
    e_repro: float = 55.0         # must save up well past start to reproduce
    mut_rate: float = 0.18
    mut_sigma: float = 0.35
    steps: int = 6000


def _spec(cfg: EcoConfig) -> BrainSpec:
    return BrainSpec(N_IN, cfg.n_hidden, N_OUT)


def _wrap(p, w):
    return np.mod(p, w)


def _torus_delta(a, b, w):
    """Shortest vector from a to b on a torus of side w. a:(...,2), b:(...,2)."""
    d = b - a
    return d - w * np.round(d / w)


def run(cfg: EcoConfig, seed: int = 0, record_every: int = 0):
    """Simulate the living world. Returns a metrics dict; if record_every>0 also
    stores creature/food snapshots at that interval for visualization."""
    rng = np.random.default_rng(seed)
    spec = _spec(cfg)
    nw = spec.n_weights
    P = cfg.max_pop

    genome = rng.normal(0, 1.0, (P, nw))
    pos = rng.uniform(0, cfg.world, (P, 2))
    head = rng.uniform(-np.pi, np.pi, P)
    energy = np.full(P, cfg.e_start)
    alive = np.zeros(P, bool); alive[: cfg.init_pop] = True
    generation = np.zeros(P, int)          # lineage depth (born-generation proxy)

    food = rng.uniform(0, cfg.world, (cfg.food_max, 2))
    food_on = np.ones(cfg.food_max, bool)

    hist = {"t": [], "pop": [], "directedness": [], "mean_gen": [], "intake": []}
    snaps = []

    for t in range(cfg.steps):
        idx = np.where(alive)[0]
        if idx.size == 0:
            break
        on_idx = np.where(food_on)[0]
        fpos = food[on_idx]
        intake_step = 0.0
        directed = np.nan
        if fpos.shape[0] > 0:
            # nearest food per alive creature (torus)
            d = _torus_delta(pos[idx][:, None, :], fpos[None, :, :], cfg.world)
            dist = np.linalg.norm(d, axis=2)
            nn = np.argmin(dist, axis=1)
            ndist = dist[np.arange(idx.size), nn]
            nvec = d[np.arange(idx.size), nn]               # vector to nearest food
            bearing = np.arctan2(nvec[:, 1], nvec[:, 0]) - head[idx]
            food_ahead = np.cos(bearing)
            food_left = np.sin(bearing)
            food_prox = 1.0 / (1.0 + ndist)
            x = np.stack([food_ahead, food_left, food_prox,
                          np.clip(energy[idx] / cfg.e_repro, 0, 2)], axis=1)
            out = forward(genome[idx], spec, x)
            turn = np.tanh(out[:, 0]) * cfg.max_turn
            thrust = (np.tanh(out[:, 1]) * 0.5 + 0.5) * cfg.max_speed
            head[idx] = head[idx] + turn
            step = np.stack([np.cos(head[idx]), np.sin(head[idx])], axis=1) * thrust[:, None]
            pos[idx] = _wrap(pos[idx] + step, cfg.world)
            energy[idx] -= cfg.base_cost + cfg.move_cost * thrust
            directed = float(np.mean((thrust > 0.05) * food_ahead))  # moving toward food?

            # eating: each creature eats its nearest food if within reach (greedy, one-per-food)
            can = ndist < cfg.eat_radius
            if np.any(can):
                eaters = np.where(can)[0]
                # resolve contested food: nearest eater wins each pellet
                order = np.argsort(ndist[eaters])
                for e in eaters[order]:
                    fi = on_idx[nn[e]]              # absolute food index (fixed for this step)
                    if not food_on[fi]:
                        continue
                    food_on[fi] = False
                    energy[idx[e]] += cfg.food_energy
                    intake_step += cfg.food_energy
        else:
            energy[idx] -= cfg.base_cost

        # death
        dead = idx[energy[idx] <= 0]
        alive[dead] = False

        # reproduction: pay e_repro, split with a child in a free slot
        idx = np.where(alive)[0]
        parents = idx[energy[idx] >= cfg.e_repro]
        free = np.where(~alive)[0]
        n = min(parents.size, free.size)
        if n > 0:
            par = parents[:n]; child = free[:n]
            energy[par] *= 0.5
            energy[child] = energy[par]
            genome[child] = genome[par] + (rng.normal(0, cfg.mut_sigma, (n, nw))
                                           * (rng.random((n, nw)) < cfg.mut_rate))
            pos[child] = _wrap(pos[par] + rng.normal(0, 2.0, (n, 2)), cfg.world)
            head[child] = rng.uniform(-np.pi, np.pi, n)
            generation[child] = generation[par] + 1
            alive[child] = True

        # food respawn
        off = np.where(~food_on)[0]
        if off.size > 0:
            k = min(cfg.food_spawn, off.size)
            pick = off[:k]
            food[pick] = rng.uniform(0, cfg.world, (k, 2))
            food_on[pick] = True

        if t % 50 == 0:
            a = np.where(alive)[0]
            hist["t"].append(t)
            hist["pop"].append(int(a.size))
            hist["directedness"].append(directed)
            hist["mean_gen"].append(float(generation[a].mean()) if a.size else 0.0)
            hist["intake"].append(intake_step)
        if record_every and t % record_every == 0:
            a = np.where(alive)[0]
            snaps.append({"t": t, "pos": pos[a].copy(), "head": head[a].copy(),
                          "gen": generation[a].copy(), "food": food[food_on].copy()})

    out = {k: np.array(v, dtype=float) for k, v in hist.items()}
    out["snaps"] = snaps
    return out
