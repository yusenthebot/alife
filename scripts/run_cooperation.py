#!/usr/bin/env python
"""Round 19 — evolution of cooperation (Hamilton's rule).

Sweeps assortment and shows cooperation switching on right at the Hamilton
threshold (assortment = c/b), plus example trajectories.

Artifacts into runs/<name>/:
  cooperation.png   cooperation vs assortment (threshold at c/b) + trajectories
Usage:
  python scripts/run_cooperation.py --name cooperation
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

from alife.cooperation import CooperationConfig, evolve, sweep_assortment  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--name", type=str, default="cooperation")
    args = ap.parse_args()
    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)
    cfg = CooperationConfig()
    thr = cfg.cost / cfg.benefit

    ass = np.linspace(0, 0.7, 15)
    final = sweep_assortment(cfg, ass, seed=args.seed)

    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    ax[0].plot(ass, final, "o-", color="tab:green", lw=2)
    ax[0].axvline(thr, color="tab:red", ls="--", lw=1.5, label=f"Hamilton threshold c/b = {thr:.2f}")
    ax[0].set_title("Cooperation evolves above assortment = c/b")
    ax[0].set_xlabel("assortment (relatedness proxy)"); ax[0].set_ylabel("final cooperation level")
    ax[0].set_ylim(0, 1); ax[0].grid(alpha=0.25); ax[0].legend()

    for a, color in [(0.1, "tab:red"), (0.25, "tab:orange"), (0.5, "tab:green")]:
        traj = evolve(cfg, assortment=a, seed=args.seed)
        ax[1].plot(traj, color=color, lw=1.8, label=f"assortment {a}")
    ax[1].set_title("Cooperation over generations")
    ax[1].set_xlabel("generation"); ax[1].set_ylabel("mean cooperation"); ax[1].set_ylim(0, 1)
    ax[1].grid(alpha=0.25); ax[1].legend()
    fig.suptitle("Evolution of cooperation: Hamilton's rule (cooperation evolves iff assortment·b > c)", fontsize=13)
    fig.tight_layout(); fig.savefig(out / "cooperation.png", dpi=110); plt.close(fig)

    print(f"threshold c/b={thr:.2f} | cooperation at a=0.1: {final[2]:.2f}, a=0.5: {sweep_assortment(cfg,[0.5],seed=args.seed)[0]:.2f}")
    print(f"Artifacts in {out}")


if __name__ == "__main__":
    main()
