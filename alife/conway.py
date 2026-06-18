"""R46 — Conway's Game of Life: complexity from three rules.

The most famous cellular automaton and a founding artifact of artificial life. Each
cell is alive or dead; in lockstep, a live cell survives with 2 or 3 live
neighbours and a dead cell is born with exactly 3. From those three rules come
still lifes, oscillators, gliders that crawl across the grid, and the Gosper
glider gun — a finite pattern that spits out an endless stream of gliders, proving
unbounded growth (the Life universe is Turing-complete and supports self-
replication). No genomes, no fitness; just local rules generating open-ended
structure — the cellular-automata root of the field.
"""

from __future__ import annotations

import numpy as np

# Gosper glider gun — live cells (row, col); emits a glider every 30 generations.
GOSPER_GUN = [
    (5, 1), (5, 2), (6, 1), (6, 2),
    (5, 11), (6, 11), (7, 11), (4, 12), (8, 12), (3, 13), (9, 13), (3, 14), (9, 14),
    (6, 15), (4, 16), (8, 16), (5, 17), (6, 17), (7, 17), (6, 18),
    (3, 21), (4, 21), (5, 21), (3, 22), (4, 22), (5, 22), (2, 23), (6, 23),
    (1, 25), (2, 25), (6, 25), (7, 25),
    (3, 35), (4, 35), (3, 36), (4, 36),
]
GLIDER = [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)]


def _neighbours(g: np.ndarray) -> np.ndarray:
    """Live-neighbour count with dead (zero-padded) boundaries."""
    p = np.pad(g.astype(np.int16), 1)
    h, w = g.shape
    return sum(p[i:i + h, j:j + w] for i in range(3) for j in range(3)) - g


def step(g: np.ndarray) -> np.ndarray:
    n = _neighbours(g)
    return ((g & ((n == 2) | (n == 3))) | (~g & (n == 3))).astype(bool)


def place(pattern, shape, offset=(0, 0)) -> np.ndarray:
    g = np.zeros(shape, dtype=bool)
    r0, c0 = offset
    for r, c in pattern:
        g[r0 + r, c0 + c] = True
    return g


def run(g: np.ndarray, steps: int, record_every: int = 0):
    pop = [int(g.sum())]
    snaps = {0: g.copy()}
    for t in range(1, steps + 1):
        g = step(g)
        pop.append(int(g.sum()))
        if record_every and t % record_every == 0:
            snaps[t] = g.copy()
    snaps[steps] = g.copy()
    return {"population": np.array(pop), "snaps": snaps, "final": g}


def random_soup(shape, density: float, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.random(shape) < density


def glider_gun(shape=(100, 100)) -> np.ndarray:
    return place(GOSPER_GUN, shape, offset=(1, 1))
