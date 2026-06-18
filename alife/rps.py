"""R39 — rock-paper-scissors: space keeps biodiversity alive.

Three species in a non-transitive loop: rock crushes scissors, scissors cut paper,
paper covers rock. No species is best — each is beaten by one and beats another.
Well-mixed, such a community is fragile: fluctuations send it spiralling until one
species fixates and the cycle dies. But on a lattice, where each cell only invades
its neighbours, the three lock into interwoven, ever-churning domains and coexist
indefinitely. Local dispersal preserves diversity that global mixing destroys.
(A synchronous random-neighbour rule; the empty-site May-Leonard variant produces
the crisper rotating spirals, but the coexistence-vs-fixation result is the same.)

Kerr, Riley, Feldman & Bohannan (2002); Reichenbach, Mobilia & Frey (2007). The
model: a grid of {rock, paper, scissors}; each step every cell may be invaded by a
randomly chosen neighbour of the type that dominates it. The control replaces the
neighbour with a random cell from anywhere (well-mixed).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# type t is dominated (invaded) by type (t+1)%3:  rock(0)<-paper(1)<-scissors(2)<-rock(0)


@dataclass(frozen=True)
class RPSConfig:
    size: int = 120
    steps: int = 300


def _random_neighbour_type(grid: np.ndarray, rng) -> np.ndarray:
    """For each cell, the type of one randomly chosen von-Neumann neighbour (torus)."""
    ups = np.roll(grid, 1, 0); dns = np.roll(grid, -1, 0)
    lfs = np.roll(grid, 1, 1); rgs = np.roll(grid, -1, 1)
    choice = rng.integers(0, 4, grid.shape)
    out = ups.copy()
    out = np.where(choice == 1, dns, out)
    out = np.where(choice == 2, lfs, out)
    out = np.where(choice == 3, rgs, out)
    return out


def _random_global_type(grid: np.ndarray, rng) -> np.ndarray:
    """For each cell, the type of a random cell anywhere (well-mixed control)."""
    flat = grid.ravel()
    pick = rng.integers(0, flat.size, grid.shape)
    return flat[pick]


def run(cfg: RPSConfig, well_mixed: bool = False, seed: int = 0):
    rng = np.random.default_rng(seed)
    grid = rng.integers(0, 3, (cfg.size, cfg.size))
    fracs = [[float((grid == k).mean()) for k in range(3)]]
    snaps = {0: grid.copy()}
    for t in range(1, cfg.steps + 1):
        opp = _random_global_type(grid, rng) if well_mixed else _random_neighbour_type(grid, rng)
        invaded = opp == (grid + 1) % 3        # the chosen opponent dominates this cell
        grid = np.where(invaded, opp, grid)
        fracs.append([float((grid == k).mean()) for k in range(3)])
        if t in (20, 80, cfg.steps):
            snaps[t] = grid.copy()
    return {"fractions": np.array(fracs), "snaps": snaps, "final": grid}


def diversity(result) -> float:
    """Min species fraction at the end — >0 means all three coexist."""
    return float(result["fractions"][-1].min())
