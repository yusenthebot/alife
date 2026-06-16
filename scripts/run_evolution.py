#!/usr/bin/env python
"""Run the evolving ecosystem headless and emit artifacts for inspection.

Outputs into runs/<name>/:
  evolution.mp4         creatures (hue = food-attraction trait) feeding on green motes
  eco_frame_*.png       key stills (start / quarter / half / end)
  population.png        population, food, mean energy, max generation over time
  traits.png            mean of every heritable trait over time (selection trajectories)
  trait_hist.png        initial vs final distribution of each trait (selection vs drift)
  evolution.csv         per-step time series

Usage:
  python scripts/run_evolution.py --steps 2500 --name evo
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import imageio.v2 as imageio
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alife import genome as gn  # noqa: E402
from alife.ecosystem import EcoConfig, Ecosystem  # noqa: E402
from alife.render import Renderer  # noqa: E402
from alife.world import World  # noqa: E402


def trait_hue(dna: np.ndarray) -> np.ndarray:
    t = (dna[:, gn.W_FOOD] - gn.TRAIT_LO[gn.W_FOOD]) / (gn.TRAIT_HI[gn.W_FOOD] - gn.TRAIT_LO[gn.W_FOOD])
    return 0.66 * (1.0 - np.clip(t, 0.0, 1.0))  # high food-drive -> red, low -> blue


def save_csv(path: Path, series: dict) -> None:
    keys = list(series.keys())
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["step", *keys])
        for t in range(len(next(iter(series.values())))):
            w.writerow([t, *(f"{series[k][t]:.4f}" for k in keys)])


def plot_population(path: Path, s: dict) -> None:
    fig, ax = plt.subplots(2, 2, figsize=(11, 7))
    pairs = [
        ("population", "Population", "tab:blue"),
        ("food", "Standing food", "tab:green"),
        ("mean_energy", "Mean energy", "tab:orange"),
        ("max_gen", "Max generation reached", "tab:purple"),
    ]
    for a, (k, title, c) in zip(ax.flat, pairs):
        a.plot(s[k], color=c, lw=1.5)
        a.set_title(title)
        a.set_xlabel("step")
        a.grid(alpha=0.25)
    fig.suptitle("Ecosystem dynamics")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def plot_traits(path: Path, s: dict) -> None:
    fig, ax = plt.subplots(figsize=(11, 6))
    for i, name in enumerate(gn.TRAIT_NAMES):
        series = np.array(s[f"trait_{name}"])
        norm = (series - gn.TRAIT_LO[i]) / (gn.TRAIT_HI[i] - gn.TRAIT_LO[i])
        ax.plot(norm, lw=1.8, label=name)
    ax.set_title("Mean trait value over time (normalized to [0,1]) — selection trajectories")
    ax.set_xlabel("step")
    ax.set_ylabel("normalized mean trait")
    ax.set_ylim(0, 1)
    ax.grid(alpha=0.25)
    ax.legend(loc="upper left", ncol=2, fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def plot_hist(path: Path, dna0: np.ndarray, dna1: np.ndarray) -> None:
    fig, ax = plt.subplots(2, 4, figsize=(14, 7))
    for i, name in enumerate(gn.TRAIT_NAMES):
        a = ax.flat[i]
        bins = np.linspace(gn.TRAIT_LO[i], gn.TRAIT_HI[i], 24)
        a.hist(dna0[:, i], bins=bins, alpha=0.5, color="tab:gray", density=True, label="initial")
        a.hist(dna1[:, i], bins=bins, alpha=0.6, color="tab:red", density=True, label="final")
        a.set_title(name, fontsize=10)
        a.grid(alpha=0.2)
    ax.flat[0].legend(fontsize=9)
    ax.flat[-1].axis("off")
    fig.suptitle("Trait distributions: initial (random) vs final (selected)")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=2500)
    ap.add_argument("--n0", type=int, default=260)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--size", type=float, default=220.0)
    ap.add_argument("--food-value", type=float, default=17.0)
    ap.add_argument("--food-cap", type=int, default=620)
    ap.add_argument("--res", type=int, default=900)
    ap.add_argument("--capture-every", type=int, default=5)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--name", type=str, default="evo")
    args = ap.parse_args()

    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)

    world = World(args.size, args.size, toroidal=True)
    cfg = EcoConfig(world=world, n0=args.n0, food_cap=args.food_cap, food_value=args.food_value)
    eco = Ecosystem(cfg, seed=args.seed)
    renderer = Renderer(world, resolution=args.res, boid_size=2.8)

    dna0 = eco.dna.copy()
    series: dict[str, list[float]] = {}
    frames: list[np.ndarray] = []

    print(f"Evolving {args.n0} creatures for {args.steps} steps ...")
    for t in range(args.steps):
        snap = eco.snapshot()
        for k, v in snap.items():
            series.setdefault(k, []).append(v)
        if t % args.capture_every == 0 and eco.pos.shape[0]:
            frames.append(renderer.eco_frame(eco.pos, eco.vel, trait_hue(eco.dna), eco.food))
        eco.step()
        if eco.pos.shape[0] == 0:
            print(f"EXTINCTION at step {t}")
            break

    print("Writing evolution.mp4 ...")
    with imageio.get_writer(out / "evolution.mp4", fps=args.fps, macro_block_size=1) as w:
        for f in frames:
            w.append_data(f)
    marks = {"eco_frame_start.png": 0, "eco_frame_quarter.png": len(frames) // 4,
             "eco_frame_half.png": len(frames) // 2, "eco_frame_end.png": len(frames) - 1}
    for fname, idx in marks.items():
        if frames:
            imageio.imwrite(out / fname, frames[idx])

    save_csv(out / "evolution.csv", series)
    plot_population(out / "population.png", series)
    plot_traits(out / "traits.png", series)
    plot_hist(out / "trait_hist.png", dna0, eco.dna)

    print(f"\nPopulation: {args.n0} -> {eco.pos.shape[0]} | births {eco.births} deaths {eco.deaths} | "
          f"max gen {int(series['max_gen'][-1])}")
    print("Mean trait  initial -> final:")
    for i, name in enumerate(gn.TRAIT_NAMES):
        if eco.pos.shape[0]:
            print(f"  {name:12s} {dna0[:, i].mean():6.3f} -> {eco.dna[:, i].mean():6.3f}")
    print(f"Artifacts in {out}")


if __name__ == "__main__":
    main()
