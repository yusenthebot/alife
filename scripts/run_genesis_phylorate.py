"""R165 — GENESIS PHYLORATE: the RATE law of cumulative innovation on the unbounded tech space.

R164 showed the unbounded combinatorial space's BREADTH grows linearly under a fixed-effort regime.
R165 asks the Arthur/Kauffman question: when each new technique becomes a building block AND effort
tracks the accumulated repertoire, does innovation ACCELERATE (super-linear)? Four regimes, four
distinct rate signatures:
  * additive null        — independent invention from a FIXED pool: saturates (DECELERATING).
  * fixed-effort combo   — constant attempts on the open space: LINEAR.
  * autocatalytic + OPEN — E(N) ∝ N on the open space: SUPER-linear (exponential), SUSTAINED because the
                           collision fraction -> 0 (pair-space ~N^2 grows faster than discoveries ~N).
  * autocatalytic+CAPPED — DECISIVE control: identical ∝N effort, but a capped space -> collisions -> 1,
                           rate collapses to 0. So super-linearity is the OPEN adjacent possible, not the
                           effort multiplier alone (the R164 cap control, now on the RATE).

Panels:
  (0,0) cumulative N vs step, LOG-y     — additive plateaus; fixed straightish; autocat OPEN = straight
                                          line on log-y (exponential); autocat CAPPED bends to the cap.
  (0,1) THE MONEY PLOT dN/dt vs N       — falling / flat / rising / rising-then-zero signatures.
  (1,0) collision fraction vs N         — autocat OPEN stays low (adjacent possible open) vs CAPPED -> 1.
  (1,1) acceleration d^2N/dt^2 bar      — sign discriminator: <0 / ~0 / >0 / (capped <0 after collapse).

One process, blocking, pure numpy (no sim/GL). 禁止造假 — every number read from the live run.
"""
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from alife.genesis import phylorate as pr


