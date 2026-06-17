#!/usr/bin/env python
"""Round 14 — the large-scale living world: thousands of creatures in one 3D volume.

Evolves 3D hunt/flee brains, seeds a KD-tree-accelerated continuous ecosystem,
runs it at scale, and renders it with the atmospheric GPU renderer.

Artifacts into runs/<name>/:
  bigworld.mp4 + frames   ~10k cyan prey + red predators + green food, living in 3D
  bigpop.png              populations over time
Usage:
  python scripts/run_bigworld3d.py --steps 2200 --name bigworld
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

from alife.bigworld3d import BigWorld3D  # noqa: E402
from alife.coevo3d import Coevo3DConfig, coevolve3d  # noqa: E402
from alife.render3d import Renderer3D  # noqa: E402
from alife.world3d import World3D  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=2200)
    ap.add_argument("--gens", type=int, default=22)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--capture-every", type=int, default=8)
    ap.add_argument("--name", type=str, default="bigworld")
    args = ap.parse_args()

    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)

    print(f"Evolving 3D hunt/flee brains ({args.gens} gens) ...")
    cr = coevolve3d(Coevo3DConfig(world=World3D(size=120.0), generations=args.gens), seed=args.seed)
    eco = BigWorld3D(prey_brains=cr["prey"], pred_brains=cr["pred"], seed=args.seed)
    renderer = Renderer3D(eco.cfg.world, width=960, height=720, scale=1.1)

    prey_s, pred_s, food_s, imgs = [], [], [], []
    print(f"Running the large-scale world for {args.steps} steps ...")
    for t in range(args.steps):
        eco.step()
        s = eco.snapshot()
        prey_s.append(s["prey"]); pred_s.append(s["pred"]); food_s.append(s["food"])
        if t % args.capture_every == 0 and eco.prey["pos"].shape[0]:
            npp = eco.prey["pos"].shape[0]
            pos = np.vstack([eco.prey["pos"], eco.pred["pos"]])
            vel = np.vstack([eco.prey["vel"], eco.pred["vel"]])
            col = np.vstack([np.tile([0.35, 0.85, 0.95], (npp, 1)),
                             np.tile([0.97, 0.25, 0.25], (eco.pred["pos"].shape[0], 1))])
            imgs.append(renderer.render(pos, vel, col, cam_angle=t * 0.005, food=eco.food, radius_mult=1.5))
        if eco.prey["pos"].shape[0] == 0 or eco.pred["pos"].shape[0] == 0:
            print(f"  a species died out at step {t}"); break

    with imageio.get_writer(out / "bigworld.mp4", fps=30, macro_block_size=1) as w:
        for im in imgs:
            w.append_data(im)
    for fname, idx in {"bigworld_early.png": min(len(imgs) - 1, 10),
                       "bigworld_mid.png": len(imgs) // 2, "bigworld_late.png": len(imgs) - 1}.items():
        if imgs:
            imageio.imwrite(out / fname, imgs[idx])

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(prey_s, color="tab:cyan", lw=1.4, label="prey")
    ax.plot(pred_s, color="tab:red", lw=1.4, label="predators")
    ax.plot(food_s, color="tab:green", lw=0.8, alpha=0.5, label="food")
    ax.set_title("Large-scale 3D ecosystem: populations over time")
    ax.set_xlabel("step"); ax.set_ylabel("count"); ax.grid(alpha=0.25); ax.legend()
    fig.tight_layout(); fig.savefig(out / "bigpop.png", dpi=110); plt.close(fig)

    print(f"survived {len(prey_s)} steps | prey {int(prey_s[0])}->{int(prey_s[-1])} "
          f"predators {int(pred_s[0])}->{int(pred_s[-1])} | peak creatures {int(max(np.array(prey_s)+np.array(pred_s)))}")
    print(f"Artifacts in {out}")


if __name__ == "__main__":
    main()
