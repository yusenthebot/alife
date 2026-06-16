#!/usr/bin/env python
"""Replicate the selection result across independent seeds.

Answers the one fair criticism of a single run — "could be luck": runs the
ecosystem from several random seeds and overlays the trait trajectories. If
selection is real, the adaptive traits (food-attraction up, metabolism down)
move the same way every time, while the neutral control (w_sep) stays flat in
all of them. Sequential, no rendering — light enough to run many seeds.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alife import genome as gn  # noqa: E402
from alife.ecosystem import EcoConfig, Ecosystem  # noqa: E402
from alife.world import World  # noqa: E402

TRACK = [gn.W_FOOD, gn.METABOLISM, gn.W_SEP]  # adaptive up, adaptive down, neutral control


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=6)
    ap.add_argument("--steps", type=int, default=900)
    ap.add_argument("--name", type=str, default="r2_replicates")
    args = ap.parse_args()

    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)
    cfg = EcoConfig(world=World(150.0, 150.0, toroidal=True), n0=150, pop_cap=650, food_cap=320)

    fig, ax = plt.subplots(1, 3, figsize=(14, 4.5))
    titles = ["w_food (expect ↑)", "metabolism (expect ↓)", "w_sep (neutral control)"]
    deltas: dict[int, list[float]] = {t: [] for t in TRACK}

    for seed in range(args.seeds):
        eco = Ecosystem(cfg, seed=seed)
        tracks: dict[int, list[float]] = {t: [] for t in TRACK}
        init = {t: eco.dna[:, t].mean() for t in TRACK}
        for _ in range(args.steps):
            for t in TRACK:
                tracks[t].append(eco.dna[:, t].mean() if eco.pos.shape[0] else np.nan)
            eco.step()
        for j, t in enumerate(TRACK):
            ax[j].plot(tracks[t], lw=1.3, alpha=0.85, label=f"seed {seed}")
            deltas[t].append(float(eco.dna[:, t].mean() - init[t]))

    for j, t in enumerate(TRACK):
        ax[j].set_title(titles[j])
        ax[j].set_xlabel("step")
        ax[j].set_ylim(gn.TRAIT_LO[t], gn.TRAIT_HI[t])
        ax[j].grid(alpha=0.25)
    ax[0].legend(fontsize=8)
    fig.suptitle(f"Selection across {args.seeds} independent seeds")
    fig.tight_layout()
    fig.savefig(out / "replicates.png", dpi=110)
    plt.close(fig)

    print(f"Selection direction across {args.seeds} seeds (Δ mean trait, init→final):")
    for t in TRACK:
        d = np.array(deltas[t])
        print(f"  {gn.TRAIT_NAMES[t]:11s}  mean Δ {d.mean():+.3f}  range [{d.min():+.3f}, {d.max():+.3f}]")
    wf = np.array(deltas[gn.W_FOOD])
    mb = np.array(deltas[gn.METABOLISM])
    print(f"\nw_food increased in {int((wf > 0).sum())}/{args.seeds} seeds; "
          f"metabolism decreased in {int((mb < 0).sum())}/{args.seeds} seeds.")
    print(f"Artifacts in {out}")


if __name__ == "__main__":
    main()
