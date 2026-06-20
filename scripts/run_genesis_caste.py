"""R147 — GENESIS Stage 3 division of labour, attempt 2: a CONVEX specialization trade-off -> caste.

R146 (attempt 1) built a working two-stage food economy but no division of labour emerged: processing was
cheap and non-exclusive, so generalists doing both were optimal. R147 adds the diagnosed missing ingredient
— a heritable caste trait spec in [0,1] (0=harvester, 1=processor) with CONVEX (accelerating) returns to
specialization, so an intermediate generalist is strictly worse at BOTH tasks than a mix of specialists:
  - harvest gain  = food_value*(1-spec)^spec_gamma   (only pure harvesters eat at full value)
  - process reach = process_radius*spec              (ripened volume ~spec^3 -> strongly convex)
  - a processor earns process_payment when a HARVESTER eats a mote IT ripened (a wage / trade), so
    processors live on wages and harvesters on food -> genuine producer/consumer interdependence.

Three claims, each with a control (all in-situ, never feeding selection):
  HEADLINE  — the population self-organises into a bimodal processor/harvester CASTE; render coloured by spec.
  CONTROL A — DIFFERENTIATION: spec bimodality (Sarle BC) is high under evolution and the two roles are
              played by distinct castes (processors high-spec, harvesters low-spec), vs a frozen genome.
  CONTROL B — PRODUCTIVITY: the evolved specialised economy sustains a larger population than a
              force_generalist control (every agent pinned at spec=0.5 — a monomorphic, non-specialised world).
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

OUT = "runs/r147_caste"
os.makedirs(OUT, exist_ok=True)
PROC = np.array([0.96, 0.55, 0.10])    # orange = processor caste (high spec)
HARV = np.array([0.16, 0.60, 0.80])    # teal   = harvester caste (low spec)
PROCESS_COST = 1.0                      # the caste regime wants cheap labour (see module docstring)


def cfg(**kw):
    return replace(GenesisConfig(), processing=True, specialize=True, process_cost=PROCESS_COST, **kw)


def caste_color(spec):
    s = np.clip(spec, 0.0, 1.0)[:, None]
    return HARV * (1.0 - s) + PROC * s


def headline(steps, seed=0, render_every=160):
    from alife.render3d import Renderer3D
    c = cfg()
    w = GenesisWorld(c, seed=seed, evolve=True)
    keys = ("step", "population", "ripe_food")
    hist = {k: [] for k in keys}
    bimod, fracspec, gap = [], [], []
    frames = []
    r = Renderer3D(c.world, width=720, height=540)
    t0 = time.time()
    for s in range(steps):
        w.step()
        if s % 50 == 0:
            snp = w.snapshot()
            for k in keys:
                hist[k].append(snp[k])
            ct = w.caste_test()
            bimod.append(ct.get("bimodality", 0.0)); fracspec.append(ct.get("frac_specialist", 0.0))
            gap.append(ct.get("proc_spec", 0.0) - ct.get("harv_spec", 0.0))
        if s % render_every == 0:
            act = w.pop.active()
            if act.size:
                frames.append(r.render(w.pop.pos[act], w.pop.vel[act], caste_color(w.pop.spec[act]),
                                       cam_angle=s * 0.012, cam_elev=0.42, food=w.food[w.food_ripe]))
    r.ctx.release()
    w.save_checkpoint(os.path.join(OUT, "checkpoint.npz"))
    if frames:
        imageio.mimsave(os.path.join(OUT, "caste.gif"), frames, fps=12, loop=0)
    final_spec = w.pop.spec[w.pop.active()]
    print(f"headline: {steps} steps {time.time()-t0:.1f}s pop {hist['population'][-1]:.0f} "
          f"bimod {bimod[-1]:.3f} fracspec {fracspec[-1]:.2f} caste-gap {gap[-1]:+.2f}", flush=True)
    hist.update(bimod=bimod, fracspec=fracspec, gap=gap, final_spec=final_spec)
    return hist


def control_run(steps, seed, evolve=True, fg=False):
    w = GenesisWorld(cfg(force_generalist=fg), seed=seed, evolve=evolve)
    pops, bms, gaps = [], [], []
    for s in range(steps):
        w.step()
        if s >= steps - 1500 and s % 100 == 0:
            pops.append(w.snapshot()["population"])
            ct = w.caste_test()
            bms.append(ct.get("bimodality", 0.0))
            gaps.append(ct.get("proc_spec", 0.0) - ct.get("harv_spec", 0.0))
    return (float(np.mean(pops)) if pops else 0.0,
            float(np.mean(bms)) if bms else 0.0,
            float(np.mean(gaps)) if gaps else 0.0)


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    cs = int(sys.argv[2]) if len(sys.argv) > 2 else 3500
    seeds = (0, 1, 2)
    print(f"=== headline caste run ({steps} steps, spec-coloured 3D) ===", flush=True)
    h = headline(steps)

    print(f"=== CONTROLS A (differentiation) + B (productivity), {len(seeds)} seeds, {cs} steps ===", flush=True)
    evo_pop, evo_bm, evo_gap, frz_bm, frz_gap, fg_pop = [], [], [], [], [], []
    for seed in seeds:
        ep, eb, eg = control_run(cs, seed, evolve=True)
        _, fb, fgp = control_run(cs, seed, evolve=False)
        gp, _, _ = control_run(cs, seed, evolve=True, fg=True)
        evo_pop.append(ep); evo_bm.append(eb); evo_gap.append(eg)
        frz_bm.append(fb); frz_gap.append(fgp); fg_pop.append(gp)
        print(f"  seed {seed}: EVOLVE bimod {eb:.3f} gap {eg:+.2f} pop {ep:.0f} | "
              f"FROZEN bimod {fb:.3f} gap {fgp:+.2f} | FORCEGEN pop {gp:.0f}", flush=True)
    mEb, mFb = np.mean(evo_bm), np.mean(frz_bm)
    mEg, mFg = np.mean(evo_gap), np.mean(frz_gap)
    mEp, mGp = np.mean(evo_pop), np.mean(fg_pop)
    print(f"  MEAN bimodality   evolve {mEb:.3f} vs frozen {mFb:.3f}", flush=True)
    print(f"  MEAN caste-gap    evolve {mEg:+.3f} vs frozen {mFg:+.3f}  (proc_spec - harv_spec)", flush=True)
    print(f"  MEAN population   evolve {mEp:.0f} vs force-generalist {mGp:.0f}", flush=True)
    diff = mEb > mFb + 0.05 and mEg > 0.10 and mEp > mGp * 1.15
    print(f"  VERDICT: {'DIVISION OF LABOUR EMERGED' if diff else 'NEGATIVE (no caste / no productivity gain)'}",
          flush=True)

    fig, ax = plt.subplots(2, 3, figsize=(16, 9))
    st = np.array(h["step"])
    ax[0, 0].plot(st, h["population"], color="#1f77b4"); ax[0, 0].set_title("population (caste economy)")
    ax[0, 1].plot(st, h["bimod"], color="#9467bd"); ax[0, 1].axhline(0.555, ls=":", color="k")
    ax[0, 1].set_title("spec bimodality (Sarle BC; >.555 bimodal)"); ax[0, 1].set_ylim(0, 1)
    ax[0, 2].plot(st, h["gap"], color="#ff7f0e"); ax[0, 2].axhline(0, color="k", lw=0.5)
    ax[0, 2].set_title("caste gap: proc_spec - harv_spec  (>0 = roles by caste)")
    ax[1, 0].hist(h["final_spec"], bins=24, range=(0, 1), color="#8c564b")
    ax[1, 0].set_title("final spec distribution (two modes = two castes)"); ax[1, 0].set_xlabel("spec")
    ax[1, 1].bar(["evolve", "frozen"], [mEb, mFb], color=["#9467bd", "#999999"])
    ax[1, 1].axhline(0.555, ls=":", color="k")
    ax[1, 1].set_title(f"CONTROL A bimodality: evo {mEb:.3f} vs frz {mFb:.3f}")
    ax[1, 2].bar(["evolve\n(caste)", "force\ngeneralist"], [mEp, mGp], color=["#1f77b4", "#999999"])
    ax[1, 2].set_title(f"CONTROL B productivity: evo {mEp:.0f} vs forcegen {mGp:.0f}")
    verdict = "DIVISION OF LABOUR EMERGED" if diff else "HONEST NEGATIVE"
    fig.suptitle(f"GENESIS R147 — convex specialization trade-off -> caste division of labour.  {verdict}\n"
                 "(orange = processor caste, teal = harvester caste in caste.gif)", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=100)
    print(f"wrote {OUT}/caste.gif and {OUT}/panel.png", flush=True)


if __name__ == "__main__":
    main()
