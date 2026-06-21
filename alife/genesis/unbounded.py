"""GENUINELY UNBOUNDED generative tech space (R164) — lift R150's fixed `max_techniques` ceiling.

R150's combinatorial culture explores a tech tree of FIXED size `n_techniques`, pre-built ahead of the
run. Frontier depth therefore ceilings at that tree's deepest pre-built level: cumulative, but ultimately
bounded by a deliberate cap (raise the cap and it climbs a bit more, then stops again). R164 removes the
cap entirely: a technique is no longer a pre-allocated column in a boolean matrix but the COMPOSITION of
two known techniques, materialized on demand. Combining techniques a and b yields a product whose identity
is the canonical pair (min(a,b), max(a,b)) and whose level is 1 + max(level[a], level[b]); a product never
made before becomes a brand-new technique with a fresh id. Because any two known techniques compose, and
the product is itself composable, the reachable space is the (infinite) closure of the seeds under pairing
— there is no fixed point and no cap. Frontier depth is then bounded only by the number of composition
rounds, not by any pre-set ceiling: open-ended BY CONSTRUCTION, and provably so — after t composition
rounds the deepest reachable level is exactly t (a strictly rising envelope with no asymptote).

The level is the LONGEST ancestral composition chain back to the seeds (`chain_len` proves the invariant
`chain_len(k) == level(k)`): a level-L technique genuinely descends through L compositions from primitive
seeds, so frontier DEPTH is literal cumulative-descent depth — tying R164's open-ended climb back to the
R160-R163 descent-structure rung.

Memory stays bounded for any finite run because ONLY the techniques actually DISCOVERED are materialized
(a registry of {pair -> id}); nothing pre-allocates the infinite space. Repertoires are Python sets of
ints (sparse), not dense boolean rows, precisely because the column set is unbounded. A `cap` recovers the
R150 regime on otherwise IDENTICAL dynamics — once the registry fills, `combine` refuses to materialize a
new technique (returns None) and depth freezes. So `cap=None` vs `cap=K` is the decisive control: same
machinery, the ONLY difference is whether the space can grow, isolating "open-ended climb" from "capped
plateau".
"""

from __future__ import annotations

import numpy as np


class TechSpace:
    """A lazily-materialized combinatorial technique space (the registry of discovered techniques).

    Seeds 0..n_seed-1 are primitives at level 0 (parents (-1,-1), first_step 0). Every other technique is
    materialized by `combine` the first time its parent pair is composed, and is assigned the next integer
    id. With `cap` set, no more than `cap` techniques are ever materialized (the R150 fixed-ceiling regime).
    """

    def __init__(self, n_seed: int, cap: int | None = None):
        if n_seed < 2:
            raise ValueError("need n_seed >= 2 (a seed must be combinable)")
        if cap is not None and cap < n_seed:
            raise ValueError("cap must be >= n_seed")
        self.n_seed = int(n_seed)
        self.cap = cap
        self.levels: list[int] = [0] * n_seed
        self.parents: list[tuple[int, int]] = [(-1, -1)] * n_seed
        self.first_step: list[int] = [0] * n_seed
        self.registry: dict[tuple[int, int], int] = {}
        self._chain: dict[int, int] = {}

    @property
    def n(self) -> int:
        """Number of techniques materialized so far (seeds + discovered products)."""
        return len(self.levels)

    def combine(self, a: int, b: int, step: int = 0) -> int | None:
        """Compose two DISTINCT known techniques. Returns the product id (materializing it the first time),
        or None if a `cap` is set and the space is full and the product does not already exist."""
        if a == b:
            raise ValueError("cannot compose a technique with itself")
        key = (a, b) if a < b else (b, a)
        existing = self.registry.get(key)
        if existing is not None:
            return existing
        if self.cap is not None and self.n >= self.cap:
            return None                                  # capped: no new technique can be born
        nid = self.n
        self.registry[key] = nid
        self.levels.append(1 + max(self.levels[a], self.levels[b]))
        self.parents.append(key)
        self.first_step.append(int(step))
        return nid

    def level(self, k: int) -> int:
        return self.levels[k]

    def chain_len(self, k: int) -> int:
        """Longest ancestral composition chain from k down to a seed. For a seed this is 0. Used to PROVE
        the cumulative-descent invariant `chain_len(k) == level(k)` (a level-L technique descends through L
        genuine compositions from primitive seeds)."""
        cached = self._chain.get(k)
        if cached is not None:
            return cached
        pa, pb = self.parents[k]
        out = 0 if pa < 0 else 1 + max(self.chain_len(pa), self.chain_len(pb))
        self._chain[k] = out
        return out


