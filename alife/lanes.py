"""R128 — Lane formation: two crowds walking through each other spontaneously sort into lanes.

Push two streams of people (or driven colloids, or ants, or charged grains) in OPPOSITE directions
through the same space and something orderly happens for free: instead of a turbulent jam, they
segregate into smooth LANES, each lane carrying one direction. No one plans it — a +x walker who drifts
into the on-coming -x stream gets bumped sideways more than one already among its own kind, so same-
direction walkers accrete into stripes parallel to the flow. It is a textbook non-equilibrium
self-organisation (Helbing's pedestrian model; driven binary colloids), and you see it instantly: a
mixed salt-and-pepper crowd resolves into clean bands of two colours.

Model: overdamped particles in a periodic box; each is DRIVEN at constant force along +x or -x by its
species, repels close neighbours with a soft force, and feels noise. Lanes emerge above enough
density / below enough noise; remove the drive and the two species stay mixed. The lane order parameter
(mean species purity within transverse stripes) is ~1 for clean lanes, ~0 for a 50/50 mix. Neighbour
repulsion uses a periodic KD-tree (O(N log N)). Pure numpy/scipy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree


@dataclass(frozen=True)
class LaneConfig:
    N: int = 800
    L: float = 44.0
    v0: float = 1.0           # drive strength (0 = no drive -> stays mixed)
    A: float = 2.0            # soft repulsion strength
    r0: float = 1.5           # repulsion range
    noise: float = 0.3        # thermal noise (large -> lanes melt)
    dt: float = 0.02
    steps: int = 4000
    seed: int = 0


def init(cfg: LaneConfig, rng):
    pos = rng.uniform(0, cfg.L, (cfg.N, 2))
    species = np.where(np.arange(cfg.N) < cfg.N // 2, 1.0, -1.0)   # +x and -x streams
    return pos, species


def step(pos, species, cfg: LaneConfig, rng):
    L = cfg.L
    F = np.zeros((cfg.N, 2))
    pairs = cKDTree(pos % L, boxsize=L).query_pairs(cfg.r0, output_type="ndarray")
    if len(pairs):
        i, j = pairs[:, 0], pairs[:, 1]
        d = pos[i] - pos[j]
        d -= L * np.round(d / L)
        r = np.maximum(np.sqrt((d ** 2).sum(1)), 1e-6)
        f = (cfg.A * (1 - r / cfg.r0) / r)[:, None] * d
        np.add.at(F, i, f)
        np.add.at(F, j, -f)
    vx = cfg.v0 * species + F[:, 0] + cfg.noise * rng.standard_normal(cfg.N)
    vy = F[:, 1] + cfg.noise * rng.standard_normal(cfg.N)
    pos = pos + cfg.dt * np.column_stack([vx, vy])
    return pos % L, species


def lane_order(pos, species, L, nbins=22) -> float:
    """Mean species purity within transverse (y) stripes: ~1 clean lanes, ~0 fully mixed."""
    yb = (pos[:, 1] / L * nbins).astype(int) % nbins
    phi = []
    for b in range(nbins):
        m = yb == b
        if m.sum() > 2:
            phi.append(abs(species[m].mean()))
    return float(np.mean(phi)) if phi else 0.0


def run(cfg: LaneConfig, record_every: int = 0):
    rng = np.random.default_rng(cfg.seed)
    pos, species = init(cfg, rng)
    order, snaps = [], []
    for t in range(cfg.steps):
        pos, species = step(pos, species, cfg, rng)
        order.append(lane_order(pos, species, cfg.L))
        if record_every and (t % record_every == 0 or t == cfg.steps - 1):
            snaps.append((pos.copy(), species.copy()))
    return {"pos": pos, "species": species, "order": np.asarray(order), "snaps": snaps}
