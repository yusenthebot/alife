"""R42 — group selection and Simpson's paradox.

Cooperation is altruism: a cooperator pays a cost c so its group receives a benefit
b. Inside any one group a defector always does better than a cooperator (it reaps
the benefit without paying), so the cooperator fraction *falls within every group*.
And yet — if cooperators assort, so that some groups are rich in them — those
cooperator-rich groups out-produce the rest, and the *global* cooperator fraction
can RISE at the same time. Decline in every part, increase in the whole: Simpson's
paradox, and the engine of multilevel (group) selection.

Trait-group model (D.S. Wilson). Each generation individuals form groups with a
tunable degree of assortment; group composition sets everyone's fitness; offspring
re-pool and re-form groups. The Price equation splits Δp into a within-group term
(always against cooperation) and a between-group term (for it) — assortment decides
which wins.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class GroupSelConfig:
    n: int = 4000            # population size
    group_size: int = 20
    benefit: float = 8.0     # b: total benefit a fully-cooperative group confers
    cost: float = 1.0        # c: cost a cooperator pays
    assortment: float = 0.12  # 0 = random; low-but-nonzero keeps groups MIXED so the
                              # within-group decline stays visible (Simpson's paradox)
    init_coop: float = 0.5
    generations: int = 60


def _form_groups(types: np.ndarray, cfg: GroupSelConfig, rng) -> np.ndarray:
    """Return group-membership as a (G, group_size) index array. Assortment sorts
    like-with-like: key = a*type + (1-a)*noise, then chunk."""
    a = cfg.assortment
    key = a * types + (1 - a) * rng.random(types.size)
    order = np.argsort(key)
    g = types.size // cfg.group_size
    return order[: g * cfg.group_size].reshape(g, cfg.group_size)


def step(types: np.ndarray, cfg: GroupSelConfig, rng):
    """One generation. Returns (new_types, global_dp, mean_within_group_dp)."""
    groups = _form_groups(types, cfg, rng)
    gt = types[groups]                                  # (G, group_size) 1=coop 0=def
    f = gt.mean(axis=1, keepdims=True)                  # cooperator fraction per group
    # within-group payoff: cooperator pays c; everyone shares b*f
    coop_fit = 1.0 - cfg.cost + cfg.benefit * f
    def_fit = 1.0 + cfg.benefit * f
    fitness = np.where(gt == 1, coop_fit, def_fit)      # (G, group_size)

    # offspring contributed by each group, split into coop/def
    coop_off = (fitness * (gt == 1)).sum()
    def_off = (fitness * (gt == 0)).sum()
    new_p = coop_off / (coop_off + def_off)

    # within-group change in cooperator fraction (Simpson's "every part")
    g_coop = (fitness * (gt == 1)).sum(axis=1)
    g_def = (fitness * (gt == 0)).sum(axis=1)
    g_newf = g_coop / np.maximum(g_coop + g_def, 1e-9)
    within_dp = float(np.mean(g_newf - f.ravel()))

    global_dp = float(new_p - types.mean())
    new_types = (rng.random(cfg.n) < new_p).astype(np.int8)
    return new_types, global_dp, within_dp


def evolve(cfg: GroupSelConfig, seed: int = 0):
    rng = np.random.default_rng(seed)
    types = (rng.random(cfg.n) < cfg.init_coop).astype(np.int8)
    p_hist = [float(types.mean())]
    within_hist = []
    for _ in range(cfg.generations):
        types, gdp, wdp = step(types, cfg, rng)
        p_hist.append(float(types.mean()))
        within_hist.append(wdp)
    return {"coop_fraction": np.array(p_hist), "within_group_dp": np.array(within_hist)}


def assortment_sweep(cfg: GroupSelConfig, assortments, seed: int = 0) -> np.ndarray:
    """Final global cooperator fraction across assortment levels."""
    out = []
    for a in assortments:
        c = GroupSelConfig(n=cfg.n, group_size=cfg.group_size, benefit=cfg.benefit,
                           cost=cfg.cost, assortment=float(a), init_coop=cfg.init_coop,
                           generations=cfg.generations)
        out.append(float(evolve(c, seed=seed)["coop_fraction"][-1]))
    return np.array(out)
