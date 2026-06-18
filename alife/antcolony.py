"""R65 — Ant-colony foraging: stigmergy builds trails and finds the shortest path.

No ant knows where the food is or how to get there efficiently. Each one just wanders,
and — once it has found food — lays a chemical trail on the way home while heading back by
dead-reckoning; searching ants probabilistically follow that trail. From this purely local
rule (deposit + follow + evaporate) a foraging HIGHWAY self-organises between nest and food,
and — the Deneubourg double-bridge result — when two routes exist the colony converges on
the SHORTER one: ants on the short route complete the round trip faster, so they reinforce
it faster, and positive feedback locks it in. Collective optimisation with no optimiser.

Two models here: a spatial grid colony (the emergent trail) and the abstract binary-bridge
(the shortest-path phase transition + symmetry-breaking control). Pure numpy/CPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# ----------------------------------------------------------------------------- spatial colony

@dataclass(frozen=True)
class AntConfig:
    size: int = 200
    n_ants: int = 500
    speed: float = 1.4
    sensor_dist: float = 7.0
    sensor_angle: float = 0.6        # rad, left/right sensor offset
    wiggle: float = 0.45             # rad random turn while searching
    deposit: float = 24.0            # trail laid per step by a homing (laden) ant
    evaporate: float = 0.012         # fraction of pheromone lost per step
    diffuse: float = 0.10            # diffusion coefficient
    nest_radius: float = 7.0
    food_radius: float = 7.0


def _sample(field, x, y):
    N = field.shape[0]
    xi = np.clip(x.astype(int), 0, N - 1)
    yi = np.clip(y.astype(int), 0, N - 1)
    return field[yi, xi]


def _laplacian(a):
    return (np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1) - 4 * a)


def simulate(cfg: AntConfig, steps: int, nest=None, foods=None, seed: int = 0, record_every: int = 0):
    rng = np.random.default_rng(seed)
    N = cfg.size
    nest = np.array(nest if nest is not None else (N * 0.5, N * 0.15), float)
    foods = np.array(foods if foods is not None else [(N * 0.5, N * 0.85)], float)
    x = nest[0] + rng.normal(0, 3, cfg.n_ants)
    y = nest[1] + rng.normal(0, 3, cfg.n_ants)
    head = rng.uniform(0, 2 * np.pi, cfg.n_ants)
    laden = np.zeros(cfg.n_ants, bool)
    trail = np.zeros((N, N))
    delivered = []
    snaps = {}
    total_delivered = 0
    for t in range(steps):
        # --- searching ants: follow trail (3 sensors), else wander ---
        srch = ~laden
        cx = x + cfg.sensor_dist * np.cos(head)
        cy = y + cfg.sensor_dist * np.sin(head)
        lx = x + cfg.sensor_dist * np.cos(head + cfg.sensor_angle)
        ly = y + cfg.sensor_dist * np.sin(head + cfg.sensor_angle)
        rx = x + cfg.sensor_dist * np.cos(head - cfg.sensor_angle)
        ry = y + cfg.sensor_dist * np.sin(head - cfg.sensor_angle)
        sc, sl, sr = _sample(trail, cx, cy), _sample(trail, lx, ly), _sample(trail, rx, ry)
        turn = np.zeros(cfg.n_ants)
        turn = np.where((sl > sc) & (sl >= sr), cfg.sensor_angle, turn)
        turn = np.where((sr > sc) & (sr > sl), -cfg.sensor_angle, turn)
        on_trail = np.maximum.reduce([sc, sl, sr]) > 0.5
        head = np.where(srch & on_trail, head + turn, head)
        head = np.where(srch & ~on_trail, head + rng.uniform(-cfg.wiggle, cfg.wiggle, cfg.n_ants), head)

        # --- laden ants: dead-reckon home, deposit trail ---
        desired = np.arctan2(nest[1] - y, nest[0] - x)
        dh = (desired - head + np.pi) % (2 * np.pi) - np.pi
        head = np.where(laden, head + 0.5 * dh + rng.uniform(-0.1, 0.1, cfg.n_ants), head)

        x = x + cfg.speed * np.cos(head)
        y = y + cfg.speed * np.sin(head)
        # reflect at walls
        offx = (x < 1) | (x > N - 2); offy = (y < 1) | (y > N - 2)
        head = np.where(offx | offy, head + np.pi, head)
        x = np.clip(x, 1, N - 2); y = np.clip(y, 1, N - 2)

        if laden.any():
            lx_, ly_ = x[laden].astype(int), y[laden].astype(int)
            np.add.at(trail, (ly_, lx_), cfg.deposit)

        # --- pick up / drop off ---
        for fx, fy in foods:
            hit = (~laden) & ((x - fx) ** 2 + (y - fy) ** 2 < cfg.food_radius ** 2)
            laden = laden | hit
            head = np.where(hit, head + np.pi, head)
        home = laden & ((x - nest[0]) ** 2 + (y - nest[1]) ** 2 < cfg.nest_radius ** 2)
        n_home = int(home.sum())
        if n_home:
            total_delivered += n_home
            laden = laden & ~home
            head = np.where(home, rng.uniform(0, 2 * np.pi, cfg.n_ants), head)

        trail *= (1 - cfg.evaporate)
        trail += cfg.diffuse * _laplacian(trail)
        np.clip(trail, 0, None, out=trail)
        delivered.append(total_delivered)
        if record_every and (t % record_every == 0 or t == steps - 1):
            snaps[t] = (trail.copy(), x.copy(), y.copy(), laden.copy())
    return {"trail": trail, "x": x, "y": y, "laden": laden, "delivered": np.array(delivered),
            "snaps": snaps, "nest": nest, "foods": foods}


def trail_strength(trail, nest, food, width: int = 6) -> float:
    """Mean pheromone along the straight nest->food corridor (a proxy for 'a trail exists')."""
    n = int(np.hypot(*(food - nest)))
    ts = np.linspace(0, 1, n)
    xs = (nest[0] + ts * (food[0] - nest[0])).astype(int)
    ys = (nest[1] + ts * (food[1] - nest[1])).astype(int)
    vals = []
    N = trail.shape[0]
    for dx in range(-width, width + 1):
        vals.append(trail[np.clip(ys, 0, N - 1), np.clip(xs + dx, 0, N - 1)])
    return float(np.mean(vals))


# ----------------------------------------------------------------------------- double bridge

def deneubourg_bridge(len_a: float, len_b: float, steps: int = 400, ants_per_step: int = 20,
                      k: float = 20.0, n: float = 2.0, q: float = 1.0, rho: float = 0.05,
                      seed: int = 0):
    """Abstract binary bridge (Deneubourg 1990). Each step a batch of ants picks branch i with
    prob (k+tau_i)^n / sum; branch i is reinforced at a rate proportional to traffic / length
    (shorter branch -> faster round trips -> more reinforcement); pheromone evaporates.
    Returns the time series of P(choose branch A)."""
    rng = np.random.default_rng(seed)
    tau = np.array([0.0, 0.0])
    lens = np.array([len_a, len_b], float)
    pa = []
    for _ in range(steps):
        w = (k + tau) ** n
        p = w / w.sum()
        pa.append(float(p[0]))
        choices = rng.multinomial(ants_per_step, p)         # ants on each branch this step
        tau = (1 - rho) * tau + q * choices / lens          # reinforcement ∝ traffic / length
    return np.array(pa)
