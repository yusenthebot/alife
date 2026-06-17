"""R31 — evolving morphology: virtual creatures that evolve a body AND a gait.

Every brain so far drove a fixed point or sphere. Here the creature's *form*
evolves too. A creature is a cluster of point masses joined by springs in a
2D world with gravity, ground contact and friction. Some springs are muscles:
they rhythmically lengthen and shorten. The genome encodes the body (where the
masses sit) and the gait (each muscle's amplitude and phase). Selection rewards
one thing — horizontal distance travelled — and nothing says *how* to move.

Random blobs twitch in place; over generations they evolve into things that
crawl, inch and hop. This is Karl Sims' evolved virtual creatures (1994), in 2D.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

N_NODES = 6


def _pairs(n: int):
    I, J = np.triu_indices(n, k=1)
    return I, J            # the M = n(n-1)/2 springs of a complete graph


I_IDX, J_IDX = _pairs(N_NODES)
M_SPRINGS = I_IDX.size


def _incidence(n: int, I, J) -> np.ndarray:
    B = np.zeros((n, I.size))
    B[I, np.arange(I.size)] = 1.0
    B[J, np.arange(J.size)] = -1.0
    return B


B_INC = _incidence(N_NODES, I_IDX, J_IDX)


@dataclass(frozen=True)
class MorphConfig:
    steps: int = 400
    dt: float = 0.02
    k_spring: float = 80.0
    k_ground: float = 600.0
    gravity: float = 30.0
    mass: float = 1.0
    damping: float = 0.06       # velocity damping per second
    friction: float = 0.9       # ground friction coefficient
    omega: float = 6.0          # gait angular frequency
    max_amp: float = 0.6        # muscle length modulation (fraction of rest length)
    v_clip: float = 25.0
    pop: int = 200
    generations: int = 120
    elite_frac: float = 0.1
    parent_frac: float = 0.3
    mut_rate: float = 0.25
    mut_sigma: float = 0.25


GENOME = 2 * N_NODES + 2 * M_SPRINGS    # node xy + per-spring amplitude + phase


def random_genomes(p: int, rng: np.random.Generator) -> np.ndarray:
    g = np.zeros((p, GENOME))
    g[:, : 2 * N_NODES] = rng.uniform(-1, 1, (p, 2 * N_NODES))          # body layout
    g[:, 2 * N_NODES: 2 * N_NODES + M_SPRINGS] = rng.uniform(-1, 1, (p, M_SPRINGS))  # amp
    g[:, 2 * N_NODES + M_SPRINGS:] = rng.uniform(-np.pi, np.pi, (p, M_SPRINGS))      # phase
    return g


def mutate(g: np.ndarray, rng: np.random.Generator, rate: float, sigma: float) -> np.ndarray:
    noise = rng.normal(0, sigma, g.shape) * (rng.random(g.shape) < rate)
    return g + noise


def _decode(g: np.ndarray, cfg: MorphConfig):
    """-> (init_pos:(P,N,2), amp:(P,M), phase:(P,M))."""
    p = g.shape[0]
    pos = g[:, : 2 * N_NODES].reshape(p, N_NODES, 2) * 1.2
    pos = pos - pos.min(axis=1, keepdims=True)        # lift so min y >= 0
    pos[:, :, 1] += 0.3                                # small clearance above ground
    amp = np.tanh(g[:, 2 * N_NODES: 2 * N_NODES + M_SPRINGS]) * cfg.max_amp
    phase = g[:, 2 * N_NODES + M_SPRINGS:]
    return pos, amp, phase


def simulate(g: np.ndarray, cfg: MorphConfig, record: bool = False):
    """Roll out a batch of creatures. Returns horizontal COM displacement (P,).
    If record, also returns a list of position frames for the FIRST creature."""
    pos, amp, phase = _decode(g, cfg)
    P = g.shape[0]
    vel = np.zeros((P, N_NODES, 2))
    # rest lengths from the initial body geometry
    d0 = pos[:, J_IDX] - pos[:, I_IDX]
    L0 = np.linalg.norm(d0, axis=2) + 1e-6           # (P,M)
    com0 = pos[:, :, 0].mean(axis=1)
    damp_step = max(0.0, 1.0 - cfg.damping * cfg.dt)
    frames = []
    for t in range(cfg.steps):
        L = L0 * (1.0 + amp * np.sin(cfg.omega * t * cfg.dt + phase))
        d = pos[:, J_IDX] - pos[:, I_IDX]            # (P,M,2)
        dist = np.linalg.norm(d, axis=2) + 1e-6
        fmag = cfg.k_spring * (dist - L)             # (P,M) tension>0 pulls together
        fpair = (fmag / dist)[:, :, None] * d        # force on node I toward J
        F = np.einsum("nm,pmc->pnc", B_INC, fpair)   # scatter to nodes via incidence
        F[:, :, 1] -= cfg.gravity * cfg.mass
        # ground contact at y=0
        pen = np.clip(-pos[:, :, 1], 0, None)        # penetration depth
        fn = cfg.k_ground * pen                       # normal force up
        F[:, :, 1] += fn
        F[:, :, 0] -= cfg.friction * fn * np.sign(vel[:, :, 0])   # Coulomb-ish friction
        vel = (vel + F / cfg.mass * cfg.dt) * damp_step
        np.clip(vel, -cfg.v_clip, cfg.v_clip, out=vel)
        pos = pos + vel * cfg.dt
        if record:
            frames.append(pos[0].copy())
    com1 = pos[:, :, 0].mean(axis=1)
    disp = com1 - com0
    if record:
        return disp, frames, L0[0]
    return disp


def fitness(g: np.ndarray, cfg: MorphConfig) -> np.ndarray:
    """Locomotion: absolute horizontal distance travelled (either direction counts)."""
    return np.abs(simulate(g, cfg))


def evolve(cfg: MorphConfig, seed: int = 0):
    rng = np.random.default_rng(seed)
    g = random_genomes(cfg.pop, rng)
    n_elite = max(1, int(cfg.elite_frac * cfg.pop))
    n_parent = max(2, int(cfg.parent_frac * cfg.pop))
    best_hist, mean_hist = [], []
    best_g = g[0].copy()
    for _ in range(cfg.generations):
        fit = fitness(g, cfg)
        order = np.argsort(fit)[::-1]
        best_hist.append(float(fit[order[0]])); mean_hist.append(float(fit.mean()))
        best_g = g[order[0]].copy()
        elite = g[order[:n_elite]]
        parents = g[order[:n_parent]]
        kids = mutate(parents[rng.integers(0, n_parent, cfg.pop - n_elite)],
                      rng, cfg.mut_rate, cfg.mut_sigma)
        g = np.vstack([elite, kids])
    return {"best": np.array(best_hist), "mean": np.array(mean_hist), "best_genome": best_g}
