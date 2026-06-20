"""R142 — GENESIS resource partitioning: 3D GIF (agents coloured by diet) + panel + red-team.

Shows the monoculture broken: with 3 food types and a heritable diet, three specialist niches coexist
(diet diversity holds ~3) where the single-resource world collapses to one. Agents are coloured by
diet so the niches are visible as distinct foraging groups. One sim at a time; GL context released.
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

OUT = "runs/r142_niches"
os.makedirs(OUT, exist_ok=True)
PALETTE = np.array([[0.95, 0.35, 0.25], [0.35, 0.85, 0.45], [0.35, 0.55, 0.95]])  # 3 diet hues


def diet_curve(steps, seed, k, every=250):
    w = GenesisWorld(replace(GenesisConfig(), n_food_types=k), seed=seed, evolve=True)
    xs, dd, dr = [], [], []
    for s in range(steps):
        w.step()
        if s % every == 0:
            snp = w.snapshot()
            xs.append(s); dd.append(snp["diet_diversity"]); dr.append(snp["directedness"])
    return np.array(xs), np.array(dd), np.array(dr)


def headline(steps, seed=0, k=3, render_every=200):
    from alife.render3d import Renderer3D
    cfg = replace(GenesisConfig(), n_food_types=k)
    w = GenesisWorld(cfg, seed=seed, evolve=True)
    hist = {x: [] for x in ("step", "population", "directedness", "diet_diversity", "diversity")}
    frames = []
    r = Renderer3D(cfg.world, width=720, height=540)
    t0 = time.time()
    for s in range(steps):
        w.step()
        if s % 50 == 0:
            snp = w.snapshot()
            for x in hist:
                hist[x].append(snp[x])
        if s % render_every == 0:
            pos, vel, _, food = w.render_arrays()
            if pos.shape[0]:
                diet = np.clip(np.round(w.pop.diet[w.pop.active()]).astype(int), 0, k - 1)
                frames.append(r.render(pos, vel, PALETTE[diet], cam_angle=s * 0.012,
                                       cam_elev=0.42, food=food))
    r.ctx.release()
    w.save_checkpoint(os.path.join(OUT, "checkpoint.npz"))
    if frames:
        imageio.mimsave(os.path.join(OUT, "niches.gif"), frames, fps=12, loop=0)
    print(f"headline K={k}: {steps} steps {time.time()-t0:.1f}s, final diet_div "
          f"{hist['diet_diversity'][-1]:.2f} dir {hist['directedness'][-1]:+.3f}", flush=True)
    return hist


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 16000
    rt = int(sys.argv[2]) if len(sys.argv) > 2 else 6000
    print(f"=== headline K=3 niches run ({steps} steps, diet-coloured 3D) ===", flush=True)
    h = headline(steps)
    print(f"=== red-team: diet diversity K=1 vs K=3, 3 seeds, {rt} steps ===", flush=True)
    k1, k3 = [], []
    ex1 = ex3 = None
    for seed in (0, 1, 2):
        _, d1, _ = diet_curve(rt, seed, 1)
        x3, d3, r3 = diet_curve(rt, seed, 3)
        k1.append(d1[-3:].mean()); k3.append(d3[-3:].mean())
        if seed == 0:
            ex1, ex3 = d1, (x3, d3)
        print(f"  seed {seed}: K=1 diet_div {d1[-3:].mean():.2f}  K=3 diet_div {d3[-3:].mean():.2f}", flush=True)
    print(f"  MEAN K=1 {np.mean(k1):.2f} vs K=3 {np.mean(k3):.2f}", flush=True)

    fig, ax = plt.subplots(2, 3, figsize=(16, 9))
    st = np.array(h["step"])
    ax[0, 0].plot(st, h["population"], color="#1f77b4"); ax[0, 0].set_title("population (food-limited)")
    ax[0, 1].plot(st, h["diet_diversity"], color="#d62728"); ax[0, 1].axhline(3, ls=":", color="k")
    ax[0, 1].set_title("diet diversity (eff. # niches, ->3)"); ax[0, 1].set_ylim(0.8, 3.2)
    ax[0, 2].plot(st, h["directedness"], color="#2ca02c"); ax[0, 2].axhline(0, color="k", lw=0.5)
    ax[0, 2].set_title("foraging directedness (still evolves)")
    ax[1, 0].plot(st, h["diversity"], color="#ff7f0e"); ax[1, 0].set_title("lineage diversity (eff. #)")
    if ex3 is not None:
        ax[1, 1].plot(ex3[0], ex3[1], color="#d62728", label="K=3 (partitioned)")
        ax[1, 1].plot(ex3[0], ex1, color="#1f77b4", label="K=1 (single resource)")
        ax[1, 1].set_title(f"RED-TEAM diet div: K=3 {np.mean(k3):.2f} vs K=1 {np.mean(k1):.2f}")
        ax[1, 1].legend(); ax[1, 1].set_ylim(0.8, 3.2)
    ax[1, 2].axis("off")
    ax[1, 2].text(0.05, 0.5, "Agents coloured by diet in niches.gif:\nred / green / blue = the 3 diet\n"
                  "specialists. Three coexisting\nforaging niches = the monoculture\nbroken by resource "
                  "partitioning\n(competitive exclusion).", fontsize=12, va="center")
    fig.suptitle("GENESIS R142 — resource partitioning: 3 food types + heritable diet -> coexisting niches",
                 fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=100)
    print(f"wrote {OUT}/niches.gif and {OUT}/panel.png", flush=True)


if __name__ == "__main__":
    main()
