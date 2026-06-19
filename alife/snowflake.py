"""R119 — Snowflake growth: a six-fold crystal from a one-line local rule (Reiter's CA).

Every snowflake is six-fold symmetric, every one is different, and the SHAPE — flat plate, slender
needle, feathery dendrite — is set by the temperature and humidity it grew in (Nakaya's morphology
diagram, 1954). Reiter (2005) showed all of this falls out of a tiny cellular automaton on a hexagonal
lattice, with no global plan: water vapour diffuses across the plane, and wherever the growing ice
crystal (or its immediate neighbourhood) sits, vapour is captured and frozen. Two ingredients fight:
DIFFUSION (smooths, favours flat faces) and the instability at tips (a protruding tip sees more vapour,
so it grows faster and sharpens — the Mullins-Sekerka instability that makes dendrites). The balance,
tuned by one humidity parameter, sweeps the morphology from compact hexagonal plates (high vapour) to
branching dendrites (low vapour) — the same transition Nakaya mapped in real clouds.

Reiter's rules (per step): a cell is RECEPTIVE if it is frozen (s>=1) or touches a frozen cell.
Receptive cells hold their water and gain a constant addition gamma (vapour deposition); non-receptive
cells' water DIFFUSES (hexagonal Laplacian, rate alpha). Background cells start at humidity beta. The
six-fold symmetry is exact, inherited from the lattice. Pure numpy/CPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# the six neighbours of a hexagonal (axial) lattice embedded in a square array
NEIGHBORS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1))


@dataclass(frozen=True)
class SnowflakeConfig:
    L: int = 221
    alpha: float = 1.0       # diffusion rate
    beta: float = 0.4        # background vapour / humidity -- THE morphology knob
    gamma: float = 0.001     # constant vapour addition at the crystal
    steps: int = 400


def _hex_neighbor_sum(u):
    return sum(np.roll(np.roll(u, d0, 0), d1, 1) for d0, d1 in NEIGHBORS)


def grow(cfg: SnowflakeConfig):
    """Run Reiter's CA from a single frozen seed at the centre. Returns the final water field."""
    s = np.full((cfg.L, cfg.L), cfg.beta)
    c = cfg.L // 2
    s[c, c] = 1.0
    for _ in range(cfg.steps):
        frozen = s >= 1.0
        receptive = frozen.copy()
        for d0, d1 in NEIGHBORS:
            receptive |= np.roll(np.roll(frozen, d0, 0), d1, 1)
        u = np.where(receptive, 0.0, s)                       # only non-receptive water diffuses
        v = np.where(receptive, s + cfg.gamma, 0.0)           # receptive cells hold water + gain gamma
        u = u + (cfg.alpha / 2.0) * (_hex_neighbor_sum(u) / 6.0 - u)
        s = u + v
    return s


def frozen_mask(s):
    return s >= 1.0


def crystal_mass(s) -> int:
    return int(frozen_mask(s).sum())


def crystal_radius(s) -> float:
    """Max lattice distance of a frozen cell from the seed (axial -> euclidean embedding)."""
    m = frozen_mask(s)
    if not m.any():
        return 0.0
    c = s.shape[0] // 2
    i, j = np.where(m)
    q, r = i - c, j - c
    x = q + 0.5 * r
    y = (np.sqrt(3) / 2.0) * r
    return float(np.sqrt(x * x + y * y).max())


def compactness(s) -> float:
    """Frozen cells / area of the enclosing disc: ~1 for a filled plate, small for a sparse dendrite."""
    R = crystal_radius(s)
    if R <= 0:
        return 0.0
    return float(crystal_mass(s) / (np.pi * R * R))


def is_symmetric(s, tol: float = 1e-9) -> bool:
    """The crystal inherits the lattice symmetry: invariant under the diagonal mirror (transpose) and
    central inversion about the seed (both are symmetries of the neighbour set)."""
    mirror = np.allclose(s, s.T, atol=tol)
    inversion = np.allclose(s, s[::-1, ::-1], atol=tol)
    return bool(mirror and inversion)


def to_cartesian(L):
    """Axial lattice indices -> euclidean coordinates, so the crystal plots with true 6-fold symmetry."""
    c = L // 2
    i, j = np.indices((L, L))
    q, r = i - c, j - c
    return q + 0.5 * r, (np.sqrt(3) / 2.0) * r
