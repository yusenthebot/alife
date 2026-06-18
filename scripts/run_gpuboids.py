"""R56 — a million boids: field-mediated flocking at megascale on the GPU.

Full circle from R1's ~700 CPU boids. A million GPU agents align through a coarse
grid (Vicsek model): below a critical noise they spontaneously flock (order phi ->
~1); above it, disorder. Same emergent order as R1, a thousandfold bigger.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.gpuboids import BoidsConfig, order_vs_noise, run  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r56_gpuboids"


def _show(a, ag, cfg, title, sub=25000):
    idx = np.linspace(0, len(ag) - 1, min(sub, len(ag))).astype(int)
    p = ag[idx]
    a.quiver(p[:, 0], p[:, 1], np.cos(p[:, 2]), np.sin(p[:, 2]),
             (p[:, 2] % (2 * np.pi)), cmap="hsv", scale=60, width=0.002, alpha=0.7)
    a.set_title(title); a.set_xlim(0, cfg.world); a.set_ylim(0, cfg.world)
    a.set_aspect("equal"); a.set_xticks([]); a.set_yticks([])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = BoidsConfig(n_agents=1_000_000, grid=64, noise=0.1)
    early = run(cfg, steps=30, seed=0)
    late = run(cfg, steps=600, seed=0, record_every=40)
    print(f"1M boids: order {early['order']:.2f} (t=30) -> {late['order']:.2f} (t=600), "
          f"{int(late['steps_per_s'])} steps/s")

    nz = np.round(np.arange(0.05, 0.86, 0.1), 2)
    ov = order_vs_noise(BoidsConfig(n_agents=400_000, grid=64), nz, steps=800)
    print(f"phase transition order: {dict(zip(nz.tolist(), np.round(ov,2).tolist()))}")

    fig, ax = plt.subplots(2, 2, figsize=(13, 12))
    fig.suptitle("R56 — a million boids: field-mediated flocking at megascale (GPU Vicsek)",
                 fontsize=14, fontweight="bold")
    _show(ax[0, 0], early["agents"], cfg, f"t=30: disordered (order φ={early['order']:.2f})")
    _show(ax[0, 1], late["agents"], cfg, f"t=600: flocked (order φ={late['order']:.2f})")

    a = ax[1, 0]
    oh = late["order_hist"]
    a.plot(oh[:, 0], oh[:, 1], "o-", color="#1b7a3d", lw=2)
    a.set_title("Global order emerges in 1,000,000 agents")
    a.set_xlabel("step"); a.set_ylabel("order parameter φ"); a.set_ylim(0, 1.05)

    a = ax[1, 1]
    a.plot(nz, ov, "o-", color="#1d9bf0", lw=2)
    a.set_title("The Vicsek order-disorder phase transition")
    a.set_xlabel("noise"); a.set_ylabel("steady order φ"); a.set_ylim(0, 1.05)

    fig.tight_layout()
    path = OUT / "gpuboids.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
