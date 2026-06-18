"""R75 — Swarm cognition: how a honeybee colony decides (cross-inhibition consensus).

R65 was stigmergy — ants leaving trails. This is the other side of swarm intelligence: a
decentralized DECISION. A swarm of scout bees must pick the best of several nest sites with no
leader and no bee comparing options directly (each only ever visits one). Seeley's honeybee
democracy, formalized by Marshall et al. (2009): scouts discover sites, waggle-dance to RECRUIT
others (more vigorously for better sites), spontaneously ABANDON, and — the crucial ingredient —
send a CROSS-INHIBITION "stop signal" to bees committed to rival sites. Cross-inhibition turns a
mob into a decision-maker: it locks in the better site when options differ, and breaks the
deadlock between two equally-good options into a clear consensus. Without it, equal options leave
the swarm split and unable to choose.

Agent-based stochastic simulation: each bee is uncommitted or committed to one site; transitions
fire with quality-weighted probabilities. Pure numpy/CPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

UNCOMMITTED = -1


@dataclass(frozen=True)
class SwarmConfig:
    n_bees: int = 1000
    discover: float = 0.02     # spontaneous discovery rate (scaled by site quality)
    recruit: float = 1.6       # recruitment rate (waggle dance), scaled by quality × dancers
    abandon: float = 0.05      # spontaneous abandonment rate
    inhibit: float = 1.6       # cross-inhibition (stop-signal) rate, scaled by rival quality × rivals
    dt: float = 0.1


def simulate(qualities, cfg: SwarmConfig, steps: int = 800, seed: int = 0, cross_inhibition: bool = True):
    """Run the swarm. `qualities` = per-site value (length n). Returns committed-fraction time
    series (steps+1, n) and the uncommitted fraction."""
    rng = np.random.default_rng(seed)
    v = np.asarray(qualities, float)
    n = len(v)
    s = np.full(cfg.n_bees, UNCOMMITTED, dtype=np.int64)
    frac_hist = np.empty((steps + 1, n))
    unc_hist = np.empty(steps + 1)

    def record(t):
        frac_hist[t] = [(s == i).mean() for i in range(n)]
        unc_hist[t] = (s == UNCOMMITTED).mean()

    record(0)
    for t in range(1, steps + 1):
        frac = np.array([(s == i).mean() for i in range(n)])
        u = s == UNCOMMITTED
        r = rng.random(cfg.n_bees)

        # uncommitted -> commit to site i with prob v_i*(discover + recruit*frac_i)*dt
        rate_to = v * (cfg.discover + cfg.recruit * frac)          # (n,)
        p_to = np.clip(rate_to * cfg.dt, 0, 1)
        cum = np.concatenate([[0.0], np.cumsum(p_to)])
        nxt = s.copy()
        if u.any():
            ru = r[u]
            choice = np.searchsorted(cum, ru) - 1                 # -1 stay uncommitted, else site index
            choice = np.where(ru >= cum[-1], UNCOMMITTED, choice)
            nxt[u] = np.where(choice < 0, UNCOMMITTED, choice)

        # committed -> uncommitted via abandonment + cross-inhibition from rival sites
        for i in range(n):
            ci = s == i
            if not ci.any():
                continue
            inhib = cfg.inhibit * (np.sum(v * frac) - v[i] * frac[i]) if cross_inhibition else 0.0
            p_leave = np.clip((cfg.abandon + inhib) * cfg.dt, 0, 1)
            leave = ci & (r < p_leave)
            nxt[leave] = UNCOMMITTED
        s = nxt
        record(t)
    return {"frac": frac_hist, "uncommitted": unc_hist, "n": n, "v": v}


def decision(frac_hist, quorum: float = 0.5):
    """Winning site (committed fraction crossing quorum at the end) or -1 if no consensus."""
    final = frac_hist[-1]
    i = int(final.argmax())
    return i if final[i] >= quorum else -1


def decided(frac_hist, quorum: float = 0.5) -> bool:
    return decision(frac_hist, quorum) >= 0


def accuracy(qualities, cfg: SwarmConfig, trials: int = 20, steps: int = 800, seed: int = 0,
             cross_inhibition: bool = True):
    """Fraction of trials that commit to the BEST site (value-sensitive correctness)."""
    rng = np.random.default_rng(seed)
    best = int(np.argmax(qualities))
    hits = 0
    for _ in range(trials):
        r = simulate(qualities, cfg, steps, seed=int(rng.integers(1 << 30)), cross_inhibition=cross_inhibition)
        if decision(r["frac"]) == best:
            hits += 1
    return hits / trials
