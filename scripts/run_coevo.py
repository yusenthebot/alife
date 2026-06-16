#!/usr/bin/env python
"""Round 4 — predator–prey co-evolution (an evolutionary arms race).

Artifacts into runs/<name>/:
  arms_race.png       predator hunting skill & prey evasion skill over
                      generations, each measured vs the FINAL evolved opponent
                      (de-confounded: both rising = a real arms race)
  coevo.mp4 + frames  evolved predators (red) hunting evolved prey (cyan) that
                      forage green food and flee — behavior, evolved, no rules

Usage:
  python scripts/run_coevo.py --generations 55 --name coevo
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import imageio.v2 as imageio
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alife.coevo import CoevoConfig, arms_race_curves, coevolve, rollout  # noqa: E402
from alife.render import Renderer  # noqa: E402
from alife.world import World  # noqa: E402


def plot_arms_race(path: Path, gens, pred_skill, prey_skill) -> None:
    fig, ax1 = plt.subplots(figsize=(9.5, 5.5))
    ax1.plot(gens, pred_skill, "o-", color="tab:red", lw=2, label="predator hunting (catches vs final prey)")
    ax1.set_xlabel("generation")
    ax1.set_ylabel("predator catches / episode", color="tab:red")
    ax1.tick_params(axis="y", labelcolor="tab:red")
    ax2 = ax1.twinx()
    ax2.plot(gens, prey_skill, "s-", color="tab:cyan", lw=2, label="prey evasion (survival vs final predators)")
    ax2.set_ylabel("prey survival rate", color="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:blue")
    ax1.set_title("Predator–prey arms race: both species escalate vs the final opponent")
    ax1.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--generations", type=int, default=55)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--world", type=float, default=200.0)
    ap.add_argument("--res", type=int, default=900)
    ap.add_argument("--roll-steps", type=int, default=600)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--name", type=str, default="coevo")
    args = ap.parse_args()

    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)
    cfg = CoevoConfig(world=World(args.world, args.world, toroidal=True), generations=args.generations)

    print(f"Co-evolving predators & prey for {args.generations} generations ...")
    result = coevolve(cfg, seed=args.seed)
    gens, pred_skill, prey_skill = arms_race_curves(result, cfg)
    print(f"  predator hunting (vs final prey): {pred_skill[0]:.0f} -> {pred_skill[-1]:.0f}")
    print(f"  prey evasion (survival vs final preds): {prey_skill[0]:.2f} -> {prey_skill[-1]:.2f}")
    plot_arms_race(out / "arms_race.png", gens, pred_skill, prey_skill)

    print("Rendering the evolved hunt ...")
    renderer = Renderer(cfg.world, resolution=args.res, boid_size=2.6)
    frames = rollout(result["prey"], result["pred"], cfg, seed=4321, steps=args.roll_steps, capture_every=2)
    imgs = [renderer.two_species_frame(f["prey_pos"], f["prey_vel"], f["pred_pos"], f["pred_vel"], f["food"])
            for f in frames]
    with imageio.get_writer(out / "coevo.mp4", fps=args.fps, macro_block_size=1) as w:
        for im in imgs:
            w.append_data(im)
    for fname, idx in {"coevo_start.png": 0, "coevo_mid.png": len(imgs) // 2, "coevo_end.png": len(imgs) - 1}.items():
        if imgs:
            imageio.imwrite(out / fname, imgs[idx])
    n_prey_start = frames[0]["prey_pos"].shape[0]
    n_prey_end = frames[-1]["prey_pos"].shape[0]
    print(f"  rollout: prey alive {n_prey_start} -> {n_prey_end} (predation visible)")
    print(f"Artifacts in {out}")


if __name__ == "__main__":
    main()
