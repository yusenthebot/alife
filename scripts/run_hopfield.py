"""R69 — Hopfield networks: memory as an energy landscape, and its breaking point.

Stored patterns become valleys in an energy landscape; from a corrupted cue the network slides
downhill into the nearest memory (content-addressable, error-correcting recall). Energy
decreases monotonically to the attractor, and beyond ~0.138 N stored patterns recall collapses.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.gridspec import GridSpec  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.hopfield import (  # noqa: E402
    store_hebbian, recall, overlap, corrupt, capacity_curve, demo_patterns,
)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r69_hopfield"


def _img(ax, vec, shape, title=""):
    ax.imshow(vec.reshape(shape), cmap="binary", vmin=-1, vmax=1)
    ax.set_xticks([]); ax.set_yticks([])
    if title:
        ax.set_title(title, fontsize=8)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pats, shape = demo_patterns(14)
    W = store_hebbian(pats)
    rng = np.random.default_rng(0)
    P = len(pats)

    recalled, cues, recovs = [], [], []
    for mu in range(P):
        cue = corrupt(pats[mu], 0.30, rng)
        s, et, _ = recall(W, cue, steps=30, seed=1)
        cues.append(cue); recalled.append(s)
        recovs.append(overlap(s, pats[mu]))
    print(f"recall from 30% noise: overlaps {[round(v, 2) for v in recovs]}")

    # energy descent for one heavily-corrupted cue
    cueE = corrupt(pats[3], 0.35, rng)
    _, etrace, _ = recall(W, cueE, steps=30, seed=2)

    al, acc = capacity_curve(N=200, alphas=np.linspace(0.02, 0.30, 15), trials=6, seed=3)
    ac = 0.138
    print(f"capacity: recall below alpha_c~{ac} stays ~1, collapses above; "
          f"acc@0.10={acc[np.argmin(abs(al-0.10))]:.2f} acc@0.25={acc[np.argmin(abs(al-0.25))]:.2f}")

    fig = plt.figure(figsize=(16.5, 9.5))
    fig.suptitle("R69 — Hopfield networks: memories as energy valleys, recalled from corrupted cues",
                 fontsize=14, fontweight="bold")
    gs = GridSpec(4, P, figure=fig, height_ratios=[1, 1, 1, 1.5], hspace=0.35, wspace=0.1)

    for mu in range(P):
        _img(fig.add_subplot(gs[0, mu]), pats[mu], shape, "stored memory" if mu == 0 else "")
        _img(fig.add_subplot(gs[1, mu]), cues[mu], shape, "30% corrupted cue" if mu == 0 else "")
        a = fig.add_subplot(gs[2, mu]); _img(a, recalled[mu], shape, "recalled" if mu == 0 else "")
        a.set_xlabel(f"overlap {recovs[mu]:+.2f}", fontsize=8)

    axE = fig.add_subplot(gs[3, 0:2])
    axE.plot(etrace, "o-", color="#1d9bf0", lw=2)
    axE.set_title("Energy descends monotonically to the attractor", fontsize=10)
    axE.set_xlabel("update sweep"); axE.set_ylabel("energy E = -½ sᵀWs"); axE.grid(alpha=0.25)

    axC = fig.add_subplot(gs[3, 2:P])
    axC.plot(al, acc, "o-", color="#e0245e", lw=2)
    axC.axvline(ac, color="#1f7a1f", ls="--", lw=1.5, label=f"αc ≈ {ac} (theory)")
    axC.set_title("Capacity phase transition: recall collapses above αc", fontsize=10)
    axC.set_xlabel("load α = P / N"); axC.set_ylabel("recall |overlap|")
    axC.set_ylim(0, 1.03); axC.legend(fontsize=8); axC.grid(alpha=0.25)

    path = OUT / "hopfield.png"
    fig.savefig(path, dpi=110, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