def main():
    seeds = [0, 1]
    add_steps = 200          # additive/fixed need a long horizon to show their (slow) laws
    auto_steps = 22          # autocatalytic is exponential — keep short so N stays bounded
    base, alpha, pool, cap_k = 10, 0.5, 1500, 300
    outdir = "runs/r165_phylorate"
    os.makedirs(outdir, exist_ok=True)

    t0 = time.time()
    additive = [pr.run_additive(steps=add_steps, base=40, pool_size=pool, seed=s) for s in seeds]
    fixed = [pr.run_fixed(steps=add_steps, base=40, seed=s) for s in seeds]
    auto_open = [pr.run_autocatalytic(steps=auto_steps, base=base, alpha=alpha, cap=None, seed=s) for s in seeds]
    auto_cap = [pr.run_autocatalytic(steps=auto_steps, base=base, alpha=alpha, cap=cap_k, seed=s) for s in seeds]

    def acc(runs):
        return np.array([pr.acceleration(r["step"], r["n_distinct"]) for r in runs])

    a_add, a_fix, a_auo, a_auc = acc(additive), acc(fixed), acc(auto_open), acc(auto_cap)
    exp_open = np.array([pr.growth_exponent(r["step"], r["n_distinct"], 0.5) for r in auto_open])
    col_open = np.array([r["collision_frac"][-5:].mean() for r in auto_open])
    col_cap = np.array([r["collision_frac"][-1] for r in auto_cap])
    n_open = np.array([r["n_distinct"][-1] for r in auto_open])
    n_cap = np.array([r["n_distinct"][-1] for r in auto_cap])

    print(f"acceleration d2N/dt2: additive {a_add} (<0) | fixed {a_fix} (~0) | "
          f"autocat-OPEN {a_auo} (>0) | autocat-CAPPED {a_auc}", flush=True)
    print(f"autocat-OPEN late power-law exponent {exp_open} (>>1 = super-linear)", flush=True)
    print(f"autocat OPEN final N {n_open} (collision {col_open}) vs CAPPED final N {n_cap} "
          f"(collision {col_cap} -> rate collapsed)  ({time.time()-t0:.0f}s)", flush=True)

    cols = {"additive": "slategray", "fixed": "seagreen", "open": "crimson", "capped": "darkorange"}
    fig, ax = plt.subplots(2, 2, figsize=(13, 9))

    # (0,0) cumulative N vs step, log-y
    for j, (ad, fx, ao, ac) in enumerate(zip(additive, fixed, auto_open, auto_cap)):
        lab = (j == 0)
        ax[0, 0].plot(ad["step"], ad["n_distinct"], color=cols["additive"], lw=2,
                      label="additive null (saturates)" if lab else None)
        ax[0, 0].plot(fx["step"], fx["n_distinct"], color=cols["fixed"], lw=2,
                      label="fixed-effort (linear)" if lab else None)
        ax[0, 0].plot(ao["step"], ao["n_distinct"], color=cols["open"], lw=2,
                      label="autocatalytic + OPEN (super-linear)" if lab else None)
        ax[0, 0].plot(ac["step"], ac["n_distinct"], color=cols["capped"], lw=2, ls="--",
                      label=f"autocatalytic + CAPPED (K={cap_k})" if lab else None)
    ax[0, 0].axhline(cap_k, color=cols["capped"], lw=0.7, alpha=0.5)
    ax[0, 0].set_yscale("log"); ax[0, 0].set_xlabel("step"); ax[0, 0].set_ylabel("cumulative techniques N (log)")
    ax[0, 0].set_title("cumulative innovation: autocat+OPEN is a straight LOG line (exponential)")
    ax[0, 0].legend(fontsize=8)

    # (0,1) the money plot: dN/dt vs N
    for name, runs, marker in [("additive", additive, "o"), ("fixed", fixed, "s"),
                                ("open", auto_open, "^"), ("capped", auto_cap, "x")]:
        c, r = pr.rate_vs_size(runs[0], bins=8)
        ax[0, 1].plot(c, r, marker=marker, color=cols[name], lw=1.8, label=name)
    ax[0, 1].set_xscale("log"); ax[0, 1].set_xlabel("current size N (log)")
    ax[0, 1].set_ylabel("discovery rate dN/dt (new per step)")
    ax[0, 1].set_title("RATE vs SIZE — falling / flat / rising / rising-then-0 (mechanism-intrinsic)")
    ax[0, 1].legend(fontsize=8)

    # (1,0) collision fraction vs N (combinatorial runs)
    for name, runs in [("fixed", fixed), ("open", auto_open), ("capped", auto_cap)]:
        r = runs[0]
        ax[1, 0].plot(r["n_distinct"], r["collision_frac"], color=cols[name], lw=2, label=name)
    ax[1, 0].set_xlabel("current size N"); ax[1, 0].set_ylabel("collision fraction (attempts that hit a known pair)")
    ax[1, 0].set_title("adjacent possible stays OPEN (collision low) vs CAPPED -> 1 (throttled)")
    ax[1, 0].legend(fontsize=8); ax[1, 0].set_ylim(-0.03, 1.03)

    # (1,1) acceleration bar
    x = np.arange(len(seeds))
    w = 0.2
    ax[1, 1].bar(x - 1.5 * w, a_add, w, color=cols["additive"], label="additive (<0)")
    ax[1, 1].bar(x - 0.5 * w, a_fix, w, color=cols["fixed"], label="fixed (~0)")
    ax[1, 1].bar(x + 0.5 * w, a_auo, w, color=cols["open"], label="autocat OPEN (>0)")
    ax[1, 1].bar(x + 1.5 * w, a_auc, w, color=cols["capped"], label="autocat CAPPED")
    ax[1, 1].axhline(0, color="k", lw=0.8)
    ax[1, 1].set_yscale("symlog"); ax[1, 1].set_xticks(x); ax[1, 1].set_xticklabels([f"seed {s}" for s in seeds])
    ax[1, 1].set_ylabel("acceleration d^2N/dt^2 (symlog)")
    ax[1, 1].set_title("acceleration sign = the rate-law signature")
    ax[1, 1].legend(fontsize=8)

    fig.suptitle("R165 PHYLORATE — autocatalytic recombination on an OPEN combinatorial space gives "
                 "SUPER-LINEAR (accelerating) innovation; cap collapses it", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    path = os.path.join(outdir, "panel.png")
    fig.savefig(path, dpi=110)
    print(f"wrote {path}  ({time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
