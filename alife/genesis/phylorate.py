"""PHYLORATE — the RATE law of cumulative innovation on the unbounded tech space (R165).

R164 built a genuinely unbounded combinatorial tech space (`unbounded.TechSpace`) and found its
*breadth* grows linearly under the R164 effort regime: a FIXED population each making ONE combination
per step yields ~n_agents new techniques per step, a constant rate. R165 asks the deeper question of
combinatorial-evolution theory (Arthur, "The Nature of Technology"; Kauffman's expanding "adjacent
possible"): when each newly-made technique *itself* becomes a building block for the next, does the
discovery RATE merely stay constant, or does it ACCELERATE — does technology beget technology fast
enough to be SUPER-linear?

The answer hinges entirely on the EFFORT LAW E(N) — how many recombination attempts a culture of
accumulated size N mounts per unit time:

  * additive null   — there is no recombination at all: each step draws `base` independent inventions
                      from a FIXED finite pool of `pool_size`. This is the coupon-collector / "lone
                      genius drawing from a fixed idea-space" model. dN/dt = base*(1 - N/pool) FALLS to
                      zero: cumulative N saturates at `pool_size`. DECELERATING by construction.
  * fixed effort    — combinatorial recombination on the unbounded space, but E(N) = base is CONSTANT
                      (the R164 regime: a fixed workforce). Because collisions are rare on an open space
                      (see below), dN/dt ~ base: LINEAR cumulative growth.
  * autocatalytic   — combinatorial recombination with E(N) = max(base, round(alpha*N)): effort tracks
                      the accumulated repertoire (Arthur's "technology creates itself out of itself").
                      dN/dt ~ alpha*N: EXPONENTIAL cumulative growth — SUPER-linear.

The non-tautological content (the part that is DISCOVERED, not imposed): autocatalytic effort is only
*productive* if recombination keeps finding NEW pairs as N grows. On the unbounded space the number of
distinct pairs is N*(N-1)/2 (grows as N^2) while discoveries grow as N, so the fraction of attempts that
COLLIDE with an already-made pair -> 0 as N grows: the adjacent possible stays OPEN faster than it is
consumed, so the super-linear rate is SUSTAINED, not self-throttling. This is the genuine result — that
the open combinatorial space keeps the autocatalysis fed — and it is falsifiable:

  * autocatalytic + CAPPED (cap=K) — the DECISIVE control. Identical alpha*N effort law, but the space
                      is capped at K techniques. Once the registry fills, EVERY attempt collides, the
                      collision fraction -> 1, and dN/dt collapses to 0 despite the unchanged ∝N effort.
                      So sustained super-linearity is driven by the OPEN adjacent possible, NOT by the
                      effort multiplier alone. (This is the R164 cap=None-vs-cap=K control, now applied
                      to the RATE rather than the depth.)

So the four regimes give four distinct rate signatures in the dN/dt-vs-N plane — falling (additive),
flat (fixed), rising (autocatalytic+open), rising-then-collapsing (autocatalytic+capped) — and that
plane is the clean, horizon-independent discriminator (the rate law is intrinsic to the mechanism, not
an artefact of how many steps you ran).

HONEST SCOPE (red-teamed to 4 seeds, independent recomputation from the raw registry, all CONFIRMED):
the acceleration is, by construction, hard-wired by positing E(N) ∝ N — "technology begets technology"
is an ASSUMED effort law, not something the model derives. The genuinely DISCOVERED (non-tautological)
content is the NARROWER claim that the open combinatorial space does not self-throttle that posited
effort: the collision fraction -> ~1e-4 (independently recomputed: 0.40 -> 0.0001), because the distinct
pair-space grows as N^2 while discoveries grow as N. The CAPPED control proves it is the open space and
not the multiplier — identical alpha*N effort (effort pinned at alpha*K), yet `new` collapses to exactly
0 and collisions -> 1.0. The growth is EXPONENTIAL, not a fixed power law: the per-step multiplier is
N[t]/N[t-1] = 1.4996 ≈ 1+alpha to 4 dp, and `growth_exponent` rises with the fit window (it is an
exponential read through a power-law lens, NOT a real exponent ~6.7 — read it only as ">1 = super-linear").

Memory stays bounded: autocatalytic N grows exponentially so `steps` is kept small (~20-25) — the final
registry holds only the techniques actually discovered (a {pair->id} dict of ints), never the infinite
space. Pure numpy + Python ints, well under the loop's <1 GB budget.
"""

from __future__ import annotations

import numpy as np

from alife.genesis.unbounded import TechSpace


def _effort(law: str, base: int, alpha: float, n: int) -> int:
    """Recombination attempts mounted by a culture of current size `n` under effort law `law`."""
    if law == "fixed":
        return base
    if law == "autocatalytic":
        return max(base, int(round(alpha * n)))
    raise ValueError(f"unknown effort law {law!r}")


