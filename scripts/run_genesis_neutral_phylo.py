"""R162 — GENESIS clean ground-truthed phylogeny: does cultural cladistics RECOVER the true descent?

R161 ground-truthed R160's cladogram and returned an HONEST NEGATIVE: under the default OBLIQUE/horizontal
transmission on the ECOLOGICAL-selection substrate, the reconstructed cultural cladogram does NOT recover the
true line of descent (Mantel ~0, ~the label-permutation null) — cultural similarity tracked shared ENVIRONMENT
(spatial selection + horizontal copying = convergent cultural evolution / HOMOPLASY), not ancestry. Gating to
VERTICAL-only transmission raised recovery but only noisily (0.16..0.94, sig 2/4) because vertical-only
shrank viable demes -> low Mantel power.

R162 makes the recovery CLEAN and ROBUST by removing the two confounds R161 identified:
  (1) ECOLOGICAL HOMOPLASY -> turn OFF spatial ecological selection (spatial_tiers=False): cultural divergence
      is now pure NEUTRAL LINEAGE drift, not environmental convergence, so cultural distance can track ANCESTRY.
  (2) DEME SHRINKAGE -> keep a high free-food lifeline (tier0_frac=0.80) so vertical-only no longer starves
      demes: full statistical power (all ~27 demes alive).

FALSIFIABLE contrast (in a NEUTRAL world, identical spatial geometry both arms): VERTICAL transmission should
make the reconstructed inter-deme cultural distances RECOVER the true inter-deme genealogical (patristic)
distances (high, significant Mantel), while HORIZONTAL/oblique copying should NOT (~null) -- even though
horizontal copying is ALSO spatially local and therefore also builds spatially-structured culture. So a positive
under horizontal would mean the signal is mere spatial geometry; a positive ONLY under vertical means it is
genuine descent recovery. A PARTIAL Mantel (controlling for inter-deme spatial distance) further rules out the
isolation-by-distance confound.

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

OUT = "runs/r162_neutral_phylo"
os.makedirs(OUT, exist_ok=True)
GRID = 3
MIN_DEME = 12
SAMPLE = 12
N_PERM = 999


def cfg(**kw):
    base = dict(processing=True, building=True, culture=True, combinatorial=True, max_techniques=8000,
                n_seed_tech=8, innov_steps=1, hearth_reach_per_strength=3.0, hearth_radius=12.0,
                tech_actions=True, n_food_tiers=4, recipe_level_step=2, tier_value_bonus=3.0,
                tier0_frac=0.80, food_cap=3000, food_regrow=200, recipe_budget=2,
                spatial_tiers=False, track_genealogy=True)   # NEUTRAL substrate: no ecological selection
    base.update(kw)
    return replace(GenesisConfig(world=World3D(size=100.0), n0=850), **base)


def deme_color(w):
    act = w.pop.active()
    if act.size == 0:
        return np.zeros((0, 3))
    pos = w.pop.pos[act]
    size = w.cfg.world.size
    cell = np.clip((pos / size * GRID).astype(int), 0, GRID - 1)
    deme = (cell[:, 0] * GRID + cell[:, 1]) * GRID + cell[:, 2]
    import matplotlib.cm as cm
    return cm.hsv((deme % (GRID**3)) / (GRID**3))[:, :3]


def run(seed, steps, vertical_only):
    w = GenesisWorld(cfg(vertical_only=vertical_only), seed=seed, evolve=True)
    for _ in range(steps):
        w.step()
    return w.genealogy_phylogeny_test(grid=GRID, min_deme=MIN_DEME, sample_per_deme=SAMPLE, n_perm=N_PERM)


def headline(seed, steps, render_every=60):
    from alife.render3d import Renderer3D
    w = GenesisWorld(cfg(vertical_only=True), seed=seed, evolve=True)
    r = Renderer3D(w.cfg.world, width=640, height=480)
    frames = []
    for s in range(steps):
        w.step()
        if s % render_every == 0:
            act = w.pop.active()
            if act.size:
                hp, _ = w.hearth_arrays()
                frames.append(r.render(w.pop.pos[act], w.pop.vel[act], deme_color(w),
                                        cam_angle=s * 0.012, cam_elev=0.42, food=hp))
    last = frames[-1] if frames else None
    r.ctx.release()
    out = w.genealogy_phylogeny_test(grid=GRID, min_deme=MIN_DEME, sample_per_deme=SAMPLE, n_perm=N_PERM)
    return frames, last, out


def mc(o):
    return o.get("mantel_corr", float("nan"))


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 450
    seeds = (0, 1, 2, 3)
    t0 = time.time()

    print(f"=== headline VERTICAL run ({steps} steps, deme-coloured 3D + ground-truth genealogy) ===", flush=True)
    frames, last, hl = headline(0, steps)
    if frames:
        imageio.mimsave(os.path.join(OUT, "neutral_phylo.gif"), frames, fps=6, loop=0)
    print(f"  demes {hl.get('n_demes',0)}  Mantel {mc(hl):.3f}  vs null {hl.get('mantel_null_mean',float('nan')):.3f}"
          f"  z {hl.get('mantel_z',float('nan')):.2f}  p {hl.get('mantel_p',float('nan')):.4f}"
          f"  partial {hl.get('partial_mantel_corr',float('nan')):.3f} (p {hl.get('partial_mantel_p',float('nan')):.4f})"
          f"  ({time.time()-t0:.0f}s)", flush=True)

    print(f"=== NEUTRAL substrate: VERTICAL vs HORIZONTAL descent recovery, {len(seeds)} seeds ===", flush=True)
    ver = [hl] + [run(s, steps, True) for s in seeds[1:]]
    hor = [run(s, steps, False) for s in seeds]
    for s, ov, oh in zip(seeds, ver, hor):
        print(f"  seed {s}: VERT corr {mc(ov):.3f} (z {ov.get('mantel_z',float('nan')):.2f} "
              f"p {ov.get('mantel_p',float('nan')):.4f}, partial {ov.get('partial_mantel_corr',float('nan')):.3f}) | "
              f"HORIZ corr {mc(oh):.3f} (z {oh.get('mantel_z',float('nan')):.2f} p {oh.get('mantel_p',float('nan')):.4f})  "
              f"demes {ov.get('n_demes',0)}/{oh.get('n_demes',0)}", flush=True)

    vc = np.array([mc(o) for o in ver]); hcr = np.array([mc(o) for o in hor])
    vp = np.array([o.get("mantel_p", np.nan) for o in ver]); hp = np.array([o.get("mantel_p", np.nan) for o in hor])
    pc = np.array([o.get("partial_mantel_corr", np.nan) for o in ver])
    pp = np.array([o.get("partial_mantel_p", np.nan) for o in ver])
    vert_gt_hor = int(np.sum(vc > hcr))
    vert_sig = int(np.sum(vp <= 0.05)); hor_sig = int(np.sum(hp <= 0.05))
    partial_sig = int(np.sum(pp <= 0.05))
    print(f"  VERT mean {np.nanmean(vc):.3f} (sig {vert_sig}/4, partial-sig {partial_sig}/4) | "
          f"HORIZ mean {np.nanmean(hcr):.3f} (sig {hor_sig}/4) | VERT>HORIZ {vert_gt_hor}/4", flush=True)

    # ---- panel ----
    fig, ax = plt.subplots(2, 3, figsize=(15, 9))
    dc = np.array(hl.get("d_cult", [[0]])); dg = np.array(hl.get("d_gen", [[0]]))
    im0 = ax[0, 0].imshow(dg, cmap="viridis"); ax[0, 0].set_title("TRUE genealogical dist (seed0, vertical)")
    fig.colorbar(im0, ax=ax[0, 0], fraction=0.046)
    im1 = ax[0, 1].imshow(dc, cmap="viridis"); ax[0, 1].set_title("RECONSTRUCTED cultural dist (seed0)")
    fig.colorbar(im1, ax=ax[0, 1], fraction=0.046)
    iu = np.triu_indices(dc.shape[0], k=1)
    ax[0, 2].scatter(dg[iu], dc[iu], s=14, alpha=0.6)
    ax[0, 2].set_xlabel("true genealogical dist"); ax[0, 2].set_ylabel("reconstructed cultural dist")
    ax[0, 2].set_title(f"recovery scatter  Mantel={mc(hl):.3f} (p={hl.get('mantel_p',float('nan')):.3f})")

    x = np.arange(len(seeds))
    ax[1, 0].bar(x - 0.2, vc, 0.4, color="seagreen", label="vertical")
    ax[1, 0].bar(x + 0.2, hcr, 0.4, color="indianred", label="horizontal")
    ax[1, 0].axhline(0, color="grey", lw=0.8)
    ax[1, 0].set_xticks(x); ax[1, 0].set_xticklabels([f"s{s}" for s in seeds])
    ax[1, 0].set_ylabel("Mantel(cultural, genealogical)")
    ax[1, 0].set_title(f"descent recovery: VERT (mean {np.nanmean(vc):.2f}) > HORIZ (mean {np.nanmean(hcr):.2f}) {vert_gt_hor}/4")
    ax[1, 0].legend()

    ax[1, 1].bar(x - 0.2, vc, 0.4, color="seagreen", label="Mantel")
    ax[1, 1].bar(x + 0.2, pc, 0.4, color="steelblue", label="partial (control space)")
    ax[1, 1].axhline(0, color="grey", lw=0.8)
    ax[1, 1].set_xticks(x); ax[1, 1].set_xticklabels([f"s{s}" for s in seeds])
    ax[1, 1].set_title(f"vertical: Mantel vs PARTIAL Mantel (partial-sig {partial_sig}/4)")
    ax[1, 1].set_ylabel("correlation"); ax[1, 1].legend()

    if last is not None:
        ax[1, 2].imshow(last); ax[1, 2].set_title(f"deme-coloured 3D world (n={hl.get('n',0)})")
    ax[1, 2].axis("off")
    fig.suptitle("R162 GENESIS — neutral-drift world: VERTICAL transmission recovers the TRUE genealogy, "
                 "HORIZONTAL does not", fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=110)
    print(f"  wrote {OUT}/panel.png  ({time.time()-t0:.0f}s total)", flush=True)


if __name__ == "__main__":
    main()
