"""R163 — GENESIS TEMPORAL phylogeny / open-ended cumulative descent.

R160-R162 reconstructed a SPATIAL phylogeny (demes = taxa; the cladogram of traditions, validated against
the birth genealogy: vertical transmission recovers the true descent, horizontal does not). R163 turns to the
TEMPORAL axis — the time-ladder of cumulative descent. Over a long run we log the world step at which each
technique FIRST appears in the population (track_tech_history, a passive observer). The generative tech tree
(combinatorial / adjacent-possible) imposes a partial order: a technique cannot be discovered before BOTH its
prerequisites. So a genuine cumulative-descent history must (1) place every product AFTER its prereqs in time
(precedence) and (2) have first-appearance time track tree DEPTH (deep techniques appear late).

Two falsifiable claims, three arms (combinatorial-social / additive-null-social / asocial):
  OPEN-ENDEDNESS  : the population's complexity (frontier depth max_level + breadth pop_distinct) keeps
                    CLIMBING under combinatorial discovery, and stays FLAT at the floor without transmission
                    (asocial). The additive null (no prereq gate) is the contrast on the temporal structure.
  TEMPORAL LADDER : under combinatorial discovery the first-appearance order RECOVERS the tree — precedence
                    == 1.0 and level<->time Spearman is high (vs a label-permutation null); the ADDITIVE null
                    (uniform discovery) scrambles it: precedence < 1, level<->time correlation collapses.

One sim at a time; GL context released after the render. 禁止造假 — every number read from the live log.
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

OUT = "runs/r163_temporal"
os.makedirs(OUT, exist_ok=True)
N_PERM = 999
SNAP_EVERY = 25


def cfg(**kw):
    base = dict(processing=True, building=True, culture=True, combinatorial=True,
                max_techniques=1500, n_seed_tech=8, innov_steps=1, culture_fidelity=0.97,
                hearth_reach_per_strength=3.0, hearth_radius=12.0, track_tech_history=True)
    base.update(kw)
    return replace(GenesisConfig(world=World3D(size=100.0), n0=300), **base)


def depth_color(w):
    """Colour each living agent by its repertoire DEPTH (deepest technique level known) — dark = naive,
    bright gold = deep cumulative culture."""
    import matplotlib.cm as cm
    act = w.pop.active()
    if act.size == 0:
        return np.zeros((0, 3))
    tech = w.pop.tech[act]
    deepest = max(1.0, float(w._tree_level.max()))
    return cm.inferno(np.clip(tech / deepest, 0, 1))[:, :3]


def run(seed, steps, combo_prereqs, learn, render=False):
    w = GenesisWorld(cfg(combo_prereqs=combo_prereqs, learn=learn), seed=seed, evolve=True)
    traj = {"t": [], "max_level": [], "pop_distinct": []}
    r = frames = None
    if render:
        from alife.render3d import Renderer3D
        r = Renderer3D(w.cfg.world, width=640, height=480)
        frames = []
    for s in range(steps):
        w.step()
        if s % SNAP_EVERY == 0 or s == steps - 1:
            ct = w.combinatorial_test()
            if ct:
                traj["t"].append(s)
                traj["max_level"].append(ct["max_level"])
                traj["pop_distinct"].append(ct["pop_distinct"])
        if render and (s % 80 == 0 or s == steps - 1):
            act = w.pop.active()
            if act.size:
                hp, _ = w.hearth_arrays()
                frames.append(r.render(w.pop.pos[act], w.pop.vel[act], depth_color(w),
                                        cam_angle=s * 0.012, cam_elev=0.42, food=hp))
    last = None
    if render:
        last = frames[-1] if frames else None
        r.ctx.release()
        if frames:
            imageio.mimsave(os.path.join(OUT, "temporal.gif"), frames, fps=4, loop=0)
    tp = w.temporal_phylogeny_test(n_perm=N_PERM)
    return traj, tp, last, w


def scatter_data(w):
    """First-appearance time vs tree level for every appeared technique (the temporal-ladder cloud)."""
    first = w._tech_first_step
    ap = first >= 0
    return w._tree_level[ap].astype(float), first[ap].astype(float)


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    seeds = (0, 1)
    t0 = time.time()

    print(f"=== R163 temporal phylogeny ({steps} steps, 3 arms x {len(seeds)} seeds) ===", flush=True)
    # combinatorial-social (seed 0 also rendered), additive-null-social, asocial
    combo = [run(seeds[0], steps, True, True, render=True)] + \
            [run(s, steps, True, True) for s in seeds[1:]]
    addn = [run(s, steps, False, True) for s in seeds]
    aso = [run(s, steps, True, False) for s in seeds]
    last = combo[0][2]

    def mc(arm, key):
        return np.array([a[1].get(key, np.nan) for a in arm])

    c_corr, a_corr = mc(combo, "level_time_corr"), mc(addn, "level_time_corr")
    c_pre, a_pre = mc(combo, "precedence_frac"), mc(addn, "precedence_frac")
    c_p = mc(combo, "level_time_p")
    c_null = mc(combo, "level_time_null")
    c_ml, a_ml, s_ml = mc(combo, "max_level"), mc(addn, "max_level"), mc(aso, "max_level")
    c_pd, a_pd, s_pd = mc(combo, "pop_distinct"), mc(addn, "pop_distinct"), mc(aso, "pop_distinct")

    for i, s in enumerate(seeds):
        print(f"  seed {s}: COMBO corr {c_corr[i]:.3f} (p {c_p[i]:.3f}, null {c_null[i]:.3f}) "
              f"prec {c_pre[i]:.3f}  max_lvl {c_ml[i]:.0f} distinct {c_pd[i]:.0f} | "
              f"ADD corr {a_corr[i]:.3f} prec {a_pre[i]:.3f}  max_lvl {a_ml[i]:.0f} distinct {a_pd[i]:.0f} | "
              f"ASO max_lvl {s_ml[i]:.0f} distinct {s_pd[i]:.0f}", flush=True)
    combo_gt_add = int(np.sum(c_corr > a_corr))
    sig = int(np.sum(c_p <= 0.05))
    print(f"  COMBO level<->time corr mean {np.nanmean(c_corr):.3f} (sig {sig}/{len(seeds)}) > "
          f"ADD mean {np.nanmean(a_corr):.3f}  [COMBO>ADD {combo_gt_add}/{len(seeds)}]  "
          f"COMBO prec {np.nanmean(c_pre):.3f} vs ADD prec {np.nanmean(a_pre):.3f}  ({time.time()-t0:.0f}s)",
          flush=True)
    print(f"  OPEN-ENDEDNESS: max_level COMBO {np.nanmean(c_ml):.1f} | ADD {np.nanmean(a_ml):.1f} | "
          f"ASO {np.nanmean(s_ml):.1f}   distinct COMBO {np.nanmean(c_pd):.0f} | ADD {np.nanmean(a_pd):.0f} | "
          f"ASO {np.nanmean(s_pd):.0f}", flush=True)

    # ---- panel ----
    fig, ax = plt.subplots(2, 3, figsize=(15, 9))

    def plot_traj(axx, key, ylab):
        for arm, col, lab in ((combo, "goldenrod", "combinatorial"), (addn, "steelblue", "additive null"),
                              (aso, "dimgray", "asocial")):
            for j, a in enumerate(arm):
                tr = a[0]
                axx.plot(tr["t"], tr[key], color=col, alpha=0.85, lw=1.8,
                         label=lab if j == 0 else None)
        axx.set_xlabel("step"); axx.set_ylabel(ylab); axx.legend(fontsize=8)

    plot_traj(ax[0, 0], "max_level", "frontier depth (max tree level)")
    ax[0, 0].set_title("OPEN-ENDEDNESS: frontier depth keeps climbing (combinatorial)")
    plot_traj(ax[0, 1], "pop_distinct", "distinct techniques in population")
    ax[0, 1].set_title("OPEN-ENDEDNESS: cumulative repertoire breadth")

    cl, ct_ = scatter_data(combo[0][3])
    al, at_ = scatter_data(addn[0][3])
    ax[0, 2].scatter(cl, ct_, s=8, alpha=0.4, color="goldenrod")
    ax[0, 2].set_xlabel("tree level (depth)"); ax[0, 2].set_ylabel("first-appearance step")
    ax[0, 2].set_title(f"COMBINATORIAL ladder: deep=late  (corr {c_corr[0]:.2f}, prec {c_pre[0]:.2f})")
    ax[1, 0].scatter(al, at_, s=8, alpha=0.4, color="steelblue")
    ax[1, 0].set_xlabel("tree level (depth)"); ax[1, 0].set_ylabel("first-appearance step")
    ax[1, 0].set_title(f"ADDITIVE null: scrambled  (corr {a_corr[0]:.2f}, prec {a_pre[0]:.2f})")

    x = np.arange(len(seeds))
    ax[1, 1].bar(x - 0.27, c_corr, 0.27, color="goldenrod", label="combo level<->time")
    ax[1, 1].bar(x, a_corr, 0.27, color="steelblue", label="additive level<->time")
    ax[1, 1].bar(x + 0.27, c_null, 0.27, color="lightgray", label="combo null")
    ax[1, 1].axhline(0, color="grey", lw=0.8)
    ax[1, 1].set_xticks(x); ax[1, 1].set_xticklabels([f"s{s}" for s in seeds])
    ax[1, 1].set_ylabel("Spearman(level, time)")
    ax[1, 1].set_title(f"ladder recovery: COMBO>ADD {combo_gt_add}/{len(seeds)}, sig {sig}/{len(seeds)}")
    ax[1, 1].legend(fontsize=7)

    if last is not None:
        ax[1, 2].imshow(last)
        ax[1, 2].set_title(f"3D world, depth-coloured (n={combo[0][1].get('n',0)})")
    ax[1, 2].axis("off")
    fig.suptitle("R163 GENESIS — temporal phylogeny: combinatorial culture recovers the TIME-LADDER of "
                 "cumulative descent; additive null scrambles it", fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=110)
    print(f"  wrote {OUT}/panel.png  ({time.time()-t0:.0f}s total)", flush=True)


if __name__ == "__main__":
    main()
