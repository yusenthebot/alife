"""Genome: the heritable traits each creature is born with.

A genome is one row of a float matrix — one column per trait. Behavior that was
a fixed global constant in Round 1 (perception radius, social weights, speed) is
now per-individual and *heritable*: offspring inherit the parent's genome with
gaussian mutation, and clamping keeps every trait inside biologically sane
bounds. Selection does the rest — no fitness function is written down anywhere,
it emerges from who manages to eat and reproduce.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Trait schema. Order is the column order of the genome matrix; keep in sync
# with the index constants below.
TRAIT_NAMES: tuple[str, ...] = (
    "perception",  # how far it senses neighbors and food
    "w_sep",       # separation drive
    "w_ali",       # alignment drive
    "w_coh",       # cohesion drive
    "w_food",      # attraction to food
    "max_speed",   # top speed
    "metabolism",  # energy burned per unit of motion
)
TRAIT_LO = np.array([4.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.4])
TRAIT_HI = np.array([30.0, 3.0, 3.0, 3.0, 4.0, 4.0, 2.0])
N_TRAITS = len(TRAIT_NAMES)

# Column indices (readability at call sites).
PERCEPTION, W_SEP, W_ALI, W_COH, W_FOOD, MAX_SPEED, METABOLISM = range(N_TRAITS)


@dataclass(frozen=True)
class MutationConfig:
    rate: float = 0.9            # probability a given trait mutates per birth
    sigma_frac: float = 0.08     # std of mutation as a fraction of each trait's range


def random_genomes(n: int, rng: np.random.Generator) -> np.ndarray:
    """Uniformly random genomes within trait bounds — the disordered start."""
    return rng.uniform(TRAIT_LO, TRAIT_HI, size=(n, N_TRAITS))


def mutate(genomes: np.ndarray, cfg: MutationConfig, rng: np.random.Generator) -> np.ndarray:
    """Heritable variation: jitter each trait, then clamp to bounds. Pure."""
    span = TRAIT_HI - TRAIT_LO
    noise = rng.normal(0.0, cfg.sigma_frac, size=genomes.shape) * span
    hit = rng.random(genomes.shape) < cfg.rate
    child = genomes + noise * hit
    return np.clip(child, TRAIT_LO, TRAIT_HI)


def column(genomes: np.ndarray, index: int) -> np.ndarray:
    """Trait column as (N, 1) for broadcasting against per-agent vectors."""
    return genomes[:, index : index + 1]
