#!/usr/bin/env python
"""Round 7 — 3D flocking, rendered on the GPU. The visual summit begins.

Lifts R1 flocking into a 3D arena and renders it with moderngl (lit instanced
cones, orbiting camera, ground grid). Outputs into runs/<name>/:
  flock3d.mp4          orbiting view of the 3D murmuration
  flock3d_*.png        key frames (start scatter -> ordered flock)
  order3d.png          3D order parameter over time

Usage:
  python scripts/run_boids3d.py --n 900 --steps 600 --name flock3d
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

from alife import boids3d  # noqa: E402
from alife.boids3d import Boid3DParams  # noqa: E402
from alife.render3d import Renderer3D  # noqa: E402
from alife.world3d import World3D  # noqa: E402


def hue_rgb(vel: np.ndarray) -> np.ndarray:
    """Per-agent color (N,3 float) from heading azimuth — aligned flock = one hue."""
    h = (np.arctan2(vel[:, 1], vel[:, 0]) / (2 * np.pi)) % 1.0
    i = np.floor(h * 6).astype(int)
    f = h * 6 - i
    v, s = 1.0, 0.85
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    i = i % 6
    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])
    return np.stack([r, g, b], axis=1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=900)
    ap.add_argument("--steps", type=int, default=600)
    ap.add_argument("--size", type=float, default=130.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--w", type=int, default=960)
    ap.add_argument("--h", type=int, default=720)
    ap.add_argument("--capture-every", type=int, default=2)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--name", type=str, default="flock3d")
    args = ap.parse_args()

    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)
    world = World3D(size=args.size)
    p = Boid3DParams()
    rng = np.random.default_rng(args.seed)
    pos, vel = boids3d.spawn(world, args.n, p, rng)
    renderer = Renderer3D(world, width=args.w, height=args.h)

    frames, order = [], []
    print(f"3D flocking: {args.n} boids x {args.steps} steps ...")
    for t in range(args.steps):
        order.append(boids3d.order_parameter(vel))
        if t % args.capture_every == 0:
            frames.append(renderer.render(pos, vel, hue_rgb(vel), cam_angle=t * 0.012))
        pos, vel = boids3d.step(world, p, pos, vel)

    print("Writing flock3d.mp4 ...")
    with imageio.get_writer(out / "flock3d.mp4", fps=args.fps, macro_block_size=1) as w:
        for f in frames:
            w.append_data(f)
    for fname, idx in {"flock3d_start.png": 0, "flock3d_mid.png": len(frames) // 2,
                       "flock3d_end.png": len(frames) - 1}.items():
        imageio.imwrite(out / fname, frames[idx])

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(order, color="tab:cyan", lw=1.5)
    ax.set_title("3D flocking order parameter")
    ax.set_xlabel("step"); ax.set_ylabel("φ"); ax.set_ylim(0, 1); ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(out / "order3d.png", dpi=110); plt.close(fig)

    print(f"order parameter: {order[0]:.3f} -> {order[-1]:.3f}")
    print(f"Artifacts in {out}")


if __name__ == "__main__":
    main()
