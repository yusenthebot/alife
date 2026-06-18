"""R35 — evolution in a changing world: tracking a flipping environment.

A living foraging world (in the spirit of R33, no GA) with TWO kinds of food,
red and blue. Only one kind is nutritious at a time; the other is inert. Which
one nourishes FLIPS every season. Creatures sense both kinds and evolve to chase
whichever currently pays — but when the valence flips, the whole population is
suddenly adapted to the wrong food and must re-evolve.

The signature is a sawtooth: mean intake (and the fraction of meals taken from
the good kind) collapses at every flip and climbs back as selection re-shapes the
population. Evolution never finishes here, because the target keeps moving — open-
ended adaptation driven by a changing world, not by the experimenter.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from alife.brain import BrainSpec, forward

N_IN = 6    # [red_ahead, red_left, red_prox, blue_ahead, blue_left, blue_prox]
N_OUT = 2   # [turn, thrust]


@dataclass(frozen=True)
class SeasonConfig:
    world: float = 100.0
    max_pop: int = 700
    n_hidden: int = 8
    init_pop: int = 150
    food_each: int = 90          # pellets of EACH colour present
    food_spawn: int = 3
    good_energy: float = 28.0
    bad_energy: float = -12.0    # the wrong colour is poison -> strong pressure to discriminate
    eat_radius: float = 2.5
    max_speed: float = 1.4
    max_turn: float = 0.6
    base_cost: float = 0.10
    move_cost: float = 0.10
    e_start: float = 30.0
    e_repro: float = 50.0
    mut_rate: float = 0.18
    mut_sigma: float = 0.35
    season_len: int = 4000       # steps before the nutritious colour flips
    steps: int = 20000


def _wrap(p, w):
    return np.mod(p, w)


def _delta(a, b, w):
    d = b - a
    return d - w * np.round(d / w)


def _nearest(src, dst, w):
    if dst.shape[0] == 0:
        return None, None, None
    d = _delta(src[:, None, :], dst[None, :, :], w)
    dist = np.linalg.norm(d, axis=2)
    nn = np.argmin(dist, axis=1)
    a = np.arange(src.shape[0])
    return d[a, nn], dist[a, nn], nn


def _sense(vec, dist, head):
    if vec is None:
        return None
    bearing = np.arctan2(vec[:, 1], vec[:, 0]) - head
    return np.cos(bearing), np.sin(bearing), 1.0 / (1.0 + dist)


def run(cfg: SeasonConfig, seed: int = 0, record_every: int = 0):
    rng = np.random.default_rng(seed)
    spec = BrainSpec(N_IN, cfg.n_hidden, N_OUT)
    nw = spec.n_weights
    P = cfg.max_pop

    genome = rng.normal(0, 0.5, (P, nw))
    pos = rng.uniform(0, cfg.world, (P, 2))
    head = rng.uniform(-np.pi, np.pi, P)
    energy = np.full(P, cfg.e_start)
    alive = np.zeros(P, bool); alive[: cfg.init_pop] = True

    # two food colours, each a fixed-size pellet set
    red = rng.uniform(0, cfg.world, (cfg.food_each, 2)); red_on = np.ones(cfg.food_each, bool)
    blue = rng.uniform(0, cfg.world, (cfg.food_each, 2)); blue_on = np.ones(cfg.food_each, bool)

    hist = {"t": [], "pop": [], "good_frac": [], "approach_bias": [], "intake": [], "good_is_red": []}
    snaps = []

    for t in range(cfg.steps):
        good_is_red = (t // cfg.season_len) % 2 == 0
        idx = np.where(alive)[0]
        if idx.size == 0:
            break

        ron = np.where(red_on)[0]; rpos = red[ron]
        bon = np.where(blue_on)[0]; bpos = blue[bon]

        rv, rd, rnn = _nearest(pos[idx], rpos, cfg.world)
        bv, bd, bnn = _nearest(pos[idx], bpos, cfg.world)
        rs = _sense(rv, rd, head[idx]); bs = _sense(bv, bd, head[idx])
        ra, rl, rp = rs if rs else (np.zeros(idx.size),) * 3
        ba, bl, bp = bs if bs else (np.zeros(idx.size),) * 3
        x = np.stack([ra, rl, rp, ba, bl, bp], axis=1)

        out = forward(genome[idx], spec, x)
        turn = np.tanh(out[:, 0]) * cfg.max_turn
        thrust = (np.tanh(out[:, 1]) * 0.5 + 0.5) * cfg.max_speed
        head[idx] = head[idx] + turn
        stepv = np.stack([np.cos(head[idx]), np.sin(head[idx])], axis=1) * thrust[:, None]
        pos[idx] = _wrap(pos[idx] + stepv, cfg.world)
        energy[idx] -= cfg.base_cost + cfg.move_cost * thrust
        # approach bias: steering toward the GOOD colour minus toward the BAD colour
        moving = thrust > 0.05
        cos_good = ra if good_is_red else ba
        cos_bad = ba if good_is_red else ra
        approach_bias = float(np.mean(moving * (cos_good - cos_bad))) if moving.any() else np.nan

        # eat whichever colour is within reach; only the good colour nourishes
        good_meals = 0; total_meals = 0; intake = 0.0
        for colour_red in (True, False):
            on = ron if colour_red else bon
            cpos = rpos if colour_red else bpos
            con = red_on if colour_red else blue_on
            nn_c = rnn if colour_red else bnn
            d_c = rd if colour_red else bd
            if cpos.shape[0] == 0:
                continue
            can = np.where(d_c < cfg.eat_radius)[0]
            for e in can[np.argsort(d_c[can])]:
                fi = on[nn_c[e]]
                if not con[fi]:
                    continue
                con[fi] = False
                is_good = (colour_red == good_is_red)
                energy[idx[e]] += cfg.good_energy if is_good else cfg.bad_energy
                total_meals += 1; good_meals += int(is_good); intake += cfg.good_energy * is_good

        # death
        idx = np.where(alive)[0]
        alive[idx[energy[idx] <= 0]] = False
        # reproduction
        idx = np.where(alive)[0]
        par = idx[energy[idx] >= cfg.e_repro]
        free = np.where(~alive)[0]
        n = min(par.size, free.size)
        if n:
            par = par[:n]; ch = free[:n]
            energy[par] *= 0.5; energy[ch] = energy[par]
            genome[ch] = genome[par] + rng.normal(0, cfg.mut_sigma, (n, nw)) * (rng.random((n, nw)) < cfg.mut_rate)
            pos[ch] = _wrap(pos[par] + rng.normal(0, 2.0, (n, 2)), cfg.world)
            head[ch] = rng.uniform(-np.pi, np.pi, n)
            alive[ch] = True
        # respawn eaten pellets (keep each colour's count up)
        for con, arr in ((red_on, red), (blue_on, blue)):
            off = np.where(~con)[0]
            if off.size:
                k = min(cfg.food_spawn, off.size)
                arr[off[:k]] = rng.uniform(0, cfg.world, (k, 2)); con[off[:k]] = True

        if t % 50 == 0:
            hist["t"].append(t)
            hist["pop"].append(int(alive.sum()))
            hist["good_frac"].append(good_meals / total_meals if total_meals else np.nan)
            hist["approach_bias"].append(approach_bias)
            hist["intake"].append(intake)
            hist["good_is_red"].append(1.0 if good_is_red else 0.0)
        if record_every and t % record_every == 0:
            a = np.where(alive)[0]
            snaps.append({"t": t, "good_is_red": good_is_red, "pos": pos[a].copy(),
                          "red": red[red_on].copy(), "blue": blue[blue_on].copy()})

    out = {k: np.array(v, dtype=float) for k, v in hist.items()}
    out["snaps"] = snaps
    return out
