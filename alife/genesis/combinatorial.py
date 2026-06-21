"""Open-ended COMBINATORIAL culture (R150) — the tech tree that lifts R149's finite ceiling.

R149's cumulative culture is a scalar `tech` whose innovation is a FIXED-rate independent draw, so it
ratchets to a finite fixed point ~innov/(1-fidelity): cumulative but NOT open-ended. R150 replaces the
scalar with a discrete REPERTOIRE of techniques on a fixed tech TREE. A technique k (k>=n_seed) has two
PREREQUISITE techniques (a fixed deterministic table); an agent can DISCOVER k only if it already knows
BOTH prereqs — Kauffman's "adjacent possible" / Arthur's combinatorial evolution of technology. Because
the set of discoverable techniques GROWS as the repertoire grows (more known techniques -> more prereq
pairs satisfied -> more reachable products), the discovery rate ACCELERATES and the frontier never
saturates: open-ended by construction. There is no intrinsic fixed point (contrast R149); a run is
bounded only by the deliberate max_techniques cap, and raising the cap lets it keep climbing.

The combinatorial mechanism is isolated by a single switch, `combo_prereqs`:
  - True  -> discovery is gated on prerequisites (the combinatorial / adjacent-possible mechanism).
  - False -> discovery is uniform over ALL unknown techniques (the ADDITIVE null: a fixed-rate draw
             whose yield DECELERATES as the finite pool fills -> a saturating ratchet, like R149).
So `combo_prereqs` cleanly separates "open-ended combinatorial climb" from "additive saturating ratchet"
on otherwise identical machinery.

Pure array functions; no global state. The World owns the boolean repertoire matrices (one row per
agent slot / per hearth), so memory stays bounded by the fixed pools.
"""

from __future__ import annotations

import numpy as np

# The tech tree is a property of the WORLD, not of a run, so it is built from a fixed seed and is
# identical across simulation seeds (only the agents' exploration of it differs run to run).
TREE_SEED = 20250620


