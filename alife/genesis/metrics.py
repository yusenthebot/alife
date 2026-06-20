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


def flee_directedness(prey_pos: np.ndarray, prey_vel: np.ndarray, pred_pos: np.ndarray,
                      sense_range: float) -> float:
    """Among prey that can see a predator, mean cosine of velocity AWAY from the nearest predator.

    +1 = fleeing straight away, 0 = random, <0 = toward. The R143 evasion signal: it should RISE as
    prey evolve to flee and stay near 0 for a frozen-genome prey control. In situ, never feeds selection."""
    if prey_pos.shape[0] == 0 or pred_pos.shape[0] == 0:
        return 0.0
    dist, idx = cKDTree(pred_pos).query(prey_pos, k=1)
    visible = dist < sense_range
    if not visible.any():
        return 0.0
    to_pred = pred_pos[idx] - prey_pos
    nf = to_pred / np.maximum(np.linalg.norm(to_pred, axis=1, keepdims=True), 1e-9)
    sp = np.maximum(np.linalg.norm(prey_vel, axis=1, keepdims=True), 1e-9)
    flee = -((prey_vel / sp) * nf).sum(1)            # negative dot -> moving away from the predator
    return float(flee[visible].mean())


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


def danger_state(prey_pos: np.ndarray, pred_pos: np.ndarray, detect_range: float) -> np.ndarray:
    """Per-prey binary world-state: is a predator within `detect_range` (what a sender can detect).

    This is the latent variable a predator-alarm signal could encode. Returns an int array (0/1)."""
    if prey_pos.shape[0] == 0:
        return np.zeros(0, dtype=int)
    if pred_pos.shape[0] == 0:
        return np.zeros(prey_pos.shape[0], dtype=int)
    dist, _ = cKDTree(pred_pos).query(prey_pos, k=1)
    return (dist < detect_range).astype(int)


def _quantile_bins(x: np.ndarray, n_bins: int) -> np.ndarray:
    """Rank-based equal-frequency binning -> ints in [0, n_bins). Robust to the signal's scale/offset."""
    n = x.shape[0]
    order = np.argsort(x, kind="stable")
    ranks = np.empty(n, dtype=np.int64)
    ranks[order] = np.arange(n)
    return np.minimum((ranks * n_bins) // n, n_bins - 1)


def _discrete_mi(a: np.ndarray, b: np.ndarray, na: int, nb: int) -> float:
    """Mutual information I(a; b) in BITS for discrete labels a in [0,na), b in [0,nb)."""
    joint = np.zeros((na, nb))
    np.add.at(joint, (a, b), 1.0)
    tot = joint.sum()
    if tot == 0:
        return 0.0
    joint /= tot
    pa = joint.sum(1, keepdims=True)
    pb = joint.sum(0, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        terms = joint * np.log2(joint / (pa * pb))
    return float(np.nansum(terms))


def signal_world_mi(utterance: np.ndarray, world_state: np.ndarray, n_bins: int = 4) -> float:
    """I(binned-utterance ; binary world-state) in bits — does the emitted signal CARRY information
    about the world? 0 when the signal is uninformative (random or constant). The R144 headline: this
    rises under evolution to above the scrambled-channel null, meaning signals acquired meaning."""
    n = utterance.shape[0]
    ws = np.asarray(world_state).astype(int)
    if n < 2 * n_bins or ws.min() == ws.max():     # need state variation + enough samples
        return 0.0
    bins = _quantile_bins(utterance, n_bins)
    return _discrete_mi(bins, ws, n_bins, int(ws.max()) + 1)


def signal_mi_null(utterance: np.ndarray, world_state: np.ndarray, rng: np.random.Generator,
                   n_bins: int = 4, n_perm: int = 64) -> tuple[float, float]:
    """Scrambled-channel baseline: MI after permuting the state labels (destroys any real coupling).
    Returns (mean, std) of the permuted MI — the null any real MI must clear. The anti-fake control."""
    n = utterance.shape[0]
    ws = np.asarray(world_state).astype(int)
    if n < 2 * n_bins or ws.min() == ws.max():
        return 0.0, 0.0
    bins = _quantile_bins(utterance, n_bins)
    nb = int(ws.max()) + 1
    vals = np.array([_discrete_mi(bins, rng.permutation(ws), n_bins, nb) for _ in range(n_perm)])
    return float(vals.mean()), float(vals.std())


def neighbour_relatedness(pos: np.ndarray, lineage: np.ndarray) -> float:
    """Fraction of agents whose NEAREST neighbour shares their founder lineage (R145).

    The kin-structure read-out: ~1 when the population is spatially clonal (a neighbour is your clone,
    so warning it propagates your genes — kin selection can pay), ~1/n_lineages when well mixed. This
    is what the clonal-deme founding manipulates; the signalling-emergence claim rests on it being high."""
    n = pos.shape[0]
    if n < 2:
        return 0.0
    _, idx = cKDTree(pos).query(pos, k=2)
    return float((lineage == lineage[idx[:, 1]]).mean())


def point_biserial(x: np.ndarray, group: np.ndarray) -> float:
    """Correlation between a continuous x and a binary group (the Pearson r with group as 0/1).

    The R146 task-allocation read-out: x = local food proximity, group = the process decision. A NEGATIVE
    value of corr(ripe-proximity, process) means agents process when ripe food is scarce nearby (response-
    threshold division of labour); ~0 means the decision ignores local need (a frozen-genome control). 0 if
    either side has no variance."""
    x = np.asarray(x, dtype=float)
    g = np.asarray(group, dtype=float)
    if x.shape[0] < 3 or x.std() < 1e-12 or g.std() < 1e-12:
        return 0.0
    return float(np.corrcoef(x, g)[0, 1])


def diet_diversity(diet: np.ndarray, n_types: int) -> float:
    """Effective number of occupied diet niches = exp(Shannon) over the rounded-diet histogram.

    The R142 headline: with resource partitioning this stays > 1 (coexisting specialist strategies),
    where the single-resource R141 world collapses to one. 1.0 = a single strategy (monoculture)."""
    if diet.shape[0] == 0:
        return 0.0
    if n_types <= 1:
        return 1.0
    bins = np.clip(np.round(diet).astype(int), 0, n_types - 1)
    counts = np.bincount(bins, minlength=n_types)
    counts = counts[counts > 0]
    p = counts / counts.sum()
    return float(np.exp(-(p * np.log(p)).sum()))
