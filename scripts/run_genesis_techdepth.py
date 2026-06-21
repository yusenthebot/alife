"""R167 REAL-VERIFY — is the living civilization's technology a CONNECTED cumulative DAG or a flat scatter?

Runs the live combinatorial GenesisWorld in two regimes that differ ONLY in `combo_prereqs`:
  * COMBINATORIAL (combo_prereqs=True)  — discovery is gated on prerequisites (cumulative culture).
  * ADDITIVE NULL  (combo_prereqs=False) — discovery ignores prerequisites (a flat scatter), same tree.

The headline inversion (see techdepth.py): the ADDITIVE null is BROADER and reaches a HIGHER nominal tree
level -- by breadth/max_level it looks more advanced -- yet its realized dependency DAG is DISCONNECTED
(closure -> ~0.15, connected depth collapses), while the COMBINATORIAL repertoire is a prereq-closed,
deep CONNECTED ladder (closure ~1, connected depth ~ nominal level). So cumulative culture is structurally
deep-and-connected, not broad. One sim at a time; pure numpy/KD-tree, well under 1 GB.

Usage: scripts/run.sh scripts/run_genesis_techdepth.py [steps]
"""
import os
import sys
import time
from dataclasses import replace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from alife.genesis.genesis import GenesisConfig, GenesisWorld
from alife.genesis import techdepth as td
from alife.world3d import World3D

OUT = "runs/r167_techdepth"
os.makedirs(OUT, exist_ok=True)


def cfg(combo_prereqs):
    # tree large enough (8000) that the additive scatter stays a sparse SUBSET, so its broken structure is
    # visible rather than a saturated everything-known tree that is trivially closed.
    return replace(GenesisConfig(world=World3D(size=70.0), n0=200, capacity=2000),
                   processing=True, building=True, culture=True, combinatorial=True,
                   combo_prereqs=combo_prereqs, max_techniques=20000, n_seed_tech=8, innov_steps=1,
                   hearth_reach_per_strength=3.0, hearth_radius=12.0, tech_gain=0.35)


