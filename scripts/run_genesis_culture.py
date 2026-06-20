"""R149 — GENESIS Stage 5: CUMULATIVE CULTURE. The Stage-4 hearths become a CULTURAL REPOSITORY. Each agent
carries a LIFETIME-learned technique `tech` that is NOT in its genome: a newborn ACQUIRES it by copying (with
fidelity) the best technique recorded at the nearest hearth or its parent, then adds one innovation step. A
higher technique multiplies the food it harvests (so technique is selected) but every generation must RE-LEARN
it — so the accumulation lives in transmission + the built world, not the genes. Building writes the builder's
technique into the hearth's record (keeping the max), so the record RATCHETS up across generations far beyond a
single lifetime's innovation (Tomasello's ratchet). The accumulation is fidelity-bounded — it climbs across many
generations toward a finite fixed point ~innov/(1-fidelity), high but not literally unbounded.

The FALSIFIABLE headline metric is the LIVING population's mean technique (tech_mean): unlike the hearth record
(a never-reset high-water mark) it COLLAPSES back toward the asocial ceiling if transmission stops, so a non-zero
tech_mean is positive evidence that ongoing social learning sustains the accumulated culture.

Claims, each with a control (all in-situ, never feeding selection):
  HEADLINE  — the learned technique climbs across generations; render shows the population BRIGHTENING (dark =
              culturally naive, bright = high technique) over the run as knowledge accumulates.
  CONTROL A — IT'S CUMULATIVE CULTURE, not lone reinvention: WITH social learning (learn=True) the LIVING
              population's mean technique ratchets far above the ASOCIAL (learn=False) one-lifetime ceiling
              (which sits at innov_mean, ~0.15 — a single innovation draw, no accumulation).
  CONTROL B — IT'S CULTURAL, not genetic: with evolve=False (frozen genome) the technique STILL climbs — the
              ratchet runs through transmission + the built world, not the genes.
  CONTROL C — FIDELITY THRESHOLD (Lewis & Laland): accumulation needs high-fidelity transmission; below a
              critical fidelity, copy loss > innovation and the ratchet collapses to the asocial ceiling.
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
from alife.world3d import World3D

OUT = "runs/r149_culture"
os.makedirs(OUT, exist_ok=True)
NAIVE = np.array([0.10, 0.12, 0.32])     # dark indigo = culturally naive (low technique)
LEARNED = np.array([1.0, 0.93, 0.45])    # bright gold = high technique (accumulated culture)
HEARTH = np.array([1.0, 0.30, 0.55])     # magenta glow = the built cultural repository (hearths)
TECH_SCALE = 6.0                         # fixed tech->brightness scale so later frames are genuinely brighter


def cfg(**kw):
    # the viable niche regime (R148) + culture on: a denser 100^3 world so the self-built hearth economy
    # sustains a settled population, with CONVEX ripening reach so concentrated building pays.
    return replace(GenesisConfig(world=World3D(size=100.0), n0=900), processing=True, building=True,
                   culture=True, hearth_reach_per_strength=3.0, hearth_radius=12.0, **kw)


def agent_color(w):
    """Dark=naive, bright=high technique — makes 'the population accumulates culture' legible as brightening."""
    act = w.pop.active()
    if act.size == 0:
        return np.zeros((0, 3))
    t = np.clip(w.pop.tech[act] / TECH_SCALE, 0.0, 1.0)[:, None]
    return NAIVE * (1.0 - t) + LEARNED * t


def headline(steps, seed=0, render_every=150):
    from alife.render3d import Renderer3D
    c = cfg()
    w = GenesisWorld(c, seed=seed, evolve=True)
    keys = ("step", "population", "n_hearths")
    hist = {k: [] for k in keys}
    tmean, tmax, htmax, mgen = [], [], [], []
    frames = []
    r = Renderer3D(c.world, width=720, height=540)
    t0 = time.time()
    for s in range(steps):
        w.step()
        if s % 50 == 0:
            snp = w.snapshot()
            for k in keys:
                hist[k].append(snp[k])
            ct = w.culture_test()
            tmean.append(ct.get("tech_mean", 0.0)); tmax.append(ct.get("tech_max", 0.0))
            htmax.append(ct.get("hearth_tech_max", 0.0)); mgen.append(ct.get("mean_gen", 0.0))
        if s % render_every == 0:
            act = w.pop.active()
            if act.size:
                hp, _ = w.hearth_arrays()
                frames.append(r.render(w.pop.pos[act], w.pop.vel[act], agent_color(w),
                                       cam_angle=s * 0.012, cam_elev=0.42, food=hp))
    r.ctx.release()
    w.save_checkpoint(os.path.join(OUT, "checkpoint.npz"))
    if frames:
        imageio.mimsave(os.path.join(OUT, "culture.gif"), frames, fps=10, loop=0)
    print(f"headline: {steps} steps {time.time()-t0:.1f}s pop {hist['population'][-1]:.0f} "
          f"mean_gen {mgen[-1]:.1f} tech_mean {tmean[-1]:.2f} tech_max {tmax[-1]:.2f} "
          f"hearth_tech_max {htmax[-1]:.2f}", flush=True)
    hist.update(tmean=tmean, tmax=tmax, htmax=htmax, mgen=mgen)
    return hist


def trace(steps, seed, learn=True, evolve=True, fidelity=0.97, every=100):
    """Run a control and return the per-step traces of the culture read-out + final living technique."""
    w = GenesisWorld(cfg(learn=learn, culture_fidelity=fidelity), seed=seed, evolve=evolve)
    st, htmax, tmean, tmax, gen, pop = [], [], [], [], [], []
    for s in range(steps):
        w.step()
        if s % every == 0:
            ct = w.culture_test()
            st.append(s); htmax.append(ct.get("hearth_tech_max", 0.0)); tmean.append(ct.get("tech_mean", 0.0))
            tmax.append(ct.get("tech_max", 0.0)); gen.append(ct.get("mean_gen", 0.0))
            pop.append(w.snapshot()["population"])
    return dict(st=st, htmax=htmax, tmean=tmean, tmax=tmax, gen=gen, pop=pop,
                final_tmax=tmax[-1], final_htmax=htmax[-1], final_tmean=tmean[-1], final_gen=gen[-1])


def mean_trace(runs, key):
    n = min(len(r[key]) for r in runs)
    return np.mean([r[key][:n] for r in runs], axis=0), runs[0]["st"][:n]


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 2500
    cs = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
    seeds = (0, 1, 2)
    print(f"=== headline culture run ({steps} steps, technique-coloured 3D) ===", flush=True)
    h = headline(steps)

    print(f"=== CONTROL A: cumulative (learn) vs asocial (no-learn), {len(seeds)} seeds, {cs} steps ===", flush=True)
    cum = [trace(cs, s, learn=True) for s in seeds]
    aso = [trace(cs, s, learn=False) for s in seeds]
    cum_tm = np.mean([r["final_tmean"] for r in cum]); aso_tm = np.mean([r["final_tmean"] for r in aso])
    cum_tmax = np.mean([r["final_tmax"] for r in cum]); aso_tmax = np.mean([r["final_tmax"] for r in aso])
    cum_ht = np.mean([r["final_htmax"] for r in cum]); aso_ht = np.mean([r["final_htmax"] for r in aso])
    for s, rc, ra in zip(seeds, cum, aso):
        print(f"  seed {s}: CUMULATIVE tech_mean {rc['final_tmean']:.2f} (max {rc['final_tmax']:.2f}) "
              f"gen {rc['final_gen']:.1f} | ASOCIAL tech_mean {ra['final_tmean']:.2f} (max {ra['final_tmax']:.2f})",
              flush=True)
    print(f"  MEAN tech_mean (FALSIFIABLE — collapses w/o transmission): cumulative {cum_tm:.2f} vs asocial "
          f"{aso_tm:.2f}  ({cum_tm/max(aso_tm,1e-9):.1f}x)", flush=True)
    print(f"  MEAN tech_max (high-water record): cumulative {cum_tmax:.2f} vs asocial {aso_tmax:.2f}  "
          f"({cum_tmax/max(aso_tmax,1e-9):.1f}x)", flush=True)

    print(f"=== CONTROL B: cultural not genetic — evolve=False still climbs, {len(seeds)} seeds ===", flush=True)
    frz = [trace(cs, s, learn=True, evolve=False) for s in seeds]
    frz_tm = np.mean([r["final_tmean"] for r in frz])
    frz_tmax = np.mean([r["final_tmax"] for r in frz])
    print(f"  MEAN frozen-genome tech_mean {frz_tm:.2f} max {frz_tmax:.2f} (vs asocial tech_mean {aso_tm:.2f}: "
          f"culture climbs without genetic change)", flush=True)

    print(f"=== CONTROL C: fidelity threshold (Lewis-Laland), 2 seeds, {cs} steps ===", flush=True)
    fids = (0.99, 0.9, 0.7, 0.5)
    fid_ht = {}
    for fd in fids:
        runs = [trace(cs, s, learn=True, fidelity=fd) for s in (0, 1)]
        fid_ht[fd] = np.mean([r["final_htmax"] for r in runs])
        print(f"  fidelity {fd:.2f}: hearth_tech_max {fid_ht[fd]:.2f}", flush=True)

    cumulative = cum_tm > 3.0 * aso_tm and cum_ht > 1.5 * aso_ht            # falsifiable mean ratchets >> asocial
    not_genetic = frz_tm > 3.0 * aso_tm                                      # mean climbs with genes frozen
    threshold = fid_ht[0.99] > fid_ht[0.5] * 1.5                             # high fidelity ratchets, low doesn't
    verdict = cumulative and not_genetic and threshold
    print(f"  CHECKS: cumulative>asocial {cumulative} | cultural-not-genetic {not_genetic} | "
          f"fidelity-threshold {threshold}", flush=True)
    print(f"  VERDICT: {'CUMULATIVE CULTURE EMERGED' if verdict else 'NEGATIVE'}", flush=True)

    # ---- panel ----
    fig, ax = plt.subplots(2, 3, figsize=(16, 9))
    st = np.array(h["step"])
    ax[0, 0].plot(st, h["htmax"], color="#d62728", lw=2)
    ax[0, 0].set_title("THE RATCHET: hearth technique record (cultural memory) climbing"); ax[0, 0].set_xlabel("step")
    cm, cst = mean_trace(cum, "htmax"); am, _ = mean_trace(aso, "htmax")
    ax[0, 1].plot(cst, cm, color="#2ca02c", lw=2, label="cumulative (learn)")
    ax[0, 1].plot(cst, am, color="#999999", lw=2, label="asocial (no learn)")
    ax[0, 1].set_title("cultural record: cumulative vs asocial"); ax[0, 1].legend(); ax[0, 1].set_xlabel("step")
    cgm, _ = mean_trace(cum, "gen"); ctm, _ = mean_trace(cum, "tmax")
    ax[0, 2].plot(cgm, ctm, color="#1f77b4", lw=2)
    ax[0, 2].set_title("technique vs generation depth (ratchet across generations)")
    ax[0, 2].set_xlabel("mean generation"); ax[0, 2].set_ylabel("tech_max")
    ax[1, 0].bar(["cumulative", "asocial", "frozen\ngenome"], [cum_tm, aso_tm, frz_tm],
                 color=["#2ca02c", "#999999", "#1f77b4"])
    ax[1, 0].set_title(f"final tech_MEAN (falsifiable): cumulative {cum_tm:.1f} vs asocial {aso_tm:.1f} "
                       f"({cum_tm/max(aso_tm,1e-9):.0f}x)")
    ax[1, 1].plot(list(fids), [fid_ht[f] for f in fids], "o-", color="#9467bd", lw=2)
    ax[1, 1].axhline(aso_ht, ls=":", color="#999999", label="asocial ceiling")
    ax[1, 1].set_title("fidelity threshold: accumulation needs high-fidelity copying (bounded ceiling)")
    ax[1, 1].set_xlabel("transmission fidelity"); ax[1, 1].set_ylabel("hearth_tech_max"); ax[1, 1].legend()
    fm, fst = mean_trace(frz, "tmean")
    cmt, _ = mean_trace(cum, "tmean"); amt, _ = mean_trace(aso, "tmean")
    ax[1, 2].plot(fst, fm, color="#1f77b4", lw=2, label="frozen genome (learn)")
    ax[1, 2].plot(cst, cmt, color="#2ca02c", lw=2, label="cumulative (evolve)")
    ax[1, 2].plot(cst, amt, color="#999999", lw=2, label="asocial")
    ax[1, 2].set_title("cultural NOT genetic: technique climbs even with frozen genes")
    ax[1, 2].legend(); ax[1, 2].set_xlabel("step")
    vtxt = "CUMULATIVE CULTURE EMERGED" if verdict else "HONEST NEGATIVE"
    fig.suptitle(f"GENESIS R149 — cumulative culture: a learned technique ratchets across generations through "
                 f"the built world.  {vtxt}\n(dark=naive, bright=high technique in culture.gif; the population "
                 f"brightens as culture accumulates)", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=100)
    print(f"wrote {OUT}/culture.gif and {OUT}/panel.png", flush=True)


if __name__ == "__main__":
    main()
