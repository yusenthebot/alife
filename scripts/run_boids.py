#!/usr/bin/env python
"""Run a Boids flocking simulation headless and emit artifacts for inspection.

Outputs into runs/<name>/:
  flock.mp4          animation of the swarm
  frame_*.png        key still frames (start / quarter / half / end)
  metrics.csv        per-step time series
  metrics.png        plots of order parameter, packing, milling, clusters

Usage:
  python scripts/run_boids.py --n 700 --steps 450 --name demo
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alife.boids import BoidParams  # noqa: E402
from alife.render import Renderer  # noqa: E402
from alife.sim import SimConfig, run  # noqa: E402
from alife.world import World  # noqa: E402


def save_metrics_csv(path: Path, series: dict) -> None:
    keys = list(series.keys())
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["step", *keys])
        for t in range(len(next(iter(series.values())))):
            writer.writerow([t, *(f"{series[k][t]:.5f}" for k in keys)])


def save_metrics_plot(path: Path, series: dict) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    plots = [
        ("order", "Order parameter φ (alignment)", "tab:cyan", (0, 1)),
        ("nn_dist", "Mean nearest-neighbor distance", "tab:orange", None),
        ("rotation", "Rotation order (milling)", "tab:green", (0, 1)),
        ("clusters", "Number of clusters", "tab:red", None),
    ]
    for ax, (key, title, color, ylim) in zip(axes.flat, plots):
        ax.plot(series[key], color=color, lw=1.6)
        ax.set_title(title)
        ax.set_xlabel("step")
        ax.grid(alpha=0.25)
        if ylim:
            ax.set_ylim(*ylim)
    fig.suptitle("Boids emergence metrics", fontsize=14)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=700)
    ap.add_argument("--steps", type=int, default=450)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--size", type=float, default=200.0)
    ap.add_argument("--res", type=int, default=900)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--name", type=str, default="demo")
    args = ap.parse_args()

    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)

    world = World(width=args.size, height=args.size, toroidal=True)
    cfg = SimConfig(n=args.n, steps=args.steps, seed=args.seed, world=world, params=BoidParams())
    renderer = Renderer(world, resolution=args.res)

    print(f"Running {args.n} boids x {args.steps} steps ...")
    result = run(cfg, renderer=renderer, capture_every=1)

    print("Writing flock.mp4 ...")
    with imageio.get_writer(out / "flock.mp4", fps=args.fps, macro_block_size=1) as w:
        for frame in result.frames:
            w.append_data(frame)

    marks = {
        "frame_start.png": 0,
        "frame_quarter.png": len(result.frames) // 4,
        "frame_half.png": len(result.frames) // 2,
        "frame_end.png": len(result.frames) - 1,
    }
    for fname, idx in marks.items():
        imageio.imwrite(out / fname, result.frames[idx])

    save_metrics_csv(out / "metrics.csv", result.metrics)
    save_metrics_plot(out / "metrics.png", result.metrics)

    m = result.metrics
    print(
        f"order: {m['order'][0]:.3f} -> {m['order'][-1]:.3f} | "
        f"nn_dist: {m['nn_dist'][0]:.2f} -> {m['nn_dist'][-1]:.2f} | "
        f"clusters: {int(m['clusters'][0])} -> {int(m['clusters'][-1])}"
    )
    print(f"Artifacts in {out}")


if __name__ == "__main__":
    main()
