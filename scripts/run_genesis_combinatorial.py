"""R150 — GENESIS open-ended COMBINATORIAL culture. R149 proved cumulative culture, but its scalar `tech`
innovates at a FIXED rate, giving a linear recurrence with a fixed point ~innov/(1-fidelity): the ratchet
DECELERATES and saturates — cumulative, not open-ended. R150 replaces the scalar with a discrete REPERTOIRE
on a fixed tech TREE: a technique is DISCOVERABLE only once both its prerequisite techniques are known
(Kauffman's adjacent possible / Arthur's combinatorial evolution). Because the set of discoverable techniques
GROWS as the repertoire grows, discovery ACCELERATES — ideas beget ideas — and cultural complexity climbs
super-linearly with no dynamical fixed point.

FALSIFIABLE open-ended signatures (in situ; never feed selection):
  (1) pop_distinct (techniques known by the living population) climbs SUPER-LINEARLY — its per-window
      growth RATE RISES — and stays far below the tech-tree cap (not saturation).
  (2) the frontier (deepest tech-tree LEVEL reached) keeps deepening across generations.
Controls:
  ASOCIAL (learn=False)          — no transmission; each agent explores from empty in one lifetime. The
                                   acid test: cumulative culture is impossible alone -> the climb vanishes.
  R149 SCALAR (combinatorial=False) — the fixed-rate ratchet; its technique level DECELERATES toward a finite
                                   fixed point. Plotted to show R150 lifts that ceiling (rate rises, not falls).
NO INTRINSIC CEILING: the combinatorial frontier's only bound is the deliberate tree-depth cap, a TUNABLE
design parameter (max tree depth grows with max_techniques) — not a dynamical attractor like R149's fixed
point. One sim at a time; GL context released after the render.
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

from alife.genesis import combinatorial as cb
from alife.genesis.genesis import GenesisConfig, GenesisWorld
from alife.world3d import World3D

OUT = "runs/r150_combinatorial"
os.makedirs(OUT, exist_ok=True)
NAIVE = np.array([0.10, 0.12, 0.32])     # dark indigo = shallow repertoire (low frontier)
DEEP = np.array([0.30, 1.0, 0.55])       # bright green = deep combinatorial frontier
LEVEL_SCALE = 14.0


def cfg(**kw):
    # the R148/R149 viable building+culture regime + a large tech tree so the run never approaches the cap.
    base = dict(processing=True, building=True, culture=True, combinatorial=True, max_techniques=8000,
                n_seed_tech=8, innov_steps=1, hearth_reach_per_strength=3.0, hearth_radius=12.0)
    base.update(kw)                                          # caller overrides (e.g. combinatorial=False)
    return replace(GenesisConfig(world=World3D(size=100.0), n0=900), **base)


def agent_color(w):
    act = w.pop.active()
    if act.size == 0:
        return np.zeros((0, 3))
    t = np.clip(w.pop.tech[act] / LEVEL_SCALE, 0.0, 1.0)[:, None]
    return NAIVE * (1.0 - t) + DEEP * t


def headline(steps, seed=0, render_every=150):
    from alife.render3d import Renderer3D
    c = cfg()
    w = GenesisWorld(c, seed=seed, evolve=True)
    st, popd, hd, mlvl, mgen, pop = [], [], [], [], [], []
    frames = []
    r = Renderer3D(c.world, width=720, height=540)
    t0 = time.time()
    for s in range(steps):
        w.step()
        if s % 50 == 0:
            ct = w.combinatorial_test()
            st.append(s); popd.append(ct.get("pop_distinct", 0)); hd.append(ct.get("hearth_distinct", 0))
            mlvl.append(ct.get("max_level", 0)); mgen.append(ct.get("mean_gen", 0.0))
            pop.append(w.snapshot()["population"])
        if s % render_every == 0:
            act = w.pop.active()
            if act.size:
                hp, _ = w.hearth_arrays()
                frames.append(r.render(w.pop.pos[act], w.pop.vel[act], agent_color(w),
                                       cam_angle=s * 0.012, cam_elev=0.42, food=hp))
    r.ctx.release()
    if frames:
        imageio.mimsave(os.path.join(OUT, "combinatorial.gif"), frames, fps=10, loop=0)
    print(f"headline: {steps} steps {time.time()-t0:.1f}s pop {pop[-1]:.0f} gen {mgen[-1]:.1f} "
          f"pop_distinct {popd[-1]} hearth_distinct {hd[-1]} max_level {mlvl[-1]}", flush=True)
    return dict(st=st, popd=popd, hd=hd, mlvl=mlvl, mgen=mgen, pop=pop)


def trace_combo(steps, seed, learn=True, every=100):
    w = GenesisWorld(cfg(learn=learn), seed=seed, evolve=True)
    st, popd, mlvl, gen = [], [], [], []
    for s in range(steps):
        w.step()
        if s % every == 0:
            ct = w.combinatorial_test()
            st.append(s); popd.append(ct.get("pop_distinct", 0)); mlvl.append(ct.get("max_level", 0))
            gen.append(ct.get("mean_gen", 0.0))
    return dict(st=st, popd=popd, mlvl=mlvl, gen=gen, final_popd=popd[-1], final_mlvl=mlvl[-1])


def trace_scalar(steps, seed, every=100):
    """The R149 scalar ratchet (combinatorial=False) — the saturating reference."""
    w = GenesisWorld(cfg(combinatorial=False), seed=seed, evolve=True)
    st, tmax, tmean = [], [], []
    for s in range(steps):
        w.step()
        if s % every == 0:
            ct = w.culture_test()
            st.append(s); tmax.append(ct.get("tech_max", 0.0)); tmean.append(ct.get("tech_mean", 0.0))
    return dict(st=st, tmax=tmax, tmean=tmean)


def mean_trace(runs, key):
    n = min(len(r[key]) for r in runs)
    return np.mean([r[key][:n] for r in runs], axis=0), runs[0]["st"][:n]


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 1300
    cs = int(sys.argv[2]) if len(sys.argv) > 2 else 1200
    seeds = (0, 1)
    print(f"=== headline combinatorial run ({steps} steps, level-coloured 3D) ===", flush=True)
    h = headline(steps)

    print(f"=== controls: combinatorial-social vs asocial vs R149-scalar, {len(seeds)} seeds, {cs} steps ===",
          flush=True)
    cmb = [trace_combo(cs, s, learn=True) for s in seeds]
    aso = [trace_combo(cs, s, learn=False) for s in seeds]
    scl = [trace_scalar(cs, s) for s in seeds]
    cmb_pd = np.mean([r["final_popd"] for r in cmb]); aso_pd = np.mean([r["final_popd"] for r in aso])
    cmb_ml = np.mean([r["final_mlvl"] for r in cmb]); aso_ml = np.mean([r["final_mlvl"] for r in aso])
    cmb_curve, cst = mean_trace(cmb, "popd"); aso_curve, _ = mean_trace(aso, "popd")
    scl_curve, sst = mean_trace(scl, "tmax")
    for s, rc, ra in zip(seeds, cmb, aso):
        print(f"  seed {s}: COMBINATORIAL pop_distinct {rc['final_popd']} (frontier lvl {rc['final_mlvl']}) | "
              f"ASOCIAL pop_distinct {ra['final_popd']} (lvl {ra['final_mlvl']})", flush=True)
    # growth-rate slope: does the discovery RATE rise (open-ended) or fall (saturating)?
    cdiff = np.diff(cmb_curve)
    rate_first, rate_last = float(cdiff[:len(cdiff)//2].mean()), float(cdiff[len(cdiff)//2:].mean())
    sdiff = np.diff(scl_curve)
    s_first, s_last = float(sdiff[:len(sdiff)//2].mean()), float(sdiff[len(sdiff)//2:].mean())
    print(f"  MEAN final pop_distinct: combinatorial {cmb_pd:.0f} vs asocial {aso_pd:.0f}  "
          f"({cmb_pd/max(aso_pd,1):.0f}x); cap = {cfg().max_techniques} (run stays far below = not saturation)",
          flush=True)
    print(f"  MEAN frontier level: combinatorial {cmb_ml:.1f} vs asocial {aso_ml:.1f}", flush=True)
    print(f"  COMBINATORIAL discovery RATE (distinct/window): early {rate_first:.0f} -> late {rate_last:.0f} "
          f"({'RISES = open-ended' if rate_last > rate_first else 'falls'})", flush=True)
    print(f"  R149 SCALAR technique RATE: early {s_first:.2f} -> late {s_last:.2f} "
          f"({'falls = saturating fixed point' if s_last < s_first else 'rises'})", flush=True)

    # tree-depth vs cap: the ceiling is a TUNABLE design parameter, not a dynamical fixed point
    caps = (2000, 4000, 8000, 16000)
    depths = [int(cb.build_tech_tree(K, 8)[2].max()) for K in caps]
    print(f"  TREE DEPTH vs max_techniques cap: {dict(zip(caps, depths))}  (ceiling tunable, not intrinsic)",
          flush=True)

    accelerates = rate_last > rate_first                      # discovery rate RISES = open-ended signature
    needs_transmission = cmb_pd > 5 * aso_pd and cmb_ml > aso_ml + 3   # asocial cannot climb
    scalar_saturates = s_last < s_first                       # R149 fixed-rate ratchet decelerates
    far_from_cap = cmb_pd < 0.3 * cfg().max_techniques        # not just filling the finite pool
    verdict = accelerates and needs_transmission and scalar_saturates and far_from_cap
    print(f"  CHECKS: accelerating {accelerates} | needs-transmission {needs_transmission} | "
          f"scalar-saturates {scalar_saturates} | far-from-cap {far_from_cap}", flush=True)
    print(f"  VERDICT: {'OPEN-ENDED COMBINATORIAL CULTURE' if verdict else 'NEGATIVE'}", flush=True)

    # ---- panel ----
    fig, ax = plt.subplots(2, 3, figsize=(16, 9))
    hst = np.array(h["st"])
    ax[0, 0].plot(hst, h["popd"], color="#2ca02c", lw=2, label="living population")
    ax[0, 0].plot(hst, h["hd"], color="#d62728", lw=2, label="hearth records (built store)")
    ax[0, 0].set_title("OPEN-ENDED METRIC: distinct techniques (climbs, far below cap)")
    ax[0, 0].set_xlabel("step"); ax[0, 0].legend()
    ax[0, 1].plot(cst, cmb_curve, color="#2ca02c", lw=2, label="combinatorial (social)")
    ax[0, 1].plot(cst, aso_curve, color="#999999", lw=2, label="asocial (no learning)")
    ax[0, 1].set_title(f"pop_distinct: social climb {cmb_pd:.0f} vs asocial floor {aso_pd:.0f}")
    ax[0, 1].set_xlabel("step"); ax[0, 1].legend()
    ax[0, 2].plot(cst[1:], cdiff, color="#2ca02c", lw=2)
    ax[0, 2].set_title(f"discovery RATE rises: {rate_first:.0f}->{rate_last:.0f}/window (ideas beget ideas)")
    ax[0, 2].set_xlabel("step"); ax[0, 2].set_ylabel("Δ distinct / window")
    cmb_lvl, _ = mean_trace(cmb, "mlvl"); aso_lvl, _ = mean_trace(aso, "mlvl")
    cgen, _ = mean_trace(cmb, "gen")
    ax[1, 0].plot(cgen, cmb_lvl, color="#1f77b4", lw=2, label="combinatorial")
    ax[1, 0].plot(mean_trace(aso, "gen")[0], aso_lvl, color="#999999", lw=2, label="asocial")
    ax[1, 0].set_title("FRONTIER deepens across generations (structured dependency depth)")
    ax[1, 0].set_xlabel("mean generation"); ax[1, 0].set_ylabel("max tech-tree level"); ax[1, 0].legend()
    ax[1, 1].plot(sst, scl_curve, color="#ff7f0e", lw=2, label="R149 scalar tech_max")
    ax[1, 1].plot(sst, mean_trace(scl, "tmean")[0], color="#ffbb78", lw=2, label="R149 scalar tech_mean")
    ax[1, 1].set_title(f"R149 fixed-rate ratchet SATURATES (rate {s_first:.2f}->{s_last:.2f}): the ceiling R150 lifts")
    ax[1, 1].set_xlabel("step"); ax[1, 1].legend()
    ax[1, 2].plot(caps, depths, "o-", color="#9467bd", lw=2)
    ax[1, 2].set_title("ceiling is TUNABLE: max tree depth grows with the cap\n(no dynamical fixed point, unlike R149)")
    ax[1, 2].set_xlabel("max_techniques cap"); ax[1, 2].set_ylabel("max tech-tree depth")
    vtxt = "OPEN-ENDED COMBINATORIAL CULTURE" if verdict else "HONEST NEGATIVE"
    fig.suptitle(f"GENESIS R150 — open-ended combinatorial culture: prerequisite-gated discovery (adjacent "
                 f"possible) lifts R149's finite ceiling.  {vtxt}\n(dark=shallow, bright green=deep frontier in "
                 f"combinatorial.gif; the population brightens as the tech tree is climbed)", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=100)
    print(f"wrote {OUT}/combinatorial.gif and {OUT}/panel.png", flush=True)


if __name__ == "__main__":
    main()
