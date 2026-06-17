#!/usr/bin/env python
"""Round 8 — evolved 3D foraging brains, flown through the GPU renderer.

Evolves 3D foragers (R3's GA in 3D), checks they generalize to a held-out food
field, then renders a living 3D ecosystem of the evolved swarm chasing food.

Artifacts into runs/<name>/:
  fitness3d.png    foraging fitness over generations (random -> competent)
  eco3d.mp4 + frames   evolved foragers (hued by heading) hunting green food in 3D
Usage:
  python scripts/run_evolve3d.py --generations 45 --name evolve3d
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

import imageio.v2 as imageio
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alife.evolve3d import Forage3DConfig, batch_forage3d, evolve3d, rollout3d_shared, spec  # noqa: E402
from alife.render3d import Renderer3D  # noqa: E402
from alife.world3d import World3D  # noqa: E402


def hue_rgb(vel):
    h = (np.arctan2(vel[:, 1], vel[:, 0]) / (2 * np.pi)) % 1.0
    i = np.floor(h * 6).astype(int)
    f = h * 6 - i
    v, s = 1.0, 0.85
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    i = i % 6
    return np.stack([np.choose(i, [v, q, p, p, t, v]),
                     np.choose(i, [t, v, v, q, p, p]),
                     np.choose(i, [p, p, t, v, v, q])], axis=1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--generations", type=int, default=45)
    ap.add_argument("--pop", type=int, default=160)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--size", type=float, default=130.0)
    ap.add_argument("--roll-n", type=int, default=320)
    ap.add_argument("--roll-steps", type=int, default=600)
    ap.add_argument("--name", type=str, default="evolve3d")
    args = ap.parse_args()

    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)
    world = World3D(size=args.size)
    cfg = replace(Forage3DConfig(), world=world, pop=args.pop, generations=args.generations)

    print(f"Evolving 3D foragers for {args.generations} generations ...")
    brains, hist, gen0, sp = evolve3d(cfg, seed=args.seed)
    rand = batch_forage3d(gen0[:24], sp, replace(cfg, eval_steps=300), 300, seed=99999).mean()
    evo = batch_forage3d(brains[:24], sp, replace(cfg, eval_steps=300), 300, seed=99999).mean()
    print(f"  fitness gen0 {hist[0,1]:.1f} -> final {hist[-1,1]:.1f} | held-out random {rand:.1f} -> evolved {evo:.1f}")

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(hist[:, 0], hist[:, 1], "o-", color="tab:purple", lw=2, label="mean")
    ax.plot(hist[:, 0], hist[:, 2], color="tab:orange", lw=1.5, label="best")
    ax.axhline(hist[0, 1], color="gray", ls="--", lw=1, label="gen 0 (random)")
    ax.set_title("3D foraging fitness over generations")
    ax.set_xlabel("generation"); ax.set_ylabel("food eaten"); ax.grid(alpha=0.25); ax.legend()
    fig.tight_layout(); fig.savefig(out / "fitness3d.png", dpi=110); plt.close(fig)

    print("Rendering the evolved 3D ecosystem ...")
    # tile evolved brains up to roll_n agents for a fuller swarm
    pick = np.resize(np.arange(brains.shape[0]), args.roll_n)
    frames_data = rollout3d_shared(brains[pick], sp, replace(cfg, n_food=500), args.roll_steps, seed=7)
    renderer = Renderer3D(world, width=960, height=720)
    imgs = [renderer.render(f["pos"], f["vel"], hue_rgb(f["vel"]), cam_angle=i * 0.012, food=f["food"])
            for i, f in enumerate(frames_data)]
    with imageio.get_writer(out / "eco3d.mp4", fps=30, macro_block_size=1) as w:
        for im in imgs:
            w.append_data(im)
    for fname, idx in {"eco3d_start.png": 0, "eco3d_mid.png": len(imgs) // 2, "eco3d_end.png": len(imgs) - 1}.items():
        imageio.imwrite(out / fname, imgs[idx])
    print(f"Artifacts in {out}")


if __name__ == "__main__":
    main()
