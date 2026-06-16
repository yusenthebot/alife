#!/usr/bin/env python
"""Round 3 — evolve neural-network foraging brains, then watch them live.

Three artifacts into runs/<name>/:
  fitness_evolution.png   mean & best foraging fitness per generation (the proof
                          that selection works: a rising curve from random nets)
  behavior.png            a gen-0 random brain vs an evolved brain navigating an
                          identical food field, solo — random wanders, evolved
                          beelines. Behavior, evolved from weights, no rules.
  living_world.mp4 + frames   evolved brains dropped into the continuous
                          ecosystem, hued by how well they head to food
  living_compare.png      in-situ food-seeking of an evolved- vs random-brained
                          world over time

Usage:
  python scripts/run_evolve.py --generations 45 --name evolve
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

from alife import sensors  # noqa: E402
from alife.brain import BrainSpec  # noqa: E402
from alife.evolve import EvolveConfig, evolve  # noqa: E402
from alife.neuro import NeuroConfig, NeuroEcosystem, solo_run  # noqa: E402
from alife.render import Renderer  # noqa: E402
from alife.world import World  # noqa: E402


def behavior_hue(eco: NeuroEcosystem) -> np.ndarray:
    if eco.food.shape[0] == 0:
        return np.full(eco.pos.shape[0], 0.5)
    fr = eco.cfg.world.delta_to(eco.pos, eco.food)
    nearest = fr[np.arange(fr.shape[0]), np.einsum("nfk,nfk->nf", fr, fr).argmin(1)]
    nf = nearest / np.maximum(np.linalg.norm(nearest, axis=1, keepdims=True), 1e-9)
    sp = np.maximum(np.linalg.norm(eco.vel, axis=1, keepdims=True), 1e-9)
    a = (eco.vel / sp * nf).sum(1)
    return (1.0 - (a + 1.0) / 2.0) * 0.66


def plot_fitness(path: Path, hist: np.ndarray) -> None:
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(hist[:, 0], hist[:, 1], "o-", color="tab:purple", lw=2, label="population mean")
    ax.plot(hist[:, 0], hist[:, 2], "-", color="tab:orange", lw=1.5, alpha=0.8, label="best individual")
    ax.axhline(hist[0, 1], color="tab:gray", ls="--", lw=1.2, label="generation 0 (random)")
    ax.set_title("Foraging fitness evolving over generations (food eaten per episode)")
    ax.set_xlabel("generation")
    ax.set_ylabel("food eaten")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def plot_behavior(path: Path, spec, cfg, random_w, evolved_w, steps: int = 340) -> None:
    fig, ax = plt.subplots(1, 2, figsize=(13, 6.4))
    for a, (w, title) in zip(ax, [(random_w, "random brain (generation 0)"), (evolved_w, "evolved brain")]):
        r = solo_run(w, spec, cfg, steps=steps, seed=2024)
        a.scatter(r["food"][:, 0], r["food"][:, 1], s=10, c="tab:green", alpha=0.45, label="food")
        t = r["traj"]
        a.scatter(t[:, 0], t[:, 1], s=4, c=np.arange(len(t)), cmap="plasma")
        a.scatter([t[0, 0]], [t[0, 1]], s=90, marker="*", c="white", edgecolors="k", zorder=5, label="start")
        a.set_title(f"{title}\neaten={r['eaten']}  alignment={r['alignment']:+.2f}")
        a.set_xlim(0, cfg.world.width); a.set_ylim(0, cfg.world.height); a.set_aspect("equal")
        a.legend(loc="upper right", fontsize=8)
    fig.suptitle("Foraging behavior: random vs evolved brain (identical food field, no hand-coded rules)")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def seed_ecosystem(cfg: NeuroConfig, brains: np.ndarray, seed: int) -> NeuroEcosystem:
    eco = NeuroEcosystem(cfg, seed=seed)
    pick = np.random.default_rng(seed).integers(0, brains.shape[0], eco.pos.shape[0])
    eco.brains = brains[pick].copy()
    return eco


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--generations", type=int, default=45)
    ap.add_argument("--pop", type=int, default=160)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--world", type=float, default=200.0)
    ap.add_argument("--live-steps", type=int, default=1400)
    ap.add_argument("--res", type=int, default=900)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--name", type=str, default="evolve")
    args = ap.parse_args()

    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)
    cfg = NeuroConfig(world=World(args.world, args.world, toroidal=True))
    spec = BrainSpec(n_in=sensors.n_inputs(), n_hidden=cfg.hidden, n_out=2)

    print(f"Evolving foraging brains for {args.generations} generations ...")
    brains, hist, gen0 = evolve(spec, cfg, EvolveConfig(pop=args.pop, generations=args.generations), seed=args.seed)
    print(f"  fitness gen0 mean {hist[0,1]:.1f} -> final mean {hist[-1,1]:.1f} (best {hist[-1,2]:.0f})")
    plot_fitness(out / "fitness_evolution.png", hist)

    best = brains[0]                       # elitism keeps the best at index 0
    typ_rand = gen0[gen0.shape[0] // 2]
    plot_behavior(out / "behavior.png", spec, cfg, typ_rand, best)

    # living world: evolved brains in the continuous ecosystem, plus a random
    # control, tracking in-situ food-seeking over time
    print("Rendering living world (evolved brains) ...")
    evo_eco = seed_ecosystem(cfg, brains, seed=7)
    rnd_eco = NeuroEcosystem(cfg, seed=7)
    renderer = Renderer(cfg.world, resolution=args.res, boid_size=2.9)
    frames, evo_align, rnd_align = [], [], []
    marks = {}
    for t in range(args.live_steps):
        evo_align.append(evo_eco.food_alignment())
        rnd_align.append(rnd_eco.food_alignment())
        if t % 6 == 0 and evo_eco.pos.shape[0]:
            frames.append(renderer.eco_frame(evo_eco.pos, evo_eco.vel, behavior_hue(evo_eco), evo_eco.food))
        evo_eco.step(); rnd_eco.step()
        if evo_eco.pos.shape[0] == 0:
            break

    with imageio.get_writer(out / "living_world.mp4", fps=args.fps, macro_block_size=1) as w:
        for f in frames:
            w.append_data(f)
    if frames:
        for fname, idx in {"live_start.png": 0, "live_end.png": len(frames) - 1}.items():
            imageio.imwrite(out / fname, frames[idx])

    fig, ax = plt.subplots(figsize=(9, 5))
    win = 25
    for series, c, lbl in [(evo_align, "tab:red", "evolved brains"), (rnd_align, "tab:gray", "random brains")]:
        s = np.convolve(series, np.ones(win) / win, mode="valid")
        ax.plot(s, color=c, lw=1.6, label=lbl)
    ax.set_title("In-situ food-seeking in the living world (evolved vs random brains)")
    ax.set_xlabel("step"); ax.set_ylabel("food alignment (smoothed)")
    ax.grid(alpha=0.25); ax.legend()
    fig.tight_layout(); fig.savefig(out / "living_compare.png", dpi=110); plt.close(fig)

    print(f"In-situ food alignment (mean over run): evolved {np.mean(evo_align):+.3f}  random {np.mean(rnd_align):+.3f}")
    print(f"Artifacts in {out}")


if __name__ == "__main__":
    main()
