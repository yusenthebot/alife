#!/usr/bin/env python
"""Round 5 — continuous predator–prey ecology (energy, reproduction, death).

Evolves hunt/flee brains (R4), seeds a continuous two-species world with full
lifecycles, and runs it. Artifacts into runs/<name>/:
  populations.png   prey & predator counts over time (boom -> lagged predator
                    boom -> prey crash -> coexistence) + food
  phase_plane.png   predator vs prey trajectory (the Lotka–Volterra portrait:
                    a damped spiral into a stable coexistence point)
  predprey.mp4 + frames   the living world: cyan prey grazing/fleeing, red
                    predators hunting, both breeding and dying

Usage:
  python scripts/run_predprey.py --steps 5000 --name predprey
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

from alife.coevo import CoevoConfig, coevolve  # noqa: E402
from alife.predprey import PredPreyConfig, PredPreyEcosystem  # noqa: E402
from alife.render import Renderer  # noqa: E402
from alife.world import World  # noqa: E402


def plot_populations(path: Path, prey, pred, food) -> None:
    fig, ax1 = plt.subplots(figsize=(11, 5.5))
    t = np.arange(len(prey))
    ax1.plot(t, prey, color="tab:cyan", lw=1.5, label="prey")
    ax1.plot(t, pred, color="tab:red", lw=1.5, label="predators")
    ax1.plot(t, food, color="tab:green", lw=0.8, alpha=0.5, label="plants")
    ax1.set_xlabel("step")
    ax1.set_ylabel("population")
    ax1.set_title("Predator–prey ecology: boom → lagged predator boom → prey crash → coexistence")
    ax1.grid(alpha=0.25)
    ax1.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def plot_phase(path: Path, prey, pred) -> None:
    fig, ax = plt.subplots(figsize=(7, 6.5))
    t = np.arange(len(prey))
    ax.scatter(prey, pred, c=t, cmap="viridis", s=5)
    ax.plot(prey, pred, color="gray", lw=0.4, alpha=0.5)
    ax.set_xlabel("prey population")
    ax.set_ylabel("predator population")
    ax.set_title("Phase plane (color = time): the Lotka–Volterra spiral")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=5000)
    ap.add_argument("--gens", type=int, default=35)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--res", type=int, default=900)
    ap.add_argument("--capture-every", type=int, default=12)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--name", type=str, default="predprey")
    args = ap.parse_args()

    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)

    print(f"Evolving hunt/flee brains ({args.gens} gens) ...")
    cr = coevolve(CoevoConfig(world=World(200, 200, toroidal=True), generations=args.gens), seed=args.seed)
    cfg = PredPreyConfig()
    eco = PredPreyEcosystem(cfg, prey_brains=cr["prey"], pred_brains=cr["pred"], seed=args.seed)
    renderer = Renderer(cfg.world, resolution=args.res, boid_size=2.3)

    prey_s, pred_s, food_s, frames = [], [], [], []
    print(f"Running the ecosystem for {args.steps} steps ...")
    for t in range(args.steps):
        eco.step()
        s = eco.snapshot()
        prey_s.append(s["prey"]); pred_s.append(s["pred"]); food_s.append(s["food"])
        if t % args.capture_every == 0:
            frames.append(renderer.two_species_frame(
                eco.prey["pos"], eco.prey["vel"], eco.pred["pos"], eco.pred["vel"], eco.food))
        if eco.prey["pos"].shape[0] == 0 or eco.pred["pos"].shape[0] == 0:
            print(f"  one species died out at step {t}")
            break

    plot_populations(out / "populations.png", prey_s, pred_s, food_s)
    plot_phase(out / "phase_plane.png", np.array(prey_s), np.array(pred_s))
    with imageio.get_writer(out / "predprey.mp4", fps=args.fps, macro_block_size=1) as w:
        for f in frames:
            w.append_data(f)
    for fname, idx in {"pp_early.png": min(len(frames) - 1, len(frames) // 8),
                       "pp_mid.png": len(frames) // 2, "pp_late.png": len(frames) - 1}.items():
        if frames:
            imageio.imwrite(out / fname, frames[idx])

    pa = np.array(prey_s)
    print(f"survived {len(prey_s)} steps | prey {int(pa[0])}->{int(pa[-1])} "
          f"(coexist range after transient: {int(pa[len(pa)//4:].min())}-{int(pa[len(pa)//4:].max())}) "
          f"| predators {int(pred_s[-1])}")
    print(f"Artifacts in {out}")


if __name__ == "__main__":
    main()
