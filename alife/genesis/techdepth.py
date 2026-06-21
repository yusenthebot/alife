"""TECH DEPTH — is the living civilization's technology a CONNECTED cumulative DAG, or a flat scatter? (R167)

The R160-R166 arc measured the cumulative-culture repertoire by BREADTH (how many distinct techniques the
living population knows, `pop_distinct`) and by RATE (dN/dt, `livephylorate`). But breadth is not what makes
culture *cumulative*. A pile of a thousand independent tricks is broad and shallow; a civilization is
technology that STANDS ON technology — each thing known because the things it depends on are also known. The
structural signature of cumulative culture is therefore not the COUNT of techniques but the CONNECTEDNESS of
the dependency graph the society actually holds: are a known technique's prerequisites themselves known, all
the way down to primitives?

This module measures that structure on the LIVE `GenesisWorld`. The world already builds a fixed combinatorial
tech tree (`combinatorial.build_tech_tree`): every non-seed technique k has two prerequisites (`pa[k]`,`pb[k]`)
and a tree level `1 + max(level[pa],level[pb])`. The society's repertoire is the union of the living agents'
boolean repertoires (`rep[act].any(0)`). On that known set we read two structural quantities the breadth/rate
instruments cannot see:

  * `closure_fraction` — of the known NON-SEED techniques, the fraction whose BOTH prerequisites are also
    known by the society. Closure ~1 means the repertoire is (almost) prereq-closed: nearly nothing is known
    in isolation. This is the local "standing on known shoulders" rate.
  * `connected_depth` — the length of the LONGEST chain of consecutive, mutually-known prerequisites ending at
    any known technique (a node whose prereq is unknown breaks the chain there). This is the global reach of
    the realized cumulative ladder, in contrast to the NOMINAL depth `max_level` (the deepest tree level of
    *any* known technique, regardless of whether its supporting chain is held).

The decisive contrast is `combo_prereqs` (the same single switch that defines combinatorial vs additive).
  * combinatorial (`combo_prereqs=True`): an agent can only DISCOVER k when both prereqs are already in its
    repertoire, so the known set is prereq-closed BY CONSTRUCTION and grows a deep CONNECTED DAG — modulo the
    imperfect social transmission (`culture_fidelity<1`) that can drop a prerequisite from an inherited
    repertoire, so closure is high but not exactly 1 (a real, non-tautological number).
  * additive null (`combo_prereqs=False`): discovery is uniform over ALL unknown techniques regardless of
    prerequisites, so the society can "know" a deep technique whose supporting chain it has never acquired.
    The result reaches a comparable BREADTH and even a comparable NOMINAL `max_level`, but the realized DAG is
    DISCONNECTED — closure is low and `connected_depth` collapses. Same machinery, same tree; the only change
    is whether discovery respects dependencies.

So `connected_depth` / `closure_fraction` dissociate two regimes that breadth and nominal depth cannot tell
apart: cumulative culture is structurally DEEP-AND-CONNECTED; the additive scatter is broad-but-shallow.

All functions are pure array ops on the tree arrays + a boolean `known` mask; `depth_trajectory` is read-only
on the world (calls `world.step()` and reads `world.rep` only — no new mechanism, no extra RNG). Cheap: the
depth pass loops over tree LEVELS (~tens), each level vectorized, so it is fine to log every step.
"""

from __future__ import annotations

import numpy as np


def closure_fraction(known: np.ndarray, pa: np.ndarray, pb: np.ndarray, n_seed: int) -> float:
    """Fraction of KNOWN non-seed techniques whose BOTH prerequisites are also known.

    1.0 = the repertoire is prereq-closed (nothing known stands on unknown foundations); ~0 = the known
    set is a scatter of techniques whose dependencies are missing. NaN if no non-seed technique is known."""
    idx = np.arange(known.shape[0])
    nonseed = (idx >= n_seed) & known
    n = int(nonseed.sum())
    if n == 0:
        return float("nan")
    a, b = pa[nonseed], pb[nonseed]
    both = known[a] & known[b]
    return float(both.sum()) / n


