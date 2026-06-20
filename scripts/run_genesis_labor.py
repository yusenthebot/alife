"""R146 — GENESIS Stage 3 division of labour: 3D GIF (agents coloured by ROLE) + panel + controls.

A two-stage food economy: food spawns RAW (inedible); an agent ripens nearby raw food into edible food
via an evolved PROCESS output, paying a cost. Ripe food is a LOCAL PUBLIC GOOD (any neighbour harvests it)
and decays back to raw — a continuous flow. Over clonal kin demes a RESPONSE-THRESHOLD division of labour
can emerge: agents process when local ripe food is scarce and harvest when it is abundant.

Three claims, three controls (all in-situ, never feeding selection):
  HEADLINE  — agents self-organise into processor/harvester roles; render coloured by instantaneous role.
  CONTROL A — task allocation EMERGES: corr(process-decision, local ripe proximity) goes negative under
              evolution (process when ripe scarce) and sits ~0 for a frozen genome.
  CONTROL B — allocation RAISES productivity: the evolved conditional world sustains a larger population
              than a scramble_allocation ablation (same processing budget, conditioning destroyed).
One sim at a time; GL context released after the render.
"""
import os
import sys
import time
from dataclasses import replace

import imageio.v2 as imageio
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.genesis.genesis import GenesisConfig, GenesisWorld

OUT = "runs/r146_labor"
os.makedirs(OUT, exist_ok=True)
PROC = np.array([0.96, 0.58, 0.12])    # orange = processing this step
HARV = np.array([0.18, 0.62, 0.78])    # teal   = harvesting this step


def cfg(**kw):
    return replace(GenesisConfig(), processing=True, n_founder_genomes=8, **kw)


def headline(steps, seed=0, render_every=175):
    from alife.render3d import Renderer3D
    c = cfg()
    w = GenesisWorld(c, seed=seed, evolve=True)
    keys = ("step", "population", "ripe_food", "directedness")
    hist = {k: [] for k in keys}
    cond, frac = [], []
    frames = []
    r = Renderer3D(c.world, width=720, height=540)
    t0 = time.time()
    for s in range(steps):
        w.step()
        if s % 50 == 0:
            snp = w.snapshot()
            for k in keys:
                hist[k].append(snp[k])
            al = w.process_allocation_test()
            cond.append(al.get("cond_ripe", 0.0)); frac.append(al.get("frac_processing", 0.0))
        if s % render_every == 0:
            act = w.pop.active()
            if act.size:
                gate, _ = w._gate_decision(act)
                col = np.where(gate[:, None], PROC, HARV)
                frames.append(r.render(w.pop.pos[act], w.pop.vel[act], col,
                                       cam_angle=s * 0.012, cam_elev=0.42, food=w.food[w.food_ripe]))
    r.ctx.release()
    w.save_checkpoint(os.path.join(OUT, "checkpoint.npz"))
    if frames:
        imageio.mimsave(os.path.join(OUT, "labor.gif"), frames, fps=12, loop=0)
    print(f"headline: {steps} steps {time.time()-t0:.1f}s, final pop {hist['population'][-1]:.0f} "
          f"ripe {hist['ripe_food'][-1]:.0f} frac_proc {frac[-1]:+.2f} cond_ripe {cond[-1]:+.3f}", flush=True)
    hist["cond_ripe"] = cond
    hist["frac_proc"] = frac
    return hist


def control_run(steps, seed, evolve=True, scramble=False):
    w = GenesisWorld(cfg(scramble_allocation=scramble), seed=seed, evolve=evolve)
    pops, conds = [], []
    for s in range(steps):
        w.step()
        if s >= steps - 1500 and s % 100 == 0:
            pops.append(w.snapshot()["population"])
            conds.append(w.process_allocation_test().get("cond_ripe", 0.0))
    return float(np.mean(pops)) if pops else 0.0, float(np.mean(conds)) if conds else 0.0


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 7000
    cs = int(sys.argv[2]) if len(sys.argv) > 2 else 4500
    print(f"=== headline division-of-labour run ({steps} steps, role-coloured 3D) ===", flush=True)
    h = headline(steps)

    print(f"=== CONTROL A (allocation emerges) + B (productivity), 2 seeds, {cs} steps ===", flush=True)
    evo_pop, evo_cond, frz_cond, scr_pop = [], [], [], []
    for seed in (0, 1):
        ep, ec = control_run(cs, seed, evolve=True, scramble=False)
        _, fc = control_run(cs, seed, evolve=False, scramble=False)
        sp, _ = control_run(cs, seed, evolve=True, scramble=True)
        evo_pop.append(ep); evo_cond.append(ec); frz_cond.append(fc); scr_pop.append(sp)
        print(f"  seed {seed}: evolve cond_ripe {ec:+.3f} pop {ep:.0f} | frozen cond {fc:+.3f} | "
              f"scramble pop {sp:.0f}", flush=True)
    print(f"  MEAN cond_ripe evolve {np.mean(evo_cond):+.3f} vs frozen {np.mean(frz_cond):+.3f}", flush=True)
    print(f"  MEAN population  evolve {np.mean(evo_pop):.0f} vs scramble {np.mean(scr_pop):.0f}", flush=True)

    fig, ax = plt.subplots(2, 3, figsize=(16, 9))
    st = np.array(h["step"])
    ax[0, 0].plot(st, h["population"], color="#1f77b4"); ax[0, 0].set_title("population (labour economy)")
    ax[0, 1].plot(st, h["ripe_food"], color="#d62728"); ax[0, 1].set_title("ripe (edible) food produced")
    ax[0, 2].plot(st, h["frac_proc"], color="#ff7f0e"); ax[0, 2].axhline(0.5, ls=":", color="k")
    ax[0, 2].set_title("fraction processing (role split)"); ax[0, 2].set_ylim(0, 1)
    ax[1, 0].plot(st, h["cond_ripe"], color="#2ca02c"); ax[1, 0].axhline(0, color="k", lw=0.5)
    ax[1, 0].set_title("corr(process, ripe-prox)  (<0 = allocate by need)")
    ax[1, 1].bar(["evolve", "frozen"], [np.mean(evo_cond), np.mean(frz_cond)], color=["#2ca02c", "#999999"])
    ax[1, 1].axhline(0, color="k", lw=0.5)
    ax[1, 1].set_title(f"CONTROL A cond_ripe: evo {np.mean(evo_cond):+.3f} vs frz {np.mean(frz_cond):+.3f}")
    ax[1, 2].bar(["evolve\n(allocated)", "scramble\n(same budget)"], [np.mean(evo_pop), np.mean(scr_pop)],
                 color=["#1f77b4", "#999999"])
    ax[1, 2].set_title(f"CONTROL B productivity: evo {np.mean(evo_pop):.0f} vs scr {np.mean(scr_pop):.0f}")
    fig.suptitle("GENESIS R146 — division of labour: two-stage food economy + kin-stabilised role "
                 "allocation\n(orange = processing, teal = harvesting in labor.gif)", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=100)
    print(f"wrote {OUT}/labor.gif and {OUT}/panel.png", flush=True)


if __name__ == "__main__":
    main()
