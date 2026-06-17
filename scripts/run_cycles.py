#!/usr/bin/env python
"""Round 15 — sustained predator-prey population cycles (Lotka-Volterra at last).

Runs the refuge-stabilized ecology and plots the oscillation + the phase-plane
limit cycle (a closed loop, not a spiral into a fixed point — the difference from
R5/R10's stable coexistence).

Artifacts into runs/<name>/:
  cycles.png       prey & predator populations oscillating over time
  cycles_phase.png predator-vs-prey phase plane (the limit cycle)
Usage:
  python scripts/run_cycles.py --steps 7000 --name cycles
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

from alife.cycles import CyclesConfig, CyclesEcosystem  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=7000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--name", type=str, default="cycles")
    args = ap.parse_args()
    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)

    eco = CyclesEcosystem(CyclesConfig(), seed=args.seed)
    prey, pred, food = [], [], []
    print(f"Running predator-prey cycles for {args.steps} steps ...")
    for t in range(args.steps):
        eco.step(); s = eco.snapshot()
        prey.append(s["prey"]); pred.append(s["pred"]); food.append(s["food"])
        if eco.pred["pos"].shape[0] == 0:
            print(f"  predators died at {t}"); break
    prey, pred = np.array(prey), np.array(pred)

    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax1.plot(prey, color="tab:cyan", lw=1.2, label="prey")
    ax1.set_xlabel("step"); ax1.set_ylabel("prey", color="tab:blue"); ax1.tick_params(axis="y", labelcolor="tab:blue")
    ax2 = ax1.twinx()
    ax2.plot(pred, color="tab:red", lw=1.2, label="predators")
    ax2.set_ylabel("predators", color="tab:red"); ax2.tick_params(axis="y", labelcolor="tab:red")
    ax1.set_title("Sustained predator-prey cycles (both oscillate, out of phase)")
    ax1.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(out / "cycles.png", dpi=110); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 6.5))
    tt = np.arange(len(prey))
    ax.scatter(prey, pred, c=tt, cmap="twilight", s=5)
    ax.plot(prey, pred, color="gray", lw=0.3, alpha=0.4)
    ax.set_xlabel("prey population"); ax.set_ylabel("predator population")
    ax.set_title("Phase plane (color = time): the limit cycle")
    ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(out / "cycles_phase.png", dpi=110); plt.close(fig)

    try:
        from scipy.signal import find_peaks
        h = pred[len(pred) // 6:]
        pk, _ = find_peaks(h, prominence=h.std() * 0.4, distance=120)
        print(f"predator cycles: {len(pk)} peaks | pred {int(pred.min())}-{int(pred.max())} | prey {int(prey.min())}-{int(prey.max())}")
    except Exception:
        pass
    print(f"survived {len(prey)} steps. Artifacts in {out}")


if __name__ == "__main__":
    main()
