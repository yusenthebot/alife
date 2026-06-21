"""LIVE PHYLORATE — does the RATE law of cumulative innovation EMERGE from the live economy? (R166)

R165 (`phylorate.py`) measured the rate law dN/dt on an ABSTRACT registry model and found that
autocatalytic effort E(N) ∝ N gives super-linear innovation — but with an honest, load-bearing caveat:
*E(N) ∝ N was POSITED, not derived*. "Technology begets technology" was an assumed effort law. R166
closes that caveat by taking the rate law to the LIVE `GenesisWorld` — the real population of
evolved-neural agents that sense, metabolise, reproduce and die — and asking whether the autocatalytic
effort EMERGES from the world's own energy economy rather than being hand-wired.

The mechanism that makes it endogenous is already in the capstone world and was never built for this:
  * a newborn makes `innov_steps` combinatorial discoveries from its adjacent possible when it is born
    (`_acquire_repertoire`), so the per-step innovation EFFORT of the whole world ≈ the number of
    newborns ≈ proportional to the living population / its reproduction;
  * accumulated technique PAYS energy — the harvest gain is multiplied by (1 + tech_gain·tech)
    (`_harvest_gain`), so a deeper repertoire feeds more agents;
  * more energy → more reproduction → more newborns → more innovation attempts → deeper repertoire.

That loop — repertoire → energy → population → effort → repertoire — is an ENDOGENOUS autocatalysis:
the effort law E(N) is produced by the economy, not posited. The falsifiable prediction is that the
per-step discovery rate dN/dt should RISE with the accumulated repertoire N (the R165 super-linear
signature) and that the rise is CAUSED by the energy economy.

DECISIVE CONTROL — `tech_gain = 0` (mastery stops paying). The SAME combinatorial discovery machinery
runs on the SAME tech tree, but a deeper repertoire no longer earns extra energy, so the population no
longer grows with the repertoire. If the acceleration were intrinsic to the combinatorial adjacent
possible alone, it would survive; if it is the endogenous ECONOMY, it must vanish. (It vanishes — the
rate-vs-N slope goes from positive to ≤0 and the realized repertoire saturates several-fold lower.)

This module is deliberately thin: `step_trajectory` drives a live world and emits a trajectory dict in
EXACTLY the shape `phylorate.rate_vs_size` / `phylorate.acceleration` consume, so the abstract rate-law
instruments from R165 apply UNCHANGED to the live economy. The only new statistic is `rate_slope` —
the slope of the binned dN/dt-vs-N curve, the horizon-robust "is the rate rising with N" read used as
the live accelerating-or-not discriminator. Read-only on the world (calls world.step() and the existing
read-out `combinatorial_test()` only — no new sim mechanism, no extra RNG draws).

HONEST SCOPE: the live tech tree is bounded (`max_techniques`) and the population is bounded by
`capacity`/food, so the climb is the EARLY accelerating phase before those ceilings bite — "super-linear
while open", exactly as R165's capped regime predicts, not unbounded forever. The endogeneity claim is
the SHAPE contrast (rising vs flat) under the tech_gain control at matched N, not an unbounded exponent.
"""

from __future__ import annotations

import numpy as np

from alife.genesis import phylorate as ph


def step_trajectory(world, steps: int) -> dict:
    """Drive a live `GenesisWorld` for `steps` steps, logging per step the open-ended complexity
    (`pop_distinct` N = techniques known by the living population), the per-step discovery count
    (`new` = the non-negative increase in N), and the living workforce (`active`).

    Returns a dict with keys {step, n_distinct, new, active} — the first three are exactly what
    `phylorate.rate_vs_size` / `phylorate.acceleration` consume, so the R165 rate-law tools apply to
    the LIVE economy unchanged. Read-only: only calls `world.step()` and `world.combinatorial_test()`.
    Requires a combinatorial-culture world (else `combinatorial_test` is empty)."""
    step_arr = np.empty(steps, dtype=np.int64)
    nd_arr = np.empty(steps, dtype=np.int64)
    new_arr = np.empty(steps, dtype=np.int64)
    act_arr = np.empty(steps, dtype=np.int64)
    prev_nd = 0
    d0 = world.combinatorial_test()
    if d0:
        prev_nd = int(d0.get("pop_distinct", 0))
    for i in range(steps):
        world.step()
        d = world.combinatorial_test()
        nd = int(d.get("pop_distinct", prev_nd)) if d else prev_nd
        step_arr[i] = i + 1
        nd_arr[i] = nd
        new_arr[i] = max(nd - prev_nd, 0)
        act_arr[i] = int(world.pop.active().size)
        prev_nd = nd
    return {"step": step_arr, "n_distinct": nd_arr, "new": new_arr, "active": act_arr}


def rate_slope(out: dict, bins: int = 6) -> float:
    """Slope of the binned per-step rate dN/dt against the current size N (`phylorate.rate_vs_size`).

    > 0  the discovery rate RISES with the accumulated repertoire — super-linear / accelerating;
    ~ 0  constant rate (linear cumulative growth);
    < 0  the rate falls with N — decelerating / saturating.

    This is the horizon-robust live discriminator: with the energy economy on (tech_gain > 0) the live
    world's slope is positive; with it off the same machinery goes flat/negative. NaN if too few bins."""
    centers, rate = ph.rate_vs_size(out, bins=bins)
    if len(centers) < 2 or np.ptp(centers) == 0:
        return float("nan")
    return float(np.polyfit(centers, rate, 1)[0])
