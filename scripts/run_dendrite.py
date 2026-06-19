"""R139 figure — Dendritic solidification: snowflake & cubic crystals from an undercooled melt.

Top: a six-fold (ice) dendrite, a four-fold (cubic-metal) dendrite, and the same six-fold crystal grown
with interface noise so SIDE BRANCHES sprout.
Bottom: (D) the latent-heat halo (warm melt around the crystal); (E) arm count = anisotropy mode j;
(F) anisotropy drives growth — solid fraction vs time, δ>0 (dendritic) vs δ=0 (slow, grid-limited).
GIF: the six-fold dendrite growing its arms.
"""

from __future__ import annotations

import os

import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import replace

from alife.dendrite import DendriteConfig, run, arm_count, solid_fraction

OUT = "runs/r139_dendrite"
os.makedirs(OUT, exist_ok=True)

CFG = DendriteConfig(N=300, steps=4200, seed=3)


def main():
    print("growing six-fold dendrite (with snapshots) ...")
    r6 = run(replace(CFG, j=6), record_every=120)
    print("growing four-fold dendrite ...")
    r4 = run(replace(CFG, j=4))
    print("growing six-fold with side-branch noise ...")
    rn = run(replace(CFG, j=6, noise=0.018))
    print("isotropic control (delta=0) for growth curve ...")
    r0 = run(replace(CFG, delta=0.0), record_every=120)
    print(f"  arms: j6={arm_count(r6['p'])}  j4={arm_count(r4['p'])}  "
          f"frac j6={solid_fraction(r6['p']):.3f} delta0={solid_fraction(r0['p']):.3f}")

    fig = plt.figure(figsize=(15, 9))
    for i, (r, ttl) in enumerate([(r6, f"six-fold (ice) — {arm_count(r6['p'])} arms"),
                                  (r4, f"four-fold (cubic) — {arm_count(r4['p'])} arms"),
                                  (rn, "six-fold + noise → side branches")]):
        ax = fig.add_subplot(2, 3, i + 1)
        ax.imshow(r["p"], cmap="bone"); ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(ttl, fontsize=11)

    axD = fig.add_subplot(2, 3, 4)
    im = axD.imshow(r6["T"], cmap="inferno"); axD.set_xticks([]); axD.set_yticks([])
    axD.set_title("D. Latent-heat halo (T around crystal)"); fig.colorbar(im, ax=axD, fraction=0.046)

    axE = fig.add_subplot(2, 3, 5)
    axE.bar(["j=4", "j=6"], [arm_count(r4["p"]), arm_count(r6["p"])], color=["#1f77b4", "#2ca02c"])
    axE.set_ylabel("primary arms measured"); axE.set_ylim(0, 8)
    axE.set_title("E. Arm count = anisotropy mode j")
    for i, v in enumerate([arm_count(r4["p"]), arm_count(r6["p"])]):
        axE.text(i, v, str(v), ha="center", va="bottom", weight="bold")

    axF = fig.add_subplot(2, 3, 6)
    t6 = sorted(r6["snaps"]); f6 = [solid_fraction(r6["snaps"][t]) for t in t6]
    t0 = sorted(r0["snaps"]); f0 = [solid_fraction(r0["snaps"][t]) for t in t0]
    axF.plot(t6, f6, color="#2ca02c", label="δ=0.04 (dendritic)")
    axF.plot(t0, f0, color="#999999", label="δ=0 (isotropic, slow)")
    axF.set_xlabel("step"); axF.set_ylabel("solid fraction")
    axF.set_title("F. Anisotropy drives growth"); axF.legend(fontsize=8)

    fig.suptitle("R139 — Dendritic solidification: snowflake & cubic crystals from an undercooled melt (Kobayashi phase field)",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(f"{OUT}/dendrite.png", dpi=110)
    print(f"wrote {OUT}/dendrite.png")

    print("rendering growth GIF ...")
    gfig, gax = plt.subplots(figsize=(5, 5))
    frames = []
    for t in sorted(r6["snaps"]):
        gax.clear(); gax.imshow(r6["snaps"][t], cmap="bone")
        gax.set_xticks([]); gax.set_yticks([]); gax.set_title(f"snowflake dendrite  (t={t})", fontsize=11)
        gfig.tight_layout(); gfig.canvas.draw()
        frames.append(np.asarray(gfig.canvas.buffer_rgba())[:, :, :3].copy())
    imageio.mimsave(f"{OUT}/dendrite.gif", frames, fps=10, loop=0)
    print(f"wrote {OUT}/dendrite.gif ({len(frames)} frames)")


if __name__ == "__main__":
    main()
