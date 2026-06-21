"""R164 — GENESIS GENUINELY UNBOUNDED generative tech space.

R150's combinatorial culture explored a FIXED pre-built tree of `max_techniques`, so frontier depth
ceilinged at the cap. R164 lifts the ceiling: a technique IS the lazily-materialized composition of two
known parents (registry, no pre-allocation), so the reachable space is the infinite closure of the seeds
under pairing and frontier depth is bounded only by the number of composition rounds — open-ended by
construction (after t rounds the deepest reachable level is exactly t).

DECISIVE CONTROL — cap=None vs cap=K on IDENTICAL dynamics/seed: the capped run's depth freezes the moment
its registry fills (the R150 regime); the uncapped run climbs far past it with no asymptote. Panels:
  (0,0) frontier depth vs step       — UNBOUNDED keeps climbing; CAPPED plateaus at the cap.
  (0,1) repertoire breadth vs step   — distinct techniques materialized; capped flatlines at K.
  (1,0) temporal ladder scatter      — level vs first-appearance step (deeper == later) over the climb.
  (1,1) depth gain in final third    — unbounded still rising vs capped frozen at 0 (no-plateau read-out).

One process, blocking, no sim/GL (pure numpy registry). 禁止造假 — every number read from the live run.
"""
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from alife.genesis import unbounded as ub
from alife.genesis.phylogeny import _spearman


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 220
    seeds = [0, 1]
    n_agents, n_seed, fidelity = 40, 6, 0.5
    cap_k = 100
    outdir = "runs/r164_unbounded"
    os.makedirs(outdir, exist_ok=True)

    t0 = time.time()
    free = [ub.run_population(n_agents, n_seed, steps, fidelity, cap=None, seed=s) for s in seeds]
    capped = [ub.run_population(n_agents, n_seed, steps, fidelity, cap=cap_k, seed=s) for s in seeds]

    f_ml = np.array([r["max_level"][-1] for r in free])
    c_ml = np.array([r["max_level"][-1] for r in capped])
    f_nd = np.array([r["n_distinct"][-1] for r in free])
    # invariant: chain_len == level for every materialized technique (cumulative-descent depth is literal)
    sp = free[0]["space"]
    invariant_ok = all(sp.chain_len(k) == sp.levels[k] for k in range(sp.n))
    first, lvl = ub.ladder_arrays(sp)
    corr = _spearman(lvl, first)

    third = steps // 3
    f_gain = np.array([r["max_level"][-1] - r["max_level"][2 * third] for r in free])
    c_gain = np.array([r["max_level"][-1] - r["max_level"][2 * third] for r in capped])

    print(f"UNBOUNDED depth {f_ml}  breadth {f_nd}  | CAPPED(K={cap_k}) depth {c_ml}  "
          f"breadth {[int(r['n_distinct'][-1]) for r in capped]}", flush=True)
    print(f"  final-third depth gain: UNBOUNDED {f_gain} (still climbing) vs CAPPED {c_gain} (frozen)",
          flush=True)
    print(f"  cumulative-descent invariant chain_len==level: {invariant_ok}  | "
          f"temporal ladder level<->first_step Spearman = {corr:.3f}  ({time.time()-t0:.0f}s)", flush=True)

    fig, ax = plt.subplots(2, 2, figsize=(13, 9))

    for j, (r, c) in enumerate(zip(free, capped)):
        ax[0, 0].plot(r["step"], r["max_level"], color="crimson", lw=2.0, alpha=0.9,
                      label="UNBOUNDED (no cap)" if j == 0 else None)
        ax[0, 0].plot(c["step"], c["max_level"], color="dimgray", lw=2.0, alpha=0.9, ls="--",
                      label=f"CAPPED (K={cap_k})" if j == 0 else None)
    ax[0, 0].set_xlabel("step"); ax[0, 0].set_ylabel("frontier depth (max level)")
    ax[0, 0].set_title("OPEN-ENDED: depth climbs with NO ceiling vs capped plateau"); ax[0, 0].legend(fontsize=9)

    for j, (r, c) in enumerate(zip(free, capped)):
        ax[0, 1].plot(r["step"], r["n_distinct"], color="crimson", lw=2.0, alpha=0.9,
                      label="UNBOUNDED" if j == 0 else None)
        ax[0, 1].plot(c["step"], c["n_distinct"], color="dimgray", lw=2.0, alpha=0.9, ls="--",
                      label="CAPPED" if j == 0 else None)
    ax[0, 1].axhline(cap_k, color="dimgray", lw=0.8, alpha=0.5)
    ax[0, 1].set_xlabel("step"); ax[0, 1].set_ylabel("distinct techniques materialized (breadth)")
    ax[0, 1].set_title("breadth: unbounded space keeps generating, capped flatlines at K")
    ax[0, 1].legend(fontsize=9)

    ax[1, 0].scatter(first, lvl, s=10, alpha=0.35, color="crimson", edgecolors="none")
    ax[1, 0].set_xlabel("first-appearance step"); ax[1, 0].set_ylabel("technique level (depth)")
    ax[1, 0].set_title(f"TEMPORAL LADDER over the climb: deeper == later (Spearman {corr:.2f})")

    x = np.arange(len(seeds))
    ax[1, 1].bar(x - 0.18, f_gain, width=0.36, color="crimson", label="UNBOUNDED (still climbing)")
    ax[1, 1].bar(x + 0.18, c_gain, width=0.36, color="dimgray", label="CAPPED (frozen)")
    ax[1, 1].axhline(0, color="k", lw=0.8)
    ax[1, 1].set_xticks(x); ax[1, 1].set_xticklabels([f"seed {s}" for s in seeds])
    ax[1, 1].set_ylabel("depth gained in final third of run")
    ax[1, 1].set_title("no-plateau read-out: unbounded keeps deepening, capped does not")
    ax[1, 1].legend(fontsize=9)

    fig.suptitle(f"R164 — GENUINELY UNBOUNDED tech space: frontier depth open-ended (no cap), "
                 f"cumulative-descent invariant {invariant_ok}", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    path = os.path.join(outdir, "panel.png")
    fig.savefig(path, dpi=110)
    plt.close(fig)
    print(f"  wrote {path}", flush=True)


if __name__ == "__main__":
    main()