def run_population(n_agents: int, n_seed: int, steps: int, fidelity: float = 0.5,
                   cap: int | None = None, learn: bool = True, seed: int = 0) -> dict:
    """Evolve a population over the (un)bounded combinatorial space and log the frontier trajectory.

    Each step every agent (1) DISCOVERS — composes two random techniques from its own repertoire, adding
    the product (a possibly brand-new technique) — then, if `learn`, (2) TRANSMITS — copies a random
    neighbour's repertoire with per-technique probability `fidelity`. Everyone starts knowing the seeds.

    Returns a dict of arrays over steps:
      step, max_level (frontier depth), n_distinct (techniques materialized in the world = breadth),
      mean_level (population mean of per-agent deepest level),
    plus the final TechSpace `space` (for first_step / level / chain_len analysis).

    With cap=None depth climbs without bound; with cap=K it freezes once K techniques exist — IDENTICAL
    dynamics otherwise, so the pair is a clean open-ended-vs-capped control.
    """
    rng = np.random.default_rng(seed)
    space = TechSpace(n_seed, cap=cap)
    reps: list[set[int]] = [set(range(n_seed)) for _ in range(n_agents)]
    agent_max = [0] * n_agents                            # per-agent deepest level known (incremental)

    T, ML, ND, MeanL = [], [], [], []
    for t in range(1, steps + 1):
        # (1) discovery
        for i in range(n_agents):
            r = reps[i]
            if len(r) < 2:
                continue
            a, b = rng.choice(list(r), size=2, replace=False)
            pid = space.combine(int(a), int(b), step=t)
            if pid is not None and pid not in r:
                r.add(pid)
                if space.levels[pid] > agent_max[i]:
                    agent_max[i] = space.levels[pid]
        # (2) social transmission from one random neighbour
        if learn and fidelity > 0 and n_agents > 1:
            partners = (np.arange(n_agents) + 1 + rng.integers(0, n_agents - 1, n_agents)) % n_agents
            for i in range(n_agents):
                src = reps[int(partners[i])]
                if not src:
                    continue
                keep = rng.random(len(src)) < fidelity
                for tech, k in zip(src, keep):
                    if k and tech not in reps[i]:
                        reps[i].add(tech)
                        if space.levels[tech] > agent_max[i]:
                            agent_max[i] = space.levels[tech]
        T.append(t)
        ML.append(max(agent_max))
        ND.append(space.n)
        MeanL.append(float(np.mean(agent_max)))

    return {"step": np.array(T), "max_level": np.array(ML), "n_distinct": np.array(ND),
            "mean_level": np.array(MeanL), "space": space}


def ladder_arrays(space: TechSpace) -> tuple[np.ndarray, np.ndarray]:
    """Return (first_step, level) arrays over the NON-SEED materialized techniques, for the temporal-ladder
    check (deeper techniques should appear later) over the unbounded climb."""
    ns = space.n_seed
    if space.n <= ns:
        return np.empty(0), np.empty(0)
    first = np.array(space.first_step[ns:], dtype=float)
    lvl = np.array(space.levels[ns:], dtype=float)
    return first, lvl
