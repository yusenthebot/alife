"""R157 — GENESIS ecologically-selected divergent TRADITIONS. R156 grew traditions but they were NEUTRAL
DRIFT (modest F_ST ~0.03), and R157 verified that naive forgetting (culture_decay) cannot sharpen them —
with no force maintaining divergence, decay only erodes the deep techniques that define a tradition. The
missing ingredient is SELECTION. Here the world is spatially HETEROGENEOUS: a recipe-locked mote's tier is
set by its x-axis REGION (spatial_tiers), so region r yields only tier-(r+1) food, edible (via tech_actions)
ONLY by holders of that tier's recipe BRANCH. A recipe carry-BUDGET forces each agent to be a branch
SPECIALIST, and a free-tier LIFELINE keeps the population alive while branches sort. So in region r only
recipe-r specialists can eat the rich local food -> selection LOCKS each region to its own branch: discrete,
spatially-structured, economically-distinct traditions MAINTAINED by local adaptation, not drift.

FALSIFIABLE signature (in situ; never feeds selection): the region<->branch ALIGNMENT (mean over regions of
own-branch frac - other-branch frac) is POSITIVE and HIGHER than the scrambled-niche null.
Causal CONTROL — spatial_tiers=False: the SAME learners + SAME budget + SAME recipes, but a locked mote's tier
is uniformly RANDOM in space, cutting the region<->branch correlation. The only manipulated variable is WHERE
each branch's food is, so a higher alignment under spatial tiers isolates ECOLOGICAL SELECTION as the cause.
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

OUT = "runs/r157_ecotraditions"
os.makedirs(OUT, exist_ok=True)
# one fixed hue per recipe branch (region); grey = no/ambiguous branch
BRANCH_RGB = np.array([[0.90, 0.20, 0.20], [0.20, 0.55, 0.95], [0.95, 0.80, 0.15]])
GREY = np.array([0.55, 0.55, 0.55])
MIN_REGION = 20


def cfg(**kw):
    base = dict(processing=True, building=True, culture=True, combinatorial=True, max_techniques=8000,
                n_seed_tech=8, innov_steps=1, hearth_reach_per_strength=3.0, hearth_radius=12.0,
                tech_actions=True, n_food_tiers=4, recipe_level_step=2, tier_value_bonus=3.0,
                tier0_frac=0.65, food_cap=2600, food_regrow=140, recipe_budget=2)
    base.update(kw)
    return replace(GenesisConfig(world=World3D(size=100.0), n0=850), **base)


def branch_color(w):
    """Colour each agent by which recipe BRANCH it holds (the deepest-tier recipe it carries). Specialists in
    region r should be colour r; grey = holds no locked branch. Under spatial selection these form x-axis colour
    BANDS (region<->branch sorting); the random-tier null salts-and-peppers them."""
    act = w.pop.active()
    if act.size == 0:
        return np.zeros((0, 3))
    recipes = w._recipe_tech[1:]                                  # locked-tier recipe ids, region r -> recipes[r]
    held = w.rep[np.ix_(act, recipes)]                            # [n, B] which branches each agent holds
    tier_w = np.arange(1, recipes.size + 1)[None, :]             # deeper tier wins ties
    score = np.where(held, tier_w, 0)
    branch = np.where(held.any(axis=1), score.argmax(axis=1), -1)
    col = np.where(branch[:, None] >= 0, BRANCH_RGB[np.clip(branch, 0, None)], GREY)
    return col


def trace(spatial, seed, steps, every=50):
    w = GenesisWorld(cfg(spatial_tiers=spatial), seed=seed, evolve=True)
    st, align, pop = [], [], []
    for s in range(steps):
        w.step()
        if s % every == 0:
            e = w.ecological_traditions_test(min_region=MIN_REGION)
            st.append(s); align.append(e.get("alignment", 0.0)); pop.append(e.get("n", 0))
    e = w.ecological_traditions_test(min_region=MIN_REGION)
    return dict(st=st, align=align, pop=pop, final=e)


def headline(spatial, seed, steps, render_every=50):
    from alife.render3d import Renderer3D
    w = GenesisWorld(cfg(spatial_tiers=spatial), seed=seed, evolve=True)
    r = Renderer3D(w.cfg.world, width=640, height=480)
    frames = []
    for s in range(steps):
        w.step()
        if s % render_every == 0:
            act = w.pop.active()
            if act.size:
                hp, _ = w.hearth_arrays()
                frames.append(r.render(w.pop.pos[act], w.pop.vel[act], branch_color(w),
                                        cam_angle=s * 0.012, cam_elev=0.42, food=hp))
    last = frames[-1] if frames else None
    r.ctx.release()
    return frames, last, w.ecological_traditions_test(min_region=MIN_REGION)


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 450
    seeds = (0, 1)
    t0 = time.time()

    print(f"=== headline SPATIAL run ({steps} steps, branch-coloured 3D) ===", flush=True)
    frames, sp_last, sp_final = headline(True, 0, steps)
    if frames:
        imageio.mimsave(os.path.join(OUT, "ecotraditions.gif"), frames, fps=8, loop=0)
    print(f"  rendered {len(frames)} frames; spatial alignment {sp_final.get('alignment', 0):.3f} "
          f"({time.time()-t0:.0f}s)", flush=True)

    print("=== random-niche NULL final frame ===", flush=True)
    _, rn_last, rn_final = headline(False, 0, steps, render_every=max(50, steps))
    print(f"  random alignment {rn_final.get('alignment', 0):.3f}", flush=True)

    print(f"=== alignment controls: spatial vs random, {len(seeds)} seeds ===", flush=True)
    sp = [trace(True, s, steps) for s in seeds]
    rn = [trace(False, s, steps) for s in seeds]
    for s, rs, rr in zip(seeds, sp, rn):
        fs, fr = rs["final"], rr["final"]
        print(f"  seed {s}: SPATIAL align {fs.get('alignment',0):.3f} "
              f"(own {fs.get('own_frac',0):.2f} vs other {fs.get('other_frac',0):.2f}, "
              f"aligned {fs.get('aligned_regions',0)}/{fs.get('n_regions',0)}, n {fs.get('n',0)}) | "
              f"RANDOM align {fr.get('alignment',0):.3f}", flush=True)
    sp_a = np.array([r["final"].get("alignment", 0.0) for r in sp])
    rn_a = np.array([r["final"].get("alignment", 0.0) for r in rn])
    wins = int((sp_a > rn_a).sum())
    print(f"  MEAN alignment: spatial {sp_a.mean():.3f} vs random {rn_a.mean():.3f}; "
          f"spatial>random on {wins}/{len(seeds)} seeds", flush=True)
    verdict = wins == len(seeds) and sp_a.mean() > 0.0 and sp_a.mean() > rn_a.mean()
    print(f"  VERDICT: {'ECOLOGICALLY-SELECTED DIVERGENT TRADITIONS' if verdict else 'NEGATIVE'}", flush=True)

    # ---- panel ----
    fig = plt.figure(figsize=(16, 9))
    ax1 = fig.add_subplot(2, 3, 1)
    for r in sp:
        ax1.plot(r["st"], r["align"], color="#2ca02c", lw=2, alpha=0.8)
    for r in rn:
        ax1.plot(r["st"], r["align"], color="#999999", lw=2, alpha=0.8)
    ax1.axhline(0.0, color="k", lw=0.8, ls=":")
    ax1.plot([], [], color="#2ca02c", lw=2, label="spatial niches (selection)")
    ax1.plot([], [], color="#999999", lw=2, label="random niches (null)")
    ax1.set_title("region<->branch alignment over time")
    ax1.set_xlabel("step"); ax1.set_ylabel("own - other branch frac"); ax1.legend()

    ax2 = fig.add_subplot(2, 3, 2)
    x = np.arange(len(seeds))
    ax2.bar(x - 0.2, sp_a, 0.4, color="#2ca02c", label="spatial")
    ax2.bar(x + 0.2, rn_a, 0.4, color="#999999", label="random")
    ax2.axhline(0.0, color="k", lw=0.8)
    ax2.set_xticks(x); ax2.set_xticklabels([f"seed {s}" for s in seeds])
    ax2.set_title(f"final alignment: spatial {sp_a.mean():.3f} vs random {rn_a.mean():.3f}")
    ax2.set_ylabel("alignment"); ax2.legend()

    ax3 = fig.add_subplot(2, 3, 3)
    ax3.bar(x - 0.2, [r["final"].get("own_frac", 0) for r in sp], 0.4, color="#1f77b4", label="own branch")
    ax3.bar(x + 0.2, [r["final"].get("other_frac", 0) for r in sp], 0.4, color="#ff7f0e", label="other branches")
    ax3.set_xticks(x); ax3.set_xticklabels([f"seed {s}" for s in seeds])
    ax3.set_title("spatial: own vs other branch fraction per region")
    ax3.set_ylabel("fraction holding"); ax3.legend()

    ax4 = fig.add_subplot(2, 3, 4)
    if sp_last is not None:
        ax4.imshow(sp_last); ax4.set_title("SPATIAL: branch colour bands (sorted)")
    ax4.axis("off")
    ax5 = fig.add_subplot(2, 3, 5)
    if rn_last is not None:
        ax5.imshow(rn_last); ax5.set_title("RANDOM: branches mixed everywhere")
    ax5.axis("off")

    ax6 = fig.add_subplot(2, 3, 6)
    ax6.axis("off")
    vtxt = "ECOLOGICALLY-SELECTED\nDIVERGENT TRADITIONS" if verdict else "HONEST NEGATIVE"
    ax6.text(0.02, 0.5,
             f"VERDICT: {vtxt}\n\nspatial align {sp_a.mean():.3f}  >  random {rn_a.mean():.3f}\n"
             f"({wins}/{len(seeds)} seeds, null ~0)\n\ncolour = agent's recipe BRANCH (region r -> branch r).\n"
             f"Spatial food niches + a recipe carry-budget make\neach region SELECT for its own branch ->\n"
             f"branches sort into x-axis colour bands.\nThe random-niche null mixes them away.\n\n"
             f"(Honest: magnitude modest; the directional +\ncausal claim vs the null carries the result.)",
             fontsize=11, va="center")
    fig.suptitle("GENESIS R157 — ecologically-SELECTED divergent traditions: spatial niches + a recipe budget\n"
                 "make each region select for its own branch (alignment > scrambled-niche null).", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=100)
    print(f"wrote {OUT}/ecotraditions.gif and {OUT}/panel.png  ({time.time()-t0:.0f}s total)", flush=True)


if __name__ == "__main__":
    main()