def build_tech_tree(n_techniques: int, n_seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build the fixed combinatorial tech tree.

    Techniques 0..n_seed-1 are SEED primitives: no prerequisites (prereq = -1), level 0, discoverable
    from an empty repertoire. Each technique k>=n_seed draws two DISTINCT lower-indexed prerequisites
    and has level 1 + max(level of its prereqs). Deterministic (fixed RNG) -> the same tree every run.

    Returns (prereq_a, prereq_b, level), each shape (n_techniques,), dtype int64.
    """
    if n_seed < 2 or n_seed >= n_techniques:
        raise ValueError("need 2 <= n_seed < n_techniques (a seed must be combinable)")
    rng = np.random.default_rng(TREE_SEED)
    pa = np.full(n_techniques, -1, dtype=np.int64)
    pb = np.full(n_techniques, -1, dtype=np.int64)
    level = np.zeros(n_techniques, dtype=np.int64)
    for k in range(n_seed, n_techniques):
        a = int(rng.integers(0, k))
        b = int(rng.integers(0, k))
        while b == a:
            b = int(rng.integers(0, k))
        pa[k] = a
        pb[k] = b
        level[k] = 1 + max(int(level[a]), int(level[b]))
    return pa, pb, level


def adjacent_possible(rep: np.ndarray, pa: np.ndarray, pb: np.ndarray,
                      n_seed: int, combo_prereqs: bool) -> np.ndarray:
    """The set of techniques each agent could discover NEXT, as a boolean mask [n, K].

    combo_prereqs=True : an UNKNOWN technique is reachable iff both its prerequisites are known
                         (seeds, prereq=-1, need nothing) -> Kauffman's adjacent possible.
    combo_prereqs=False: every UNKNOWN technique is reachable (the additive null).
    """
    unknown = ~rep
    if not combo_prereqs:
        return unknown
    n, _ = rep.shape
    nonseed = np.arange(rep.shape[1]) >= n_seed       # techniques that actually have prerequisites
    have = np.ones_like(rep)
    # for the non-seed techniques, both prereqs must be present in the agent's repertoire
    have[:, nonseed] = rep[:, pa[nonseed]] & rep[:, pb[nonseed]]
    return unknown & have


def discover_inplace(rep: np.ndarray, pa: np.ndarray, pb: np.ndarray, n_seed: int,
                     combo_prereqs: bool, rng: np.random.Generator, steps: int) -> None:
    """Each agent (row of `rep`) attempts `steps` discoveries, each adding ONE technique drawn at
    random from its current adjacent possible. Mutates `rep` in place. An agent with an empty
    adjacent possible in a step discovers nothing that step (rows handled independently)."""
    if rep.shape[0] == 0:
        return
    for _ in range(max(0, steps)):
        avail = adjacent_possible(rep, pa, pb, n_seed, combo_prereqs)
        has = avail.any(axis=1)
        if not has.any():
            break
        pick = (rng.random(rep.shape) * avail).argmax(axis=1)   # uniform random among available per row
        rows = np.where(has)[0]
        rep[rows, pick[rows]] = True


def copy_with_fidelity(src: np.ndarray, fidelity: float, rng: np.random.Generator) -> np.ndarray:
    """Imperfect social transmission of a repertoire: keep each KNOWN technique with prob `fidelity`.
    `src` is a boolean matrix [n, K] (the union of the models an agent learns from)."""
    return src & (rng.random(src.shape) < fidelity)


def recipe_techniques(level: np.ndarray, n_seed: int, n_tiers: int, step: int) -> np.ndarray:
    """Designate which tech-tree node UNLOCKS each food tier (R153 — culture gates a physical action).

    Tier 0 needs no recipe (always edible, recipe id -1). Tier t>=1 is unlocked by the LOWEST-index
    technique whose tree LEVEL is >= step*t — so a higher tier requires a strictly deeper place in the
    combinatorial tree, and an agent can eat tier-t food only once its learned repertoire has climbed
    there. Deterministic in the (fixed) tree, so identical across simulation seeds.

    Returns an int64 array of length n_tiers; entry 0 is -1, entry t>=1 is the recipe technique id.
    Raises if the tree is too shallow to place a recipe for some tier.
    """
    recipes = np.full(n_tiers, -1, dtype=np.int64)
    for t in range(1, n_tiers):
        target = step * t
        cand = np.where(level >= target)[0]
        if cand.size == 0:
            raise ValueError(
                f"tech tree too shallow for tier {t}: needs a technique at level>={target}, "
                f"deepest is {int(level.max())} (raise max_techniques or lower recipe_level_step/n_food_tiers)")
        recipes[t] = int(cand[0])
    return recipes


def capability_techniques(level: np.ndarray, n_seed: int, n_caps: int, step: int) -> np.ndarray:
    """Designate which deep tech-tree node UNLOCKS each PHYSICAL capability axis (R154 — culture gates a
    multi-dimensional capability vector, not just diet).

    Capability axis i (i in 0..n_caps-1) is unlocked by the LOWEST-index technique whose tree LEVEL is
    >= step*(i+1) — so each successive axis sits strictly deeper in the combinatorial tree and is reachable
    only as the learned repertoire climbs. Deterministic in the (fixed) tree, identical across simulation
    seeds. Returns an int64 array of length n_caps of recipe-technique ids.

    Raises if the tree is too shallow to place an axis (mirrors recipe_techniques). Distinct from the food
    recipes so the same tree can carry both diet (recipe_techniques) and capability (this) gates.
    """
    if n_caps < 1:
        return np.empty(0, dtype=np.int64)
    caps = np.full(n_caps, -1, dtype=np.int64)
    for i in range(n_caps):
        target = step * (i + 1)
        cand = np.where(level >= target)[0]
        if cand.size == 0:
            raise ValueError(
                f"tech tree too shallow for capability axis {i}: needs a technique at level>={target}, "
                f"deepest is {int(level.max())} (raise max_techniques or lower cap_level_step/n_capabilities)")
        caps[i] = int(cand[0])
    return caps


def max_level_known(rep: np.ndarray, level: np.ndarray) -> np.ndarray:
    """Per-agent deepest technique level known (0 if it knows only seeds / nothing). This is the
    scalar `tech` that drives the harvest payoff — so deeper mastery is selected."""
    if rep.shape[0] == 0:
        return np.zeros(0)
    masked = np.where(rep, level[None, :], 0)
    return masked.max(axis=1).astype(float)


class GrowingTree:
    """A GENERATIVE, open-ended tech tree (R170) — the LIVE-WORLD analogue of unbounded.TechSpace, but
    over the World's DENSE boolean repertoire so it drops into the existing combinatorial culture with no
    representation rewrite.

    `build_tech_tree` pre-enumerates a FIXED random tree of K nodes whose deepest level is a frozen ceiling:
    no matter how long the world runs, the frontier cannot pass that pre-built max level (raise K and it
    climbs a little, then stops again). GrowingTree instead starts with ONLY the n_seed primitives
    materialized and grows the tree FROM the population's real compositions: the first time two KNOWN
    techniques a,b are composed, a brand-new node is materialized (id = next free column, level =
    1+max(level[a],level[b]), parents = the pair) and appended into pre-allocated capacity-K arrays — so the
    dense rep width stays K while the realized tree is built by the living culture. The space is open-ended
    BY CONSTRUCTION: the only ceiling is the capacity K (the memory cap, == unbounded.TechSpace's `cap`).
    Cap it small and the frontier FREEZES once full; raise it and depth/breadth keep climbing with run
    length — the decisive open-ended-vs-capped control, now causal in the live world. `pa/pb/level` are the
    SAME arrays the World binds as `_tree_*`, mutated in place as nodes are born, so every downstream reader
    (max_level_known, combinatorial_test, the phylogeny read-outs) works unchanged on the grown tree.
    """

    def __init__(self, capacity: int, n_seed: int):
        if n_seed < 2:
            raise ValueError("need n_seed >= 2 (a seed must be combinable)")
        if capacity < n_seed:
            raise ValueError("capacity must be >= n_seed")
        self.capacity = int(capacity)
        self.n_seed = int(n_seed)
        self.pa = np.full(capacity, -1, dtype=np.int64)
        self.pb = np.full(capacity, -1, dtype=np.int64)
        self.level = np.zeros(capacity, dtype=np.int64)
        self.n = int(n_seed)                       # number of materialized nodes (seeds 0..n_seed-1 + products)
        self.registry: dict[tuple[int, int], int] = {}

    def combine(self, a: int, b: int) -> int:
        """Compose two DISTINCT known techniques. Returns the product id (materializing it the first time),
        or -1 if the tree is full (capacity reached and the product does not already exist) — the cap."""
        if a == b:
            raise ValueError("cannot compose a technique with itself")
        key = (a, b) if a < b else (b, a)
        existing = self.registry.get(key)
        if existing is not None:
            return existing
        if self.n >= self.capacity:
            return -1                              # full: no new node can be born (the memory cap = freeze)
        nid = self.n
        self.registry[key] = nid
        self.pa[nid] = key[0]
        self.pb[nid] = key[1]
        self.level[nid] = 1 + max(int(self.level[a]), int(self.level[b]))
        self.n += 1
        return nid

    def discover_inplace(self, rep: np.ndarray, rng: np.random.Generator, steps: int) -> None:
        """Each agent (row of `rep`) attempts `steps` compositions, each picking two DISTINCT KNOWN
        techniques at random and adding their product (a possibly brand-new node) to its repertoire. Mutates
        `rep` AND the shared tree in place. An agent that knows < 2 techniques composes nothing — so callers
        must guarantee the seeds are known (set rep[:, :n_seed] = True) before the first discovery, exactly
        as unbounded.run_population starts every agent knowing the primitives."""
        n = rep.shape[0]
        if n == 0:
            return
        for _ in range(max(0, steps)):
            for i in range(n):
                known = np.flatnonzero(rep[i])
                if known.size < 2:
                    continue
                a, b = rng.choice(known, size=2, replace=False)
                pid = self.combine(int(a), int(b))
                if pid >= 0:
                    rep[i, pid] = True
