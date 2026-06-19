"""R137 figure — Invasion fronts: Fisher-KPP pulled waves and the Allee extinction threshold.

Top row: 2D colonies — a Fisher population invades (disk grows), an Allee population over threshold
COLLAPSES (disk shrinks to extinction) from the same kind of seed.
Bottom: (B) Fisher front speed c = 2*sqrt(rD) across r,D; (C) Allee front velocity vs threshold a,
crossing zero at a = 1/2 (advance -> stall -> retreat); (D) shape-invariant travelling profiles.
GIF: a growing Fisher colony beside a collapsing Allee colony.
"""

from __future__ import annotations

import os

import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import replace

from alife.fisherfront import (FrontConfig, run1d, run2d,
                               fisher_speed_theory, allee_speed_theory)

OUT = "runs/r137_fisherfront"
os.makedirs(OUT, exist_ok=True)


def main():
    N2, ST = 180, 1500
    print("2D Fisher (invading) + Allee (collapsing) ...")
    fis = run2d(FrontConfig(), N=N2, steps=ST, seed_radius=15, record_every=40)
    alle = run2d(FrontConfig(allee=0.7), N=N2, steps=ST, seed_radius=28, record_every=40)
    print(f"  Fisher radius {fis['radius'][0]:.0f}->{fis['radius'][-1]:.0f}  "
          f"Allee radius {alle['radius'][0]:.0f}->{alle['radius'][-1]:.0f}")

    print("Fisher speed law sweep ...")
    pts = []
    for r, D in [(0.5, 1.0), (1.0, 1.0), (2.0, 1.0), (1.0, 0.5), (1.0, 2.0)]:
        c = FrontConfig(r=r, D=D)
        pts.append((fisher_speed_theory(c), run1d(c)["speed"]))

    print("Allee velocity vs threshold ...")
    avs = []
    for a in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        c = FrontConfig(allee=a)
        avs.append((a, run1d(c)["speed"], allee_speed_theory(c)))
    avs = np.array(avs)

    prof = run1d(FrontConfig(), steps=2600)["profiles"]

    fig = plt.figure(figsize=(15, 9))
    axA1 = fig.add_subplot(2, 3, 1); axA1.imshow(fis["snaps"][min(fis["snaps"])], cmap="YlGn", vmin=0, vmax=1)
    axA1.set_title("Fisher colony (start)", fontsize=10); axA1.set_xticks([]); axA1.set_yticks([])
    axA2 = fig.add_subplot(2, 3, 2); axA2.imshow(fis["u"], cmap="YlGn", vmin=0, vmax=1)
    axA2.set_title(f"Fisher INVADES (r={fis['radius'][-1]:.0f})", fontsize=10); axA2.set_xticks([]); axA2.set_yticks([])
    axA3 = fig.add_subplot(2, 3, 3); axA3.imshow(alle["u"], cmap="OrRd", vmin=0, vmax=1)
    axA3.set_title(f"Allee a=0.7 EXTINCT (r={alle['radius'][-1]:.0f})", fontsize=10); axA3.set_xticks([]); axA3.set_yticks([])

    axB = fig.add_subplot(2, 3, 4)
    pts = np.array(pts)
    lim = [0, pts[:, 0].max() * 1.1]
    axB.plot(lim, lim, "k--", lw=1, label="c = 2√(rD)")
    axB.plot(pts[:, 0], pts[:, 1], "o", color="#2ca02c", ms=9, label="measured")
    axB.set_xlabel("2√(rD) (theory)"); axB.set_ylabel("measured front speed")
    axB.set_title("B. Fisher pulled-front speed law"); axB.legend(fontsize=8)

    axC = fig.add_subplot(2, 3, 5)
    aa = np.linspace(0.05, 0.85, 50)
    axC.plot(aa, np.sqrt(0.5) * (1 - 2 * aa), "-", color="#888", label="√(rD/2)(1−2a)")
    axC.plot(avs[:, 0], avs[:, 1], "o", color="#d62728", ms=8, label="measured")
    axC.axhline(0, color="k", lw=0.8); axC.axvline(0.5, color="#1f77b4", ls=":", label="a=½ threshold")
    axC.set_xlabel("Allee threshold a"); axC.set_ylabel("front velocity")
    axC.set_title("C. Allee: invade → stall → RETREAT"); axC.legend(fontsize=8)

    axD = fig.add_subplot(2, 3, 6)
    for k in range(2, len(prof), 2):
        axD.plot(np.arange(len(prof[k])) * 0.5, prof[k], color=plt.cm.viridis(k / len(prof)), lw=1)
    axD.set_xlim(0, 700); axD.set_xlabel("x"); axD.set_ylabel("u")
    axD.set_title("D. Shape-invariant travelling front")

    fig.suptitle("R137 — Invasion fronts: Fisher-KPP pulled waves (c=2√rD) & the Allee extinction threshold",
                 fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(f"{OUT}/fisherfront.png", dpi=110)
    print(f"wrote {OUT}/fisherfront.png")

    print("rendering invasion-vs-extinction GIF ...")
    gfig, (gx1, gx2) = plt.subplots(1, 2, figsize=(9, 4.6))
    keys = sorted(fis["snaps"])
    frames = []
    for t in keys:
        for ax, sn, cmap, ttl in [(gx1, fis["snaps"][t], "YlGn", "Fisher: invades"),
                                   (gx2, alle["snaps"][t], "OrRd", "Allee a=0.7: extinct")]:
            ax.clear(); ax.imshow(sn, cmap=cmap, vmin=0, vmax=1)
            ax.set_xticks([]); ax.set_yticks([]); ax.set_title(ttl, fontsize=11)
        gfig.suptitle(f"invasion vs extinction  (t={t * 0.04:.0f})", fontsize=12)
        gfig.tight_layout(); gfig.canvas.draw()
        frames.append(np.asarray(gfig.canvas.buffer_rgba())[:, :, :3].copy())
    imageio.mimsave(f"{OUT}/fisherfront.gif", frames, fps=10, loop=0)
    print(f"wrote {OUT}/fisherfront.gif ({len(frames)} frames)")


if __name__ == "__main__":
    main()
