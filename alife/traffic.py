"""R86 — Nagel-Schreckenberg traffic: phantom jams that emerge from nothing.

A self-organization model with a famous everyday consequence. Cars on a single-lane ring move by
four local rules each step: ACCELERATE (v→v+1 up to v_max), BRAKE to the gap ahead (no crashes),
randomly DAWDLE (v→v-1 with probability p — the one stochastic ingredient), then MOVE. With no
bottleneck, no accident, no cause, traffic jams nucleate spontaneously above a critical density and
propagate BACKWARD against the flow as stop-and-go waves (Nagel & Schreckenberg 1992). Sweeping
density gives the fundamental diagram of traffic flow: throughput climbs with density up to a
critical point, then collapses into congestion. Emergent gridlock from purely local driving.

Pure numpy/CPU; cars as sorted positions + integer velocities on a ring.
"""

from __future__ import annotations

import numpy as np


def simulate(road=400, n_cars=80, vmax=5, p=0.3, steps=400, seed=0, record=True):
    """Run NS on a ring road. Returns spacetime occupancy (steps x road; -1 empty else velocity),
    the per-step flow (mean velocity), and mean steady-state flow."""
    rng = np.random.default_rng(seed)
    pos = np.sort(rng.choice(road, n_cars, replace=False))
    vel = np.zeros(n_cars, dtype=np.int64)
    space = np.full((steps, road), -1, dtype=np.int64) if record else None
    flow = np.empty(steps)
    for t in range(steps):
        order = np.argsort(pos)
        pos, vel = pos[order], vel[order]
        gap = (np.roll(pos, -1) - pos - 1) % road        # empty cells to the car ahead
        vel = np.minimum(vel + 1, vmax)                  # 1. accelerate
        vel = np.minimum(vel, gap)                       # 2. brake to avoid collision
        dawdle = rng.random(n_cars) < p                  # 3. random slowdown
        vel = np.where(dawdle, np.maximum(vel - 1, 0), vel)
        pos = (pos + vel) % road                         # 4. move
        flow[t] = vel.mean()                             # cars*cells advanced / car = mean velocity
        if record:
            space[t, pos] = vel
    burn = steps // 2
    return {"space": space, "flow": flow, "mean_flow": float(flow[burn:].mean()),
            "density": n_cars / road}


def fundamental_diagram(road=400, vmax=5, p=0.3, densities=None, steps=400, seed=0, reps=4):
    """Steady-state throughput (cars passing a point per step = density * mean velocity) vs density,
    averaged over `reps` seeds per density to suppress single-run noise into a clean triangle."""
    rng = np.random.default_rng(seed)
    densities = np.asarray(densities) if densities is not None else np.linspace(0.02, 0.9, 23)
    flows = []
    for d in densities:
        n = max(1, int(d * road))
        js = [(n / road) * simulate(road, n, vmax, p, steps, seed=int(rng.integers(1 << 30)),
                                    record=False)["mean_flow"] for _ in range(reps)]
        flows.append(float(np.mean(js)))                  # throughput J = rho * <v>
    return np.asarray(densities, float), np.asarray(flows)


def jam_fraction(space):
    """Fraction of car-states that are stopped/slow (velocity <= 1) — a proxy for jamming."""
    cars = space[space >= 0]
    return float(np.mean(cars <= 1)) if cars.size else 0.0


def jam_wave_velocity(space, maxlag=8):
    """Mean propagation speed (cells/step) of stopped-car clusters, via best spatial lag aligning
    the stopped field between consecutive rows. Negative => jam moves BACKWARD against traffic."""
    stopped = (space == 0).astype(float)
    stopped -= stopped.mean(axis=1, keepdims=True)
    lags = np.arange(-maxlag, maxlag + 1)
    disp = []
    for t in range(len(stopped) - 1):
        corr = [np.dot(stopped[t], np.roll(stopped[t + 1], int(L))) for L in lags]
        disp.append(-lags[int(np.argmax(corr))])      # displacement = -(best roll lag)
    return float(np.mean(disp)) if disp else 0.0
