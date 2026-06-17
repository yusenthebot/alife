#!/usr/bin/env python
"""Round 13 — a vast 3D murmuration (10k+ agents via a spatial index).

Breaks the O(N²) ceiling with a KD-tree so tens of thousands of creatures flock,
rendered with the atmospheric GPU renderer.

Artifacts into runs/<name>/:
  swarm3d.mp4 + frames   the giant murmuration, orbiting camera
  order_swarm3d.png      order parameter over time
Usage:
  python scripts/run_swarm3d.py --n 12000 --steps 500 --name swarm3d
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import imageio.v2 as imageio
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alife import swarm3d  # noqa: E402
from alife.render3d import Renderer3D  # noqa: E402
from alife.swarm3d import Swarm3DParams  # noqa: E402
from alife.world3d import World3D  # noqa: E402


def hue_rgb(vel):
    h = (np.arctan2(vel[:, 1], vel[:, 0]) / (2 * np.pi)) % 1.0
    i = np.floor(h * 6).astype(int); f = h * 6 - i; v, s = 1.0, 0.85
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f)); i = i % 6
    return np.stack([np.choose(i, [v, q, p, p, t, v]),
                     np.choose(i, [t, v, v, q, p, p]),
                     np.choose(i, [p, p, t, v, v, q])], axis=1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12000)
    ap.add_argument("--steps", type=int, default=500)
    ap.add_argument("--size", type=float, default=160.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--capture-every", type=int, default=2)
    ap.add_argument("--name", type=str, default="swarm3d")
    args = ap.parse_args()

    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)
    world = World3D(size=args.size)
    p = Swarm3DParams()
    rng = np.random.default_rng(args.seed)
    pos, vel = swarm3d.spawn(world, args.n, p, rng)
    renderer = Renderer3D(world, width=960, height=720, scale=1.1)

    frames, order = [], []
    print(f"Vast murmuration: {args.n} agents x {args.steps} steps ...")
    t0 = time.time()
    for t in range(args.steps):
        order.append(swarm3d.order_parameter(vel))
        if t % args.capture_every == 0:
            frames.append(renderer.render(pos, vel, hue_rgb(vel), cam_angle=t * 0.01, radius_mult=1.5))
        pos, vel = swarm3d.step(world, p, pos, vel)
    print(f"  sim+render {time.time()-t0:.0f}s ({1000*(time.time()-t0)/args.steps:.0f} ms/step)")

    with imageio.get_writer(out / "swarm3d.mp4", fps=30, macro_block_size=1) as w:
        for f in frames:
            w.append_data(f)
    for fname, idx in {"swarm3d_start.png": 0, "swarm3d_mid.png": len(frames) // 2, "swarm3d_end.png": len(frames) - 1}.items():
        imageio.imwrite(out / fname, frames[idx])

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(order, color="tab:cyan", lw=1.5); ax.set_ylim(0, 1); ax.grid(alpha=0.25)
    ax.set_title(f"Order parameter — {args.n}-agent 3D murmuration"); ax.set_xlabel("step")
    fig.tight_layout(); fig.savefig(out / "order_swarm3d.png", dpi=110); plt.close(fig)

    print(f"order {order[0]:.3f} -> {order[-1]:.3f} | Artifacts in {out}")


if __name__ == "__main__":
    main()
