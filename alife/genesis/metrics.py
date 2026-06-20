"""GENESIS instruments — measured in situ, never used as a selection signal.

Two read-outs, computed from round one and designed to be red-team-resistant:

1. food_directedness — the behaviour/skill curve. Among agents that can SEE food, how well
   does their motion point at the nearest food? +1 straight at it, 0 random, <0 away. This is
   the headline "is it really evolving" signal: it should RISE under evolution and stay flat in
   a frozen-genome control. (3D port of alife.neuro.food_alignment.)

2. effective_lineages — the ecology/diversity guard, with the MODES persistence filter. Counts
   only founder bloodlines that have PERSISTED >= persist_steps, then reports the effective number
   of lineages exp(H) (Shannon). The persistence filter is the anti-gaming heart: it ignores
   transient lucky mutants and drift, so the metric can't light up green from noise. A monoculture
   collapse shows up as this falling toward 1; a healthy open ecology keeps it high.
"""

from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree


def food_directedness(pos: np.ndarray, vel: np.ndarray, food: np.ndarray,
                      sense_range: float) -> float:
    """Mean cosine between velocity and direction-to-nearest-visible-food. In [-1, 1]."""
    if pos.shape[0] == 0 or food.shape[0] == 0:
        return 0.0
    dist, idx = cKDTree(food).query(pos, k=1)
    visible = dist < sense_range
    if not visible.any():
        return 0.0
    nearest = food[idx] - pos
    nf = nearest / np.maximum(np.linalg.norm(nearest, axis=1, keepdims=True), 1e-9)
    sp = np.maximum(np.linalg.norm(vel, axis=1, keepdims=True), 1e-9)
    cos = ((vel / sp) * nf).sum(1)
    return float(cos[visible].mean())


def effective_lineages(active_lineage: np.ndarray, first_step: dict,
                       current_step: int, persist_steps: int) -> float:
    """Effective number of PERSISTENT founder lineages = exp(Shannon entropy of abundances).

    A lineage counts only if it first appeared at least `persist_steps` ago (the persistence
    filter). Returns 0.0 when none qualify, 1.0 for a single dominant bloodline (monoculture),
    higher for an even, diverse ecology.
    """
    if active_lineage.shape[0] == 0:
        return 0.0
    ids, counts = np.unique(active_lineage, return_counts=True)
    keep = np.array([(current_step - first_step.get(int(i), current_step)) >= persist_steps
                     for i in ids], dtype=bool)
    counts = counts[keep]
    if counts.size == 0:
        return 0.0
    p = counts / counts.sum()
    h = -(p * np.log(p)).sum()
    return float(np.exp(h))
