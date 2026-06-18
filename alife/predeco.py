"""R34 — in-situ predator-prey co-evolution: an arms race from pure ecology.

R33 put one species in a living world and watched foraging evolve with no GA.
This adds a second species. Prey forage for food and must dodge predators;
predators hunt prey. Both carry brains, both spend energy, both reproduce and
die. There is still no fitness function and no generational GA — only life and
death in one shared world.

What should emerge, with no one designing it: prey evolve to flee (move *away*
from the nearest predator) and predators evolve to pursue (move *toward* the
nearest prey) — a Red-Queen arms race playing out in real time, on top of the
boom-and-bust population dynamics that two coupled species produce.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from alife.brain import BrainSpec, forward

PREY_IN = 7    # [food_ahead, food_left, food_prox, pred_ahead, pred_left, pred_prox, energy]
PRED_IN = 4    # [prey_ahead, prey_left, prey_prox, energy]
N_OUT = 2      # [turn, thrust]


@dataclass(frozen=True)
class PredEcoConfig:
    world: float = 100.0
    n_hidden: int = 8
    # prey
    max_prey: int = 450
    init_prey: int = 180
    prey_speed: float = 1.4
    prey_eat_radius: float = 2.5
    prey_base_cost: float = 0.10
    prey_move_cost: float = 0.10
    prey_e_start: float = 30.0
    prey_e_repro: float = 42.0
    # predators — capped below prey (a territoriality-like ceiling; the R5 lesson)
    max_pred: int = 160
    init_pred: int = 10
    pred_speed: float = 1.45         # marginal speed edge, but pays more upkeep
    catch_radius: float = 1.8
    pred_base_cost: float = 0.50
    pred_move_cost: float = 0.10
    pred_e_start: float = 60.0
    pred_e_repro: float = 115.0
    prey_energy_to_pred: float = 55.0   # energy a predator gains per catch
    # food for prey
    food_max: int = 240
    food_spawn: int = 9
    food_energy: float = 26.0
    # shared
    max_turn: float = 0.6
    mut_rate: float = 0.18
    mut_sigma: float = 0.35
    refuge_radius: float = 15.0      # Huffaker refuge at world centre: prey inside are safe
    steps: int = 6000


def _wrap(p, w):
    return np.mod(p, w)


def _delta(a, b, w):
    d = b - a
    return d - w * np.round(d / w)


def _nearest(src, dst, w):
    """For each src point, vector to nearest dst point + distance. src:(A,2) dst:(B,2)."""
    if dst.shape[0] == 0:
        return None, None, None
    d = _delta(src[:, None, :], dst[None, :, :], w)
    dist = np.linalg.norm(d, axis=2)
    nn = np.argmin(dist, axis=1)
    a = np.arange(src.shape[0])
    return d[a, nn], dist[a, nn], nn


def _sense(vec, dist, head):
    """Body-frame (ahead, left, proximity) of a target given world vector + heading."""
    bearing = np.arctan2(vec[:, 1], vec[:, 0]) - head
    return np.cos(bearing), np.sin(bearing), 1.0 / (1.0 + dist)


def run(cfg: PredEcoConfig, seed: int = 0, record_every: int = 0):
    rng = np.random.default_rng(seed)
    prey_spec = BrainSpec(PREY_IN, cfg.n_hidden, N_OUT)
    pred_spec = BrainSpec(PRED_IN, cfg.n_hidden, N_OUT)

    def init(np_, spec, n0, e0, w):
        g = rng.normal(0, 0.25, (np_, spec.n_weights))   # small init -> near-random behavior to start
        pos = rng.uniform(0, cfg.world, (np_, 2))
        head = rng.uniform(-np.pi, np.pi, np_)
        energy = np.full(np_, e0)
        alive = np.zeros(np_, bool); alive[:n0] = True
        gen = np.zeros(np_, int)
        return dict(g=g, pos=pos, head=head, energy=energy, alive=alive, gen=gen)

    prey = init(cfg.max_prey, prey_spec, cfg.init_prey, cfg.prey_e_start, cfg.world)
    pred = init(cfg.max_pred, pred_spec, cfg.init_pred, cfg.pred_e_start, cfg.world)
    food = rng.uniform(0, cfg.world, (cfg.food_max, 2))
    food_on = np.ones(cfg.food_max, bool)

    def move(grp, spec, x, idx, speed, base, movec):
        out = forward(grp["g"][idx], spec, x)
        turn = np.tanh(out[:, 0]) * cfg.max_turn
        thrust = (np.tanh(out[:, 1]) * 0.5 + 0.5) * speed
        grp["head"][idx] = grp["head"][idx] + turn
        stepv = np.stack([np.cos(grp["head"][idx]), np.sin(grp["head"][idx])], axis=1) * thrust[:, None]
        grp["pos"][idx] = _wrap(grp["pos"][idx] + stepv, cfg.world)
        grp["energy"][idx] -= base + movec * thrust
        return thrust

    def reproduce(grp, spec, e_repro):
        idx = np.where(grp["alive"])[0]
        par = idx[grp["energy"][idx] >= e_repro]
        free = np.where(~grp["alive"])[0]
        n = min(par.size, free.size)
        if n == 0:
            return
        par = par[:n]; ch = free[:n]
        grp["energy"][par] *= 0.5
        grp["energy"][ch] = grp["energy"][par]
        nw = spec.n_weights
        grp["g"][ch] = grp["g"][par] + rng.normal(0, cfg.mut_sigma, (n, nw)) * (rng.random((n, nw)) < cfg.mut_rate)
        grp["pos"][ch] = _wrap(grp["pos"][par] + rng.normal(0, 2.0, (n, 2)), cfg.world)
        grp["head"][ch] = rng.uniform(-np.pi, np.pi, n)
        grp["gen"][ch] = grp["gen"][par] + 1
        grp["alive"][ch] = True

    hist = {"t": [], "prey": [], "pred": [], "evasion": [], "pursuit": []}
    snaps = []

    for t in range(cfg.steps):
        pidx = np.where(prey["alive"])[0]
        qidx = np.where(pred["alive"])[0]
        if pidx.size == 0:
            break
        on = np.where(food_on)[0]
        fpos = food[on]
        evasion = np.nan; pursuit = np.nan

        # ---- prey sense food (+) and nearest predator (flee) ----
        if pidx.size:
            fa = np.zeros(pidx.size); fl = np.zeros(pidx.size); fp = np.zeros(pidx.size)
            if fpos.shape[0]:
                v, d, _ = _nearest(prey["pos"][pidx], fpos, cfg.world)
                fa, fl, fp = _sense(v, d, prey["head"][pidx])
            pa = np.zeros(pidx.size); pl = np.zeros(pidx.size); pp = np.zeros(pidx.size)
            pred_bearing = None
            if qidx.size:
                v, d, _ = _nearest(prey["pos"][pidx], pred["pos"][qidx], cfg.world)
                pa, pl, pp = _sense(v, d, prey["head"][pidx])
                pred_bearing = (pa, pp)
            x = np.stack([fa, fl, fp, pa, pl, pp,
                          np.clip(prey["energy"][pidx] / cfg.prey_e_repro, 0, 2)], axis=1)
            thrust = move(prey, prey_spec, x, pidx, cfg.prey_speed, cfg.prey_base_cost, cfg.prey_move_cost)
            if pred_bearing is not None:
                # evasion: moving AWAY from the predator (predator behind you)
                evasion = float(np.mean((thrust > 0.05) * (-pred_bearing[0])))

        # ---- prey eat food ----
        pidx = np.where(prey["alive"])[0]
        if pidx.size and fpos.shape[0]:
            v, d, nn = _nearest(prey["pos"][pidx], fpos, cfg.world)
            can = np.where(d < cfg.prey_eat_radius)[0]
            for e in can[np.argsort(d[can])]:
                fi = on[nn[e]]
                if food_on[fi]:
                    food_on[fi] = False
                    prey["energy"][pidx[e]] += cfg.food_energy

        # ---- predators sense + chase nearest prey ----
        qidx = np.where(pred["alive"])[0]
        pidx = np.where(prey["alive"])[0]
        if qidx.size:
            ra = np.zeros(qidx.size); rl = np.zeros(qidx.size); rp = np.zeros(qidx.size)
            if pidx.size:
                v, d, nn = _nearest(pred["pos"][qidx], prey["pos"][pidx], cfg.world)
                ra, rl, rp = _sense(v, d, pred["head"][qidx])
            x = np.stack([ra, rl, rp, np.clip(pred["energy"][qidx] / cfg.pred_e_repro, 0, 2)], axis=1)
            thrust = move(pred, pred_spec, x, qidx, cfg.pred_speed, cfg.pred_base_cost, cfg.pred_move_cost)
            if pidx.size:
                pursuit = float(np.mean((thrust > 0.05) * ra))
                # ---- catches ----
                v, d, nn = _nearest(pred["pos"][qidx], prey["pos"][pidx], cfg.world)
                # prey sheltering in the central refuge cannot be caught (Huffaker floor)
                rc = cfg.world / 2.0
                in_refuge = np.linalg.norm(_delta(prey["pos"][pidx],
                                                   np.array([[rc, rc]]), cfg.world), axis=1) < cfg.refuge_radius
                can = np.where(d < cfg.catch_radius)[0]
                eaten = set()
                for e in can[np.argsort(d[can])]:
                    target = pidx[nn[e]]
                    if target in eaten or not prey["alive"][target] or in_refuge[nn[e]]:
                        continue
                    eaten.add(target)
                    prey["alive"][target] = False
                    pred["energy"][qidx[e]] += cfg.prey_energy_to_pred

        # ---- deaths ----
        for grp in (prey, pred):
            a = np.where(grp["alive"])[0]
            grp["alive"][a[grp["energy"][a] <= 0]] = False

        # ---- reproduction ----
        reproduce(prey, prey_spec, cfg.prey_e_repro)
        reproduce(pred, pred_spec, cfg.pred_e_repro)

        # ---- food respawn ----
        off = np.where(~food_on)[0]
        if off.size:
            k = min(cfg.food_spawn, off.size)
            food[off[:k]] = rng.uniform(0, cfg.world, (k, 2))
            food_on[off[:k]] = True

        if t % 50 == 0:
            hist["t"].append(t)
            hist["prey"].append(int(prey["alive"].sum()))
            hist["pred"].append(int(pred["alive"].sum()))
            hist["evasion"].append(evasion)
            hist["pursuit"].append(pursuit)
        if record_every and t % record_every == 0:
            pa = np.where(prey["alive"])[0]; qa = np.where(pred["alive"])[0]
            snaps.append({"t": t, "prey": prey["pos"][pa].copy(), "preyh": prey["head"][pa].copy(),
                          "pred": pred["pos"][qa].copy(), "predh": pred["head"][qa].copy(),
                          "food": food[food_on].copy()})

    out = {k: np.array(v, dtype=float) for k, v in hist.items()}
    out["snaps"] = snaps
    return out