def connected_depth_array(known: np.ndarray, pa: np.ndarray, pb: np.ndarray,
                          level: np.ndarray, n_seed: int) -> np.ndarray:
    """Per technique: the length of the longest chain of consecutive MUTUALLY-KNOWN prerequisites ending
    at it (0 for seeds, unknown techniques, or techniques whose chain is broken by a missing prereq).

    A non-seed technique contributes 1 + max(depth of its two prereqs) ONLY if both prereqs are known;
    otherwise its chain is broken and its connected depth is 0. Because a technique's prereqs have strictly
    lower tree level, a single increasing-level pass fills the array (each level vectorized). Returns int64
    array shape (K,)."""
    K = known.shape[0]
    cd = np.zeros(K, dtype=np.int64)
    if not known.any():
        return cd
    idx = np.arange(K)
    nonseed = idx >= n_seed
    maxlvl = int(level.max())
    for L in range(1, maxlvl + 1):
        at = nonseed & (level == L) & known
        if not at.any():
            continue
        a, b = pa[at], pb[at]
        both = known[a] & known[b]              # chain continues only if both prereqs are held
        d = np.zeros(int(at.sum()), dtype=np.int64)
        d[both] = 1 + np.maximum(cd[a][both], cd[b][both])
        cd[at] = d
    return cd


def connected_depth(known: np.ndarray, pa: np.ndarray, pb: np.ndarray,
                    level: np.ndarray, n_seed: int) -> int:
    """The longest fully-known consecutive prerequisite chain in the society's repertoire (max of
    `connected_depth_array`). Contrast `max_level`, the NOMINAL deepest known tree level."""
    return int(connected_depth_array(known, pa, pb, level, n_seed).max())


def realized_edges(known: np.ndarray, pa: np.ndarray, pb: np.ndarray, n_seed: int):
    """Prerequisite edges (child -> parent) of the realized DAG: non-seed techniques that are known, paired
    with each prerequisite that is ALSO known. For drawing the living civilization's tech graph. Returns
    (children, parents) int64 arrays of equal length."""
    idx = np.arange(known.shape[0])
    nonseed = np.where((idx >= n_seed) & known)[0]
    children, parents = [], []
    for prereq in (pa, pb):
        p = prereq[nonseed]
        ok = known[p]
        children.append(nonseed[ok])
        parents.append(p[ok])
    return np.concatenate(children), np.concatenate(parents)


def society_repertoire(world) -> np.ndarray:
    """The union of the living population's boolean repertoires — the techniques known by >=1 living agent
    (the society's collective knowledge). Read-only. Length max_techniques; all-False if no combinatorial
    world or no living agents."""
    if not getattr(world, "combinatorial", False):
        return np.zeros(0, dtype=bool)
    act = world.pop.active()
    if act.size == 0:
        return np.zeros(world.cfg.max_techniques, dtype=bool)
    return world.rep[act].any(axis=0)


def depth_trajectory(world, steps: int) -> dict:
    """Drive a live combinatorial `GenesisWorld` for `steps` steps, logging per step the structural depth
    of the society's repertoire alongside its breadth.

    Returns {step, breadth, max_level, conn_depth, closure, active}:
      breadth    = techniques known by the living population (= pop_distinct, the R160-R166 metric);
      max_level  = NOMINAL deepest known tree level (regardless of whether its chain is held);
      conn_depth = CONNECTED depth — longest fully-known prereq chain (the cumulative-culture signature);
      closure    = fraction of known non-seed techniques whose prereqs are also known;
      active     = living workforce.
    Read-only on the world (world.step() + world.rep only; no new RNG, no new mechanism)."""
    pa, pb, level = world._tree_pa, world._tree_pb, world._tree_level
    n_seed = world.cfg.n_seed_tech
    step_a = np.empty(steps, dtype=np.int64)
    breadth = np.empty(steps, dtype=np.int64)
    maxlvl = np.empty(steps, dtype=np.int64)
    conn = np.empty(steps, dtype=np.int64)
    clos = np.empty(steps, dtype=np.float64)
    act_a = np.empty(steps, dtype=np.int64)
    for i in range(steps):
        world.step()
        known = society_repertoire(world)
        step_a[i] = i + 1
        breadth[i] = int(known.sum())
        maxlvl[i] = int(level[known].max()) if known.any() else 0
        conn[i] = connected_depth(known, pa, pb, level, n_seed)
        clos[i] = closure_fraction(known, pa, pb, n_seed)
        act_a[i] = int(world.pop.active().size)
    return {"step": step_a, "breadth": breadth, "max_level": maxlvl,
            "conn_depth": conn, "closure": clos, "active": act_a}
