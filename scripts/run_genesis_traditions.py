"""R156 — GENESIS emergent divergent cultural TRADITIONS. R150-R155 measured ONE global frontier of the
open-ended combinatorial tree, but a real civilization is not a single monoculture of knowledge — it is
MANY divergent cultural traditions. R156 asks whether the EXISTING substrate already grows them: oblique
transmission copies the NEAREST strong hearth (a spatial cultural store), so a region that climbs one
BRANCH of the adjacent possible reinforces it locally (founder effect + path dependence) while another
region climbs another -> spatially structured traditions.

FALSIFIABLE signature (in situ; never feeds selection): Wright's F_ST over the boolean technique
repertoire across a grid of spatial demes is POSITIVE and HIGHER than the panmictic null.
Causal CONTROL — panmictic_culture: keep the SAME learners (identical nearest-hearth in-range gate) but
copy a UNIFORMLY RANDOM strong hearth instead of the nearest one. The ONLY manipulated variable is WHICH
hearth you copy, so a higher F_ST under local transmission isolates SPATIAL structure as the cause.
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

OUT = "runs/r156_traditions"
os.makedirs(OUT, exist_ok=True)
HSV = plt.get_cmap("hsv")
GRID = 3
MIN_DEME = 20


def cfg(**kw):
    base = dict(processing=True, building=True, culture=True, combinatorial=True, max_techniques=8000,
                n_seed_tech=8, innov_steps=1, hearth_reach_per_strength=3.0, hearth_radius=12.0)
    base.update(kw)
    return replace(GenesisConfig(world=World3D(size=100.0), n0=850), **base)


def agent_color(w):
    """Colour each agent by a hue hashed from its DEEPEST-known technique id: agents sharing a deep
    technique (a tradition) share a colour. Under local transmission these form spatial colour patches;
    panmictic mixing salts-and-peppers them."""
    act = w.pop.active()
    if act.size == 0:
        return np.zeros((0, 3))
    rep = w.rep[act]
    deepest = np.where(rep, w._tree_level[None, :], -1).argmax(axis=1).astype(float)
    h = (deepest * 0.61803398875) % 1.0                      # golden-ratio hash -> well-spread hues
    return HSV(h)[:, :3]


def trace(panmictic, seed, steps, every=50):
    w = GenesisWorld(cfg(panmictic_culture=panmictic), seed=seed, evolve=True)
    st, fst, distinct, pop = [], [], [], []
    for s in range(steps):
        w.step()
        if s % every == 0:
            t = w.tradition_test(grid=GRID, min_deme=MIN_DEME)
            st.append(s); fst.append(t.get("fst", 0.0))
            distinct.append(t.get("n_distinct_traditions", 0)); pop.append(t.get("n", 0))
    t = w.tradition_test(grid=GRID, min_deme=MIN_DEME)
    return dict(st=st, fst=fst, distinct=distinct, pop=pop, final=t)


def headline(panmictic, seed, steps, render_every=50):
    from alife.render3d import Renderer3D
    w = GenesisWorld(cfg(panmictic_culture=panmictic), seed=seed, evolve=True)
    r = Renderer3D(w.cfg.world, width=640, height=480)
    frames, st, fst = [], [], []
    for s in range(steps):
        w.step()
        if s % 50 == 0:
            t = w.tradition_test(grid=GRID, min_deme=MIN_DEME)
            st.append(s); fst.append(t.get("fst", 0.0))
        if s % render_every == 0:
            act = w.pop.active()
            if act.size:
                hp, _ = w.hearth_arrays()
                frames.append(r.render(w.pop.pos[act], w.pop.vel[act], agent_color(w),
                                       cam_angle=s * 0.012, cam_elev=0.42, food=hp))
    last = frames[-1] if frames else None
    r.ctx.release()
    return frames, last, dict(st=st, fst=fst, final=w.tradition_test(grid=GRID, min_deme=MIN_DEME))


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    seeds = (0, 1)
    t0 = time.time()

    print(f"=== headline LOCAL run ({steps} steps, tradition-coloured 3D) ===", flush=True)
    frames, loc_last, _ = headline(False, 0, steps)
    if frames:
        imageio.mimsave(os.path.join(OUT, "traditions.gif"), frames, fps=8, loop=0)
    print(f"  rendered {len(frames)} frames ({time.time()-t0:.0f}s)", flush=True)

    print("=== panmictic NULL final frame ===", flush=True)
    _, pan_last, _ = headline(True, 0, steps, render_every=max(50, steps))  # only need the last frame

    print(f"=== F_ST controls: local vs panmictic, {len(seeds)} seeds ===", flush=True)
    loc = [trace(False, s, steps) for s in seeds]
    pan = [trace(True, s, steps) for s in seeds]
    for s, rl, rp in zip(seeds, loc, pan):
        fl, fp = rl["final"], rp["final"]
        print(f"  seed {s}: LOCAL F_ST {fl['fst']:.4f} distinct {fl['n_distinct_traditions']} "
              f"(demes {fl['n_demes']}, n {fl.get('n',0)}) | PANMICTIC F_ST {fp['fst']:.4f} "
              f"distinct {fp['n_distinct_traditions']}", flush=True)
    loc_f = np.array([r["final"]["fst"] for r in loc]); pan_f = np.array([r["final"]["fst"] for r in pan])
    loc_d = np.array([r["final"]["n_distinct_traditions"] for r in loc])
    pan_d = np.array([r["final"]["n_distinct_traditions"] for r in pan])
    wins = int((loc_f > pan_f).sum())
    print(f"  MEAN final F_ST: local {loc_f.mean():.4f} vs panmictic {pan_f.mean():.4f}  "
          f"({loc_f.mean()/max(pan_f.mean(),1e-6):.1f}x); local>panmictic on {wins}/{len(seeds)} seeds",
          flush=True)
    print(f"  MEAN distinct traditions: local {loc_d.mean():.1f} vs panmictic {pan_d.mean():.1f}", flush=True)
    verdict = wins == len(seeds) and loc_f.mean() > pan_f.mean()
    print(f"  VERDICT: {'EMERGENT DIVERGENT CULTURAL TRADITIONS' if verdict else 'NEGATIVE'}", flush=True)

    # ---- panel ----
    fig = plt.figure(figsize=(16, 9))
    ax1 = fig.add_subplot(2, 3, 1)
    for r in loc:
        ax1.plot(r["st"], r["fst"], color="#2ca02c", lw=2, alpha=0.8)
    for r in pan:
        ax1.plot(r["st"], r["fst"], color="#999999", lw=2, alpha=0.8)
    ax1.plot([], [], color="#2ca02c", lw=2, label="local (nearest hearth)")
    ax1.plot([], [], color="#999999", lw=2, label="panmictic (random hearth)")
    ax1.set_title("cultural F_ST over time (local builds spatial structure)")
    ax1.set_xlabel("step"); ax1.set_ylabel("F_ST"); ax1.legend()

    ax2 = fig.add_subplot(2, 3, 2)
    x = np.arange(len(seeds))
    ax2.bar(x - 0.2, loc_f, 0.4, color="#2ca02c", label="local")
    ax2.bar(x + 0.2, pan_f, 0.4, color="#999999", label="panmictic")
    ax2.set_xticks(x); ax2.set_xticklabels([f"seed {s}" for s in seeds])
    ax2.set_title(f"final F_ST: local {loc_f.mean():.3f} vs panmictic {pan_f.mean():.3f}")
    ax2.set_ylabel("F_ST"); ax2.legend()

    ax3 = fig.add_subplot(2, 3, 3)
    ax3.bar(x - 0.2, loc_d, 0.4, color="#1f77b4", label="local")
    ax3.bar(x + 0.2, pan_d, 0.4, color="#999999", label="panmictic")
    ax3.set_xticks(x); ax3.set_xticklabels([f"seed {s}" for s in seeds])
    ax3.set_title("distinct deme-dominant traditions")
    ax3.set_ylabel("# distinct dominant techniques"); ax3.legend()

    ax4 = fig.add_subplot(2, 3, 4)
    if loc_last is not None:
        ax4.imshow(loc_last); ax4.set_title("LOCAL: spatial tradition patches")
    ax4.axis("off")
    ax5 = fig.add_subplot(2, 3, 5)
    if pan_last is not None:
        ax5.imshow(pan_last); ax5.set_title("PANMICTIC: traditions mixed away")
    ax5.axis("off")

    ax6 = fig.add_subplot(2, 3, 6)
    ax6.axis("off")
    vtxt = "EMERGENT DIVERGENT CULTURAL TRADITIONS" if verdict else "HONEST NEGATIVE"
    ax6.text(0.02, 0.5,
             f"VERDICT: {vtxt}\n\nlocal F_ST {loc_f.mean():.4f}  >  panmictic {pan_f.mean():.4f}\n"
             f"({wins}/{len(seeds)} seeds)\n\nlocal distinct traditions {loc_d.mean():.1f} "
             f"vs panmictic {pan_d.mean():.1f}\n\ncolour = agent's deepest-known technique\n"
             f"(a tradition); local transmission grows\nspatial colour patches, panmictic mixes them.",
             fontsize=12, va="center")
    fig.suptitle("GENESIS R156 — emergent divergent cultural TRADITIONS: local transmission over the "
                 "open-ended tree\ngrows spatially structured cultures (F_ST > panmictic null).", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=100)
    print(f"wrote {OUT}/traditions.gif and {OUT}/panel.png  ({time.time()-t0:.0f}s total)", flush=True)


if __name__ == "__main__":
    main()