def draw_dag(ax, world, color, title):
    """Scatter the society's known techniques by tree level (y) with realized prereq edges, so a connected
    cumulative ladder is visually distinct from a disconnected scatter."""
    pa, pb, level, n_seed = world._tree_pa, world._tree_pb, world._tree_level, world.cfg.n_seed_tech
    known = td.society_repertoire(world)
    idx = np.where(known)[0]
    rng = np.random.default_rng(0)
    x = rng.uniform(0, 1, size=known.shape[0])                 # horizontal jitter per technique
    cd = td.connected_depth_array(known, pa, pb, level, n_seed)
    # edges of the realized DAG (both endpoints known); cap drawn edges for legibility
    ch, par = td.realized_edges(known, pa, pb, n_seed)
    if ch.size > 1500:
        sel = rng.choice(ch.size, 1500, replace=False)
        ch, par = ch[sel], par[sel]
    for c, p in zip(ch, par):
        ax.plot([x[c], x[p]], [level[c], level[p]], color=color, alpha=0.10, lw=0.5, zorder=1)
    # connected (cd>0 or seed) vs rootless (known but no held foundation) nodes
    rootless = known.copy(); rootless[:] = False
    rootless[idx] = (cd[idx] == 0) & (idx >= n_seed)
    conn_nodes = known & ~rootless
    ax.scatter(x[conn_nodes], level[conn_nodes], s=8, color=color, alpha=0.7, zorder=2, label="connected")
    ax.scatter(x[rootless], level[rootless], s=8, color="#000000", alpha=0.5, marker="x",
               zorder=3, label="rootless (prereq missing)")
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("technique (jitter)"); ax.set_ylabel("tree level (depth)")
    ax.legend(fontsize=7, loc="upper right"); ax.grid(alpha=0.2)


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    seeds = (0, 1)
    regimes = [("COMBINATORIAL", True, "#1f78b4"), ("ADDITIVE NULL", False, "#d6263a")]
    results = {}
    last_world = {}
    t_all = time.time()
    for label, cp, color in regimes:
        for sd in seeds:
            t0 = time.time()
            w = GenesisWorld(cfg(cp), seed=sd)
            out = td.depth_trajectory(w, steps)
            results[(label, sd)] = (out, color)
            if sd == 0:
                last_world[label] = (w, color)
            print(f"{label:14s} seed{sd}: breadth={out['breadth'][-1]:5d} max_level={out['max_level'][-1]:3d} "
                  f"conn_depth={out['conn_depth'][-1]:3d} closure={out['closure'][-1]:.3f} "
                  f"active={out['active'][-1]:5d} {time.time()-t0:.0f}s", flush=True)

    fig, ax = plt.subplots(2, 3, figsize=(19, 11))
    # (A) connected depth vs step — the cumulative-ladder ratchet
    for (label, sd), (out, color) in results.items():
        ax[0, 0].plot(out["step"], out["conn_depth"], color=color, lw=2.4 if sd == 0 else 1.3,
                      ls="-" if sd == 0 else "--", label=f"{label} s{sd}")
    ax[0, 0].set_title("(A) CONNECTED depth vs step\nlongest fully-known prereq chain — combinatorial climbs",
                       fontsize=10)
    ax[0, 0].set_xlabel("step"); ax[0, 0].set_ylabel("connected depth")
    ax[0, 0].legend(fontsize=7); ax[0, 0].grid(alpha=0.3)
    # (B) breadth vs step — the additive null is BROADER (the misleading metric)
    for (label, sd), (out, color) in results.items():
        ax[0, 1].plot(out["step"], out["breadth"], color=color, lw=2.4 if sd == 0 else 1.3,
                      ls="-" if sd == 0 else "--")
    ax[0, 1].set_title("(B) breadth vs step (techniques known)\nADDITIVE null is far BROADER — yet shallower",
                       fontsize=10)
    ax[0, 1].set_xlabel("step"); ax[0, 1].set_ylabel("breadth = pop_distinct"); ax[0, 1].grid(alpha=0.3)
    # (C) closure vs BREADTH — saturation-proof matched-breadth view: combinatorial is prereq-closed at
    # EVERY size; the additive scatter only closes by brute-force near tree saturation. At matched breadth
    # the gap is decisive.
    for (label, sd), (out, color) in results.items():
        ax[0, 2].plot(out["breadth"], out["closure"], color=color, lw=2.4 if sd == 0 else 1.3,
                      ls="-" if sd == 0 else "--", label=f"{label} s{sd}")
    ax[0, 2].set_title("(C) closure vs BREADTH (matched-breadth, saturation-proof)\n"
                       "combinatorial closed at every size · additive broken until it saturates the tree",
                       fontsize=10)
    ax[0, 2].set_xlabel("breadth = techniques known"); ax[0, 2].set_ylabel("closure fraction")
    ax[0, 2].set_ylim(0, 1.05); ax[0, 2].legend(fontsize=7); ax[0, 2].grid(alpha=0.3)
    # (D),(E) the realized DAG of the living civilization (seed 0)
    draw_dag(ax[1, 0], last_world["COMBINATORIAL"][0], "#1f78b4",
             "(D) COMBINATORIAL realized DAG\ndeep CONNECTED ladder (prereq-closed)")
    draw_dag(ax[1, 1], last_world["ADDITIVE NULL"][0], "#d6263a",
             "(E) ADDITIVE NULL realized DAG\nbroad but DISCONNECTED (rootless tips)")
    # (F) the dissociation: nominal max_level vs connected depth, per regime (mean over seeds)
    labels = ["COMBINATORIAL", "ADDITIVE NULL"]
    nom = [np.mean([results[(l, s)][0]["max_level"][-1] for s in seeds]) for l in labels]
    conn = [np.mean([results[(l, s)][0]["conn_depth"][-1] for s in seeds]) for l in labels]
    xb = np.arange(2); wsp = 0.35
    ax[1, 2].bar(xb - wsp / 2, nom, wsp, color="#bbbbbb", label="nominal max_level")
    ax[1, 2].bar(xb + wsp / 2, conn, wsp, color=["#1f78b4", "#d6263a"], label="CONNECTED depth")
    ax[1, 2].set_xticks(xb); ax[1, 2].set_xticklabels(labels, fontsize=9)
    ax[1, 2].set_title("(F) nominal vs connected depth\nadditive: high nominal, collapsed connected",
                       fontsize=10)
    ax[1, 2].set_ylabel("depth (levels)"); ax[1, 2].legend(fontsize=8); ax[1, 2].grid(alpha=0.3, axis="y")

    fig.suptitle("R167 GENESIS — cumulative culture is a CONNECTED dependency DAG, not a broad scatter "
                 "(combinatorial vs additive null, same tree)", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    path = os.path.join(OUT, "panel.png")
    fig.savefig(path, dpi=110)
    print(f"\nsaved {path}  ({time.time()-t_all:.0f}s total)", flush=True)


if __name__ == "__main__":
    main()