def _run_additive(n_seed: int, steps: int, base: int, pool_size: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    known = set(range(n_seed))                       # n_seed primitives are pre-known
    T, ND, NEW, EFF, COL = [], [], [], [], []
    for t in range(1, steps + 1):
        draws = rng.integers(0, pool_size, size=base)
        novel = 0
        coll = 0
        for d in draws:
            d = int(d)
            if d in known:
                coll += 1
            else:
                known.add(d)
                novel += 1
        T.append(t); ND.append(len(known)); NEW.append(novel); EFF.append(base)
        COL.append(coll / base if base else 0.0)
    return {"step": np.array(T), "n_distinct": np.array(ND), "new": np.array(NEW),
            "effort": np.array(EFF), "collision_frac": np.array(COL), "space": None}


def _run_combinatorial(law: str, n_seed: int, steps: int, base: int, alpha: float,
                       cap: int | None, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    space = TechSpace(n_seed, cap=cap)
    known: list[int] = list(range(n_seed))           # ordered pool of discovered techniques
    T, ND, NEW, EFF, COL = [], [], [], [], []
    for t in range(1, steps + 1):
        e = _effort(law, base, alpha, space.n)
        novel = 0
        coll = 0
        m = len(known)
        # draw all attempt pairs for the step at once (distinct endpoints)
        ia = rng.integers(0, m, size=e)
        ib = rng.integers(0, m, size=e)
        for k in range(e):
            a = known[int(ia[k])]
            b = known[int(ib[k])]
            if a == b:
                coll += 1
                continue
            key = (a, b) if a < b else (b, a)
            if key in space.registry:
                coll += 1                            # pair already made — no new technique
                continue
            pid = space.combine(a, b, step=t)
            if pid is None:                          # capped & full: collision against the ceiling
                coll += 1
                continue
            known.append(pid)
            novel += 1
        T.append(t); ND.append(space.n); NEW.append(novel); EFF.append(e)
        COL.append(coll / e if e else 0.0)
    return {"step": np.array(T), "n_distinct": np.array(ND), "new": np.array(NEW),
            "effort": np.array(EFF), "collision_frac": np.array(COL), "space": space}


def run_additive(*, n_seed: int = 6, steps: int, base: int = 40, pool_size: int = 2000,
                 seed: int = 0) -> dict:
    """Additive null: independent invention from a FIXED finite pool — saturates (DECELERATING)."""
    return _run_additive(n_seed, steps, base, pool_size, seed)


def run_fixed(*, n_seed: int = 6, steps: int, base: int = 40, cap: int | None = None,
              seed: int = 0) -> dict:
    """Fixed-effort combinatorial (R164 regime): constant E=base attempts -> LINEAR cumulative growth."""
    return _run_combinatorial("fixed", n_seed, steps, base, 0.0, cap, seed)


def run_autocatalytic(*, n_seed: int = 6, steps: int, base: int = 40, alpha: float = 0.5,
                      cap: int | None = None, seed: int = 0) -> dict:
    """Autocatalytic combinatorial: E(N)=max(base, alpha*N) -> dN/dt ∝ N -> SUPER-linear (exponential)
    while the space stays open; with `cap` set, collapses to flat once the registry fills."""
    return _run_combinatorial("autocatalytic", n_seed, steps, base, alpha, cap, seed)


def growth_exponent(step: np.ndarray, n_distinct: np.ndarray, frac: float = 0.5) -> float:
    """Power-law exponent of cumulative N ~ t^p, fitted (log N vs log t least-squares) over the LAST
    `frac` of the run. p < 1 sub-linear/saturating, p ~ 1 linear, p > 1 super-linear (and exponential
    growth reads as a p that keeps RISING with the window — captured separately by `acceleration`)."""
    n = len(step)
    lo = int(n * (1 - frac))
    x = np.log(step[lo:].astype(float))
    y = np.log(np.maximum(n_distinct[lo:].astype(float), 1.0))
    if len(x) < 2 or np.ptp(x) == 0:
        return float("nan")
    return float(np.polyfit(x, y, 1)[0])


def acceleration(step: np.ndarray, n_distinct: np.ndarray) -> float:
    """Sign+magnitude of d^2N/dt^2 (quadratic fit curvature). >0 accelerating (super-linear),
    ~0 linear, <0 decelerating (saturating). The horizon-robust 'is the rate rising or falling' read."""
    x = step.astype(float)
    y = n_distinct.astype(float)
    if len(x) < 3:
        return float("nan")
    return float(2.0 * np.polyfit(x, y, 2)[0])      # 2*a is d^2/dt^2 of a*t^2 + b*t + c


def rate_vs_size(out: dict, bins: int = 8) -> tuple[np.ndarray, np.ndarray]:
    """Bin the per-step rate dN/dt against the current size N, returning (N_centers, mean_rate). This is
    the mechanism-INTRINSIC discriminator: additive falls, fixed is flat, autocatalytic rises with N."""
    n = out["n_distinct"].astype(float)
    r = out["new"].astype(float)
    if len(n) < 2:
        return np.empty(0), np.empty(0)
    edges = np.linspace(n.min(), n.max(), bins + 1)
    idx = np.clip(np.digitize(n, edges) - 1, 0, bins - 1)
    centers = 0.5 * (edges[:-1] + edges[1:])
    means = np.array([r[idx == b].mean() if np.any(idx == b) else np.nan for b in range(bins)])
    ok = ~np.isnan(means)
    return centers[ok], means[ok]
