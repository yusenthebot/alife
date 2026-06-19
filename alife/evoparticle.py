"""R91 — Evolved Particle Life: selection discovers self-propelled matter.

R61 showed that an asymmetric force matrix makes particles self-assemble into life-like clusters,
with no fitness and no evolution. Here we close the loop: we EVOLVE the matrix. Because the matrix is
asymmetric (the force on i from j need not equal the force on j from i), interactions break Newton's
third law, so a population of particles can generate NET momentum — a "chaser" pair (i pursues j while
j flees i) drives itself forward. That makes locomotion a selectable trait. Starting from random
matrices that mostly make static blobs or gas, a genetic algorithm on the K x K matrix discovers
interaction laws whose swarms PROPEL THEMSELVES across the world — active matter, evolved from the
rules up.

Fitness = net displacement of the centre of mass (true unwrapped drift = integral of mean velocity).
Compact CPU sim (scipy cKDTree); small worlds so a whole GA runs in a couple of minutes.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree


@dataclass(frozen=True)
class EvoConfig:
    n: int = 500
    types: int = 4
    world: float = 320.0
    r_max: float = 30.0
    r_inner: float = 9.0
    force: float = 0.7
    friction: float = 0.86
    dt: float = 1.0
    steps: int = 200


def _profile(d, fij, r_inner, r_max):
    f = np.zeros_like(d)
    near = d < r_inner
    f[near] = (d[near] / max(r_inner, 1e-6) - 1.0)
    mid = (~near) & (d < r_max)
    x = (d[mid] - r_inner) / (r_max - r_inner)
    f[mid] = fij[mid] * (1.0 - np.abs(2.0 * x - 1.0))
    return f


def motility(matrix, cfg=EvoConfig(), seed=0, return_traj=False):
    """Run the sim; return net centre-of-mass drift (self-propulsion). Optionally the CoM trajectory."""
    rng = np.random.default_rng(seed)
    pos = rng.uniform(0, cfg.world, (cfg.n, 2))
    vel = np.zeros((cfg.n, 2))
    typ = rng.integers(0, cfg.types, cfg.n)
    com = np.zeros(2)
    traj = [com.copy()] if return_traj else None
    for _ in range(cfg.steps):
        tree = cKDTree(pos, boxsize=cfg.world)
        pairs = tree.query_pairs(cfg.r_max, output_type="ndarray")
        acc = np.zeros_like(pos)
        if len(pairs):
            i, j = pairs[:, 0], pairs[:, 1]
            d = pos[j] - pos[i]
            d -= cfg.world * np.round(d / cfg.world)
            dist = np.linalg.norm(d, axis=1) + 1e-9
            u = d / dist[:, None]
            mag_i = _profile(dist, matrix[typ[i], typ[j]], cfg.r_inner, cfg.r_max)
            mag_j = _profile(dist, matrix[typ[j], typ[i]], cfg.r_inner, cfg.r_max)
            np.add.at(acc, i, mag_i[:, None] * u)
            np.add.at(acc, j, mag_j[:, None] * (-u))
        vel = (vel + cfg.force * acc * cfg.dt) * cfg.friction
        pos = np.mod(pos + vel * cfg.dt, cfg.world)
        com = com + vel.mean(axis=0) * cfg.dt                 # unwrapped CoM drift
        if return_traj:
            traj.append(com.copy())
    drift = float(np.linalg.norm(com))
    if return_traj:
        return drift, np.asarray(traj), (pos, typ)
    return drift


def chaser_matrix(types=4):
    """A hand-built self-propelling matrix: type 0 chases 1, 1 flees 0 (a moving 'cell')."""
    m = np.zeros((types, types))
    m[0, 1] = 1.0       # 0 attracted to 1 (pursues)
    m[1, 0] = -1.0      # 1 repelled by 0 (flees)
    m[0, 0] = 0.2       # mild self-cohesion keeps the chasers together
    m[1, 1] = 0.2
    return m


def evolve(cfg=EvoConfig(), gens=20, pop=20, mut=0.25, elite=3, seed=0, eval_seeds=2):
    """GA on the force matrix maximising motility. Returns best matrix + fitness history."""
    rng = np.random.default_rng(seed)
    population = [rng.uniform(-1, 1, (cfg.types, cfg.types)) for _ in range(pop)]

    def fit(m):
        return float(np.mean([motility(m, cfg, seed=s) for s in range(eval_seeds)]))

    best_hist, mean_hist, best_m, best_f = [], [], None, -1.0
    for _ in range(gens):
        fits = np.array([fit(m) for m in population])
        order = np.argsort(fits)[::-1]
        if fits[order[0]] > best_f:
            best_f = float(fits[order[0]]); best_m = population[order[0]].copy()
        best_hist.append(float(fits[order[0]])); mean_hist.append(float(fits.mean()))
        elites = [population[i].copy() for i in order[:elite]]
        children = []
        while len(children) < pop - elite:
            a, b = elites[rng.integers(elite)], elites[rng.integers(elite)]
            mask = rng.random((cfg.types, cfg.types)) < 0.5
            child = np.where(mask, a, b) + rng.normal(0, mut, (cfg.types, cfg.types))
            children.append(np.clip(child, -1, 1))
        population = elites + children
    return {"best_matrix": best_m, "best_fitness": best_f,
            "best_hist": np.asarray(best_hist), "mean_hist": np.asarray(mean_hist)}


def random_baseline(cfg=EvoConfig(), n=40, seed=0):
    """Distribution of motility over random matrices — the bar evolution must beat."""
    rng = np.random.default_rng(seed)
    return np.array([motility(rng.uniform(-1, 1, (cfg.types, cfg.types)), cfg, seed=1) for _ in range(n)])
