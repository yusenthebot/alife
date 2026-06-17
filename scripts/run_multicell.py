#!/usr/bin/env python
"""Round 21 — a major transition: the evolution of multicellularity.

With a size-selective predator, cells evolve to cluster (multicellularity); without
it, they stay unicellular. Plots the trajectories and the fitness landscape that
drives them.

Artifacts into runs/<name>/:
  multicell.png   stickiness over generations + fitness-vs-size landscape
Usage:
  python scripts/run_multicell.py --name multicell
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

from alife.multicell import MulticellConfig, cluster_size, evolve, fitness  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--name", type=str, default="multicell")
    args = ap.parse_args()
    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)
    cfg = MulticellConfig()

    h_pred, size_pred = evolve(cfg, predation=True, seed=args.seed)
    h_no, size_no = evolve(cfg, predation=False, seed=args.seed)

    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    ax[0].plot(h_pred, color="tab:red", lw=2, label=f"with predator (-> {size_pred:.1f} cells/cluster)")
    ax[0].plot(h_no, color="tab:blue", lw=2, label=f"no predator (-> {size_no:.1f} cells/cluster)")
    ax[0].set_title("Stickiness (clustering) over generations")
    ax[0].set_xlabel("generation"); ax[0].set_ylabel("mean stickiness"); ax[0].set_ylim(0, 1)
    ax[0].grid(alpha=0.25); ax[0].legend()

    s = np.linspace(0, 1, 200)
    sizes = cluster_size(s, cfg)
    ax[1].plot(sizes, fitness(s, cfg, predation=True), color="tab:red", lw=2, label="with predator")
    ax[1].plot(sizes, fitness(s, cfg, predation=False), color="tab:blue", lw=2, label="no predator")
    ax[1].axvline(cfg.pred_threshold, color="gray", ls="--", lw=1, label="predator size threshold")
    ax[1].set_title("Fitness landscape vs cluster size")
    ax[1].set_xlabel("cluster size (cells)"); ax[1].set_ylabel("fitness")
    ax[1].grid(alpha=0.25); ax[1].legend()
    fig.suptitle("Evolution of multicellularity: predation selects for clustering (a major transition)", fontsize=13)
    fig.tight_layout(); fig.savefig(out / "multicell.png", dpi=110); plt.close(fig)

    print(f"with predator: cluster size -> {size_pred:.1f} cells | no predator: -> {size_no:.1f} cells")
    print(f"Artifacts in {out}")


if __name__ == "__main__":
    main()
