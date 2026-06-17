#!/usr/bin/env python
"""Round 9 — predator-prey co-evolution in 3D (an aerial arms race).

Artifacts into runs/<name>/:
  arms_race3d.png   predator hunting & prey evasion vs the FINAL opponent
  hunt3d.mp4 + frames   evolved predators (red) chasing evolved prey (cyan)
                        through the volume, prey foraging green food
Usage:
  python scripts/run_coevo3d.py --generations 55 --name coevo3d
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

from alife.coevo3d import Coevo3DConfig, arms_race_curves3d, coevolve3d, episode3d  # noqa: E402
from alife.render3d import Renderer3D  # noqa: E402
from alife.world3d import World3D  # noqa: E402


def plot_arms_race(path, gens, pred_skill, prey_skill):
    fig, ax1 = plt.subplots(figsize=(9.5, 5.5))
    ax1.plot(gens, pred_skill, "o-", color="tab:red", lw=2, label="predator hunting (catches vs final prey)")
    ax1.set_xlabel("generation"); ax1.set_ylabel("predator catches", color="tab:red")
    ax1.tick_params(axis="y", labelcolor="tab:red")
    ax2 = ax1.twinx()
    ax2.plot(gens, prey_skill, "s-", color="tab:cyan", lw=2, label="prey evasion (survival vs final predators)")
    ax2.set_ylabel("prey survival rate", color="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:blue")
    ax1.set_title("3D predator-prey arms race (both vs the final opponent)")
    ax1.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--generations", type=int, default=55)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--size", type=float, default=130.0)
    ap.add_argument("--roll-steps", type=int, default=600)
    ap.add_argument("--name", type=str, default="coevo3d")
    args = ap.parse_args()

    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)
    cfg = Coevo3DConfig(world=World3D(size=args.size), generations=args.generations)

    print(f"Co-evolving 3D predators & prey for {args.generations} generations ...")
    result = coevolve3d(cfg, seed=args.seed)
    gens, pred_skill, prey_skill = arms_race_curves3d(result, cfg)
    print(f"  predator hunting vs final prey: {pred_skill[0]:.0f} -> {pred_skill[-1]:.0f}")
    print(f"  prey evasion vs final predators: {prey_skill[0]:.2f} -> {prey_skill[-1]:.2f}")
    plot_arms_race(out / "arms_race3d.png", gens, pred_skill, prey_skill)

    print("Rendering the 3D hunt ...")
    frames = episode3d(result["prey"], result["pred"], cfg, seed=4321, steps=args.roll_steps, record=True)
    renderer = Renderer3D(World3D(size=args.size), width=960, height=720)
    imgs = []
    for i, f in enumerate(frames):
        npp = f["prey_pos"].shape[0]
        pos = np.vstack([f["prey_pos"], f["pred_pos"]])
        vel = np.vstack([f["prey_vel"], f["pred_vel"]])
        col = np.vstack([np.tile([0.35, 0.85, 0.95], (npp, 1)),
                         np.tile([0.95, 0.25, 0.25], (f["pred_pos"].shape[0], 1))])
        imgs.append(renderer.render(pos, vel, col, cam_angle=i * 0.012, food=f["food"]))
    with imageio.get_writer(out / "hunt3d.mp4", fps=30, macro_block_size=1) as w:
        for im in imgs:
            w.append_data(im)
    for fname, idx in {"hunt3d_start.png": 0, "hunt3d_mid.png": len(imgs) // 2, "hunt3d_end.png": len(imgs) - 1}.items():
        imageio.imwrite(out / fname, imgs[idx])
    print(f"  prey alive {frames[0]['prey_pos'].shape[0]} -> {frames[-1]['prey_pos'].shape[0]}")
    print(f"Artifacts in {out}")


if __name__ == "__main__":
    main()
