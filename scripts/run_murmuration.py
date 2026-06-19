"""R134 figure — Murmuration vs a predator: a flock that flees as one is barely caught.

Panel A: snapshot of the flock streaming away from the hawk (prey arrows by heading, predator red).
Panel B: flee ON vs flee OFF catch count (the control — collective evasion collapses the kill rate).
Panel C: predator-to-nearest-prey distance over time (flee keeps the hawk further out).
GIF:     the murmuration boiling around the predator.
"""

from __future__ import annotations

import os

import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import replace

from alife.murmuration import MurmurConfig, run

OUT = "runs/r134_murmuration"
os.makedirs(OUT, exist_ok=True)

CFG = MurmurConfig(N=160, steps=1500, seed=2)


def _frame(ax, p, v, pp, L, title=""):
    ax.clear()
    vu = v / np.maximum(np.hypot(v[:, 0], v[:, 1])[:, None], 1e-9)
    spd = np.hypot(v[:, 0], v[:, 1])
    ax.quiver(p[:, 0], p[:, 1], vu[:, 0], vu[:, 1], spd, cmap="viridis",
              scale=42, width=0.004, headwidth=3.5, pivot="mid")
    ax.plot(pp[0], pp[1], "o", ms=15, color="#d62728", mec="k", mew=1.2, zorder=5)
    ax.text(pp[0], pp[1] + 2.0, "hawk", color="#d62728", ha="center", fontsize=9, weight="bold")
    ax.set_xlim(0, L); ax.set_ylim(0, L); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    if title:
        ax.set_title(title, fontsize=11)


def main():
    print("running flee ON (with GIF snapshots) ...")
    on = run(CFG, record_every=12)
    print("running flee OFF control ...")
    off = run(replace(CFG, flee=0.0), record_every=12)
    print(f"catches: ON={on['catches']}  OFF={off['catches']}  "
          f"({off['catches'] / max(on['catches'], 1):.0f}x), polariz(on)={on['polarization']:.2f}")

    fig = plt.figure(figsize=(15, 5))
    axA = fig.add_subplot(1, 3, 1)
    _frame(axA, on["p"], on["v"], on["pp"], CFG.L,
           f"A. Flock flees as one (caught {on['catches']}x)")

    axB = fig.add_subplot(1, 3, 2)
    axB.bar(["flee ON\n(murmuration)", "flee OFF\n(ignore hawk)"], [on["catches"], off["catches"]],
            color=["#2ca02c", "#d62728"])
    axB.set_ylabel("prey caught")
    axB.set_title(f"B. Collective evasion: {off['catches'] / max(on['catches'], 1):.0f}x fewer kills")
    for i, c in enumerate([on["catches"], off["catches"]]):
        axB.text(i, c, str(c), ha="center", va="bottom", fontsize=11, weight="bold")

    axC = fig.add_subplot(1, 3, 3)
    w = 25
    kon = np.convolve(on["near_dist"], np.ones(w) / w, "valid")
    koff = np.convolve(off["near_dist"], np.ones(w) / w, "valid")
    axC.plot(kon, color="#2ca02c", label=f"flee ON (mean {on['near_dist'].mean():.1f})")
    axC.plot(koff, color="#d62728", label=f"flee OFF (mean {off['near_dist'].mean():.1f})")
    axC.set_xlabel("step"); axC.set_ylabel("hawk → nearest prey (smoothed)")
    axC.set_title("C. Fleeing keeps the hawk at bay"); axC.legend(fontsize=8)

    fig.suptitle("R134 — Murmuration: a flock that flees together starves the predator", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(f"{OUT}/murmuration.png", dpi=110)
    print(f"wrote {OUT}/murmuration.png")

    print("rendering GIF ...")
    gfig, gax = plt.subplots(figsize=(5, 5))
    frames = []
    for k, (p, v, pp) in enumerate(on["snaps"]):
        _frame(gax, p, v, pp, CFG.L, f"murmuration vs hawk  (t={k * 12})")
        gfig.tight_layout()
        gfig.canvas.draw()
        frames.append(np.asarray(gfig.canvas.buffer_rgba())[:, :, :3].copy())
    imageio.mimsave(f"{OUT}/murmuration.gif", frames, fps=18, loop=0)
    print(f"wrote {OUT}/murmuration.gif ({len(frames)} frames)")


if __name__ == "__main__":
    main()
