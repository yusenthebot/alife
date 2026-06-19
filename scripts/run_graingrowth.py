"""R136 figure — Grain growth: a polycrystal coarsens by curvature (soap froth / annealed metal).

Top row: the grain mosaic at three times — a fine salt-and-pepper of orientations coarsens into big
grains. Bottom: (B) boundary length per area decays as a power law (anneal) vs frozen (greedy/no-noise
pinning control); (C) grain count and mean grain area vs time — the two-measure consistency (grain
count ~ 1/area ~ t^-2x while boundary ~ 1/R ~ t^-x).
GIF: the mosaic coarsening.
"""

from __future__ import annotations

import os

import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import replace

from alife.graingrowth import GrainConfig, run, coarsening_exponent

OUT = "runs/r136_graingrowth"
os.makedirs(OUT, exist_ok=True)

CFG = GrainConfig(L=200, Q=64, T=0.6, steps=200, seed=2)
LUT = np.random.default_rng(7).random((CFG.Q, 3)) * 0.85 + 0.1   # distinct colour per orientation


def main():
    log = [2, 5, 12, 30, 70, 130, 200]
    gif_at = sorted(set([0] + [int(round(x)) for x in np.geomspace(2, 200, 36)]))
    print("annealing (with history + GIF snapshots) ...")
    r = run(CFG, log_at=log, record_at=gif_at)
    print("greedy pinning control ...")
    g = run(replace(CFG, greedy=True), log_at=log)
    eb = coarsening_exponent(r["t"], r["bond"]); eg = coarsening_exponent(r["t"], r["ngrains"])
    print(f"  bond exp={eb:.2f}  grain exp={eg:.2f}  ratio={eg/eb:.2f}  "
          f"grains {int(r['ngrains'][0])}->{int(r['ngrains'][-1])}")

    gallery_t = [2, 30, 200]
    rg = run(CFG, record_at=gallery_t)

    fig = plt.figure(figsize=(15, 9))
    for i, t in enumerate(gallery_t):
        ax = fig.add_subplot(2, 3, i + 1)
        ax.imshow(LUT[rg["snaps"][t]], interpolation="nearest")
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(f"t = {t} sweeps", fontsize=11)

    axB = fig.add_subplot(2, 3, 4)
    axB.loglog(r["t"], r["bond"], "o-", color="#1f77b4", label=f"anneal (slope {eb:.2f})")
    axB.loglog(g["t"], g["bond"], "s--", color="#999999", label="greedy / no noise (pinned)")
    axB.set_xlabel("time (sweeps)"); axB.set_ylabel("boundary length per site")
    axB.set_title("B. Boundaries retract as a power law"); axB.legend(fontsize=8)

    axC = fig.add_subplot(2, 3, 5)
    axC.loglog(r["t"], r["ngrains"], "o-", color="#d62728", label=f"grain count (slope {eg:.2f})")
    area = CFG.L ** 2 / r["ngrains"]
    axC.loglog(r["t"], area, "^-", color="#2ca02c", label="mean grain area")
    axC.set_xlabel("time (sweeps)"); axC.set_ylabel("count  /  area")
    axC.set_title(f"C. Grains coarsen (area×{area[-1]/area[0]:.0f}); grain exp ≈ 2× bond exp")
    axC.legend(fontsize=8)

    axD = fig.add_subplot(2, 3, 6)
    axD.imshow(LUT[r["s"]], interpolation="nearest")
    axD.set_xticks([]); axD.set_yticks([])
    axD.set_title("D. Final coarse polycrystal", fontsize=11)

    fig.suptitle("R136 — Grain growth: a polycrystal coarsens by curvature (Q-state Potts, von Neumann-Mullins)",
                 fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(f"{OUT}/graingrowth.png", dpi=110)
    print(f"wrote {OUT}/graingrowth.png")

    print("rendering coarsening GIF ...")
    gfig, gax = plt.subplots(figsize=(5, 5))
    frames = []
    for t in gif_at:
        gax.clear()
        gax.imshow(LUT[r["snaps"][t]], interpolation="nearest")
        gax.set_xticks([]); gax.set_yticks([])
        gax.set_title(f"grain growth  (t={t})", fontsize=11)
        gfig.tight_layout(); gfig.canvas.draw()
        frames.append(np.asarray(gfig.canvas.buffer_rgba())[:, :, :3].copy())
    imageio.mimsave(f"{OUT}/graingrowth.gif", frames, fps=10, loop=0)
    print(f"wrote {OUT}/graingrowth.gif ({len(frames)} frames)")


if __name__ == "__main__":
    main()
