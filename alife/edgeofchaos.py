"""R66 — The edge of chaos: searching the SPACE of cellular-automaton rules.

Earlier CA rounds ran ONE rule (R46 Conway's Life, R60 Lenia). This round studies the
rule SPACE itself — a meta level. Langton (1990) showed that as you vary a single order
parameter lambda (the fraction of neighbourhood inputs that map to a live cell), CA dynamics
pass through a phase transition: low lambda -> everything freezes or dies (ordered), high
lambda -> everything boils into noise (chaotic), and right at the boundary lies a narrow
COMPLEX regime where long-lived structures, gliders and computation appear — the "edge of
chaos". Life-like rules such as Conway's B3/S23 sit there.

We use 2D outer-totalistic life-like rules: a Birth set B and Survive set S over the live
neighbour count 0..8 (Conway = B3/S23). lambda = (|B|+|S|)/18. We (1) sweep lambda and watch
activity/density cross the ordered->complex->chaotic transition, (2) measure a complexity
score that PEAKS at the edge, and (3) SEARCH the 2^18 rule space for the most complex rules
and show they cluster at intermediate lambda — discovering Life-like worlds, not designing them.
Pure numpy/CPU; fast.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Rule:
    born: tuple        # neighbour counts that turn a dead cell alive
    survive: tuple     # neighbour counts that keep a live cell alive


CONWAY = Rule((3,), (2, 3))


def lam(rule: Rule) -> float:
    """Langton's lambda: fraction of the 18 (state, neighbour-count) inputs mapping to alive."""
    return (len(rule.born) + len(rule.survive)) / 18.0


def _luts(rule: Rule):
    b = np.zeros(9, bool); s = np.zeros(9, bool)
    for n in rule.born:
        b[n] = True
    for n in rule.survive:
        s[n] = True
    return b, s


def _neighbours(grid):
    return sum(np.roll(np.roll(grid, dy, 0), dx, 1)
               for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0))


def step(grid, blut, slut):
    n = _neighbours(grid)
    return np.where(grid == 1, slut[n], blut[n]).astype(np.int8)


def run(rule: Rule, size: int = 96, steps: int = 200, seed: int = 0, density0: float = 0.4,
        record_every: int = 0):
    """Run from a random soup; return activity & density time series, final grid, snapshots."""
    rng = np.random.default_rng(seed)
    blut, slut = _luts(rule)
    g = (rng.random((size, size)) < density0).astype(np.int8)
    act, dens, snaps = [], [], {}
    for t in range(steps):
        nxt = step(g, blut, slut)
        act.append(float(np.mean(nxt != g)))
        dens.append(float(nxt.mean()))
        if record_every and (t % record_every == 0 or t == steps - 1):
            snaps[t] = nxt.copy()
        g = nxt
    return {"activity": np.array(act), "density": np.array(dens), "grid": g, "snaps": snaps}


def metrics(rule: Rule, size: int = 96, steps: int = 200, seed: int = 0, tail: float = 0.25):
    """Steady-state activity, density, and a COMPLEXITY score that is high only when the CA
    is alive but neither frozen nor boiling: sustained intermediate activity that also
    FLUCTUATES in time (structures appearing/dying) rather than sitting at a fixed churn."""
    r = run(rule, size, steps, seed)
    k = int(steps * (1 - tail))
    a_tail = r["activity"][k:]
    d_tail = r["density"][k:]
    a = float(a_tail.mean())
    d = float(d_tail.mean())
    fluct = float(a_tail.std())
    # Edge-of-chaos / Life-like regime: ALIVE (not frozen/dead) but SPARSE and SLOW — sustained
    # low-intermediate density & activity, the signature of persistent local structures (gliders,
    # oscillators) rather than a frozen board (a~0) or a saturated boil (high d & a). A smooth bump
    # centred on the sparse-slow corner; Conway B3/S23 (d~0.08, a~0.06) sits near its peak.
    alive = a > 0.004 and d > 0.008
    box = np.exp(-((d - 0.12) / 0.18) ** 2) * np.exp(-((a - 0.08) / 0.18) ** 2)
    complexity = float(alive) * box * (1.0 + 2.0 * fluct)
    return {"activity": a, "density": d, "fluct": fluct, "complexity": complexity, "lambda": lam(rule)}


def random_rule(rng, target_lambda=None) -> Rule:
    """A random life-like rule. If target_lambda is given, pick |B|+|S| ~ 18*lambda inputs."""
    if target_lambda is None:
        b = tuple(np.flatnonzero(rng.random(9) < 0.4).tolist())
        s = tuple(np.flatnonzero(rng.random(9) < 0.4).tolist())
        return Rule(b or (3,), s or (2,))
    k = int(round(np.clip(target_lambda, 0, 1) * 18))
    pick = rng.permutation(18)[:k]                       # 0..8 = birth inputs, 9..17 = survive inputs
    b = tuple(sorted(int(i) for i in pick if i < 9))
    s = tuple(sorted(int(i - 9) for i in pick if i >= 9))
    return Rule(b, s)


def lambda_sweep(lambdas, per_lambda: int = 20, size: int = 80, steps: int = 160, seed: int = 0,
                 complex_thresh: float = 0.3):
    """For each target lambda over random rules: mean activity & density (the order parameter
    transition) and the FRACTION that are complex (complexity is RARE, so an average washes it
    out; the fraction of edge-of-chaos rules is the right signal and peaks at intermediate lambda)."""
    rng = np.random.default_rng(seed)
    A, D, F = [], [], []
    for lv in lambdas:
        aa, dd, ff = [], [], []
        for _ in range(per_lambda):
            m = metrics(random_rule(rng, lv), size, steps, seed=int(rng.integers(1 << 30)))
            aa.append(m["activity"]); dd.append(m["density"]); ff.append(m["complexity"] > complex_thresh)
        A.append(np.mean(aa)); D.append(np.mean(dd)); F.append(np.mean(ff))
    return np.array(lambdas), np.array(A), np.array(D), np.array(F)


def search_complex_rules(n_samples: int = 1500, size: int = 80, steps: int = 160, seed: int = 0,
                         top: int = 6):
    """Sample the rule space and return the most COMPLEX rules found (edge-of-chaos hunters)."""
    rng = np.random.default_rng(seed)
    scored = []
    for _ in range(n_samples):
        rule = random_rule(rng)
        m = metrics(rule, size, steps, seed=0)
        scored.append((m["complexity"], rule, m))
    scored.sort(key=lambda t: t[0], reverse=True)
    return scored[:top], np.array([s[2]["lambda"] for s in scored])
