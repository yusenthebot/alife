"""R55 — GPU Physarum: a million slime-mold agents self-organize into networks.

A million memoryless agents, coupled only through a shared chemical trail
(stigmergy), grow the branching transport networks of Physarum polycephalum —
entirely on the GPU compute substrate from R54.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.gpuslime import SlimeConfig, run  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r55_gpuslime"


def _show(a, trail, title):
    a.imshow(np.sqrt(trail), cmap="magma", interpolation="bilinear")
    a.set_title(title); a.set_xticks([]); a.set_yticks([])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = SlimeConfig(n_agents=1_000_000)
    r = run(cfg, steps=700, seed=0, record_every=60)
    snaps, struct = r["snaps"], r["structure"]
    keys = sorted(snaps)
    early, late = keys[1], keys[-1]
    print(f"1M agents, {cfg.width}^2: {int(r['steps_per_s'])} steps/s")
    print(f"structure ratio std/mean: {struct[0,1]:.2f} (t={int(struct[0,0])}) -> {struct[-1,1]:.2f} (t={int(struct[-1,0])})")

    # throughput vs agent count
    counts = [250_000, 1_000_000, 4_000_000]
    sps = []
    for n in counts:
        _, rate = run(SlimeConfig(n_agents=n), steps=200, seed=0, measure=True)
        sps.append(rate)
        print(f"  {n:,} agents: {int(rate)} steps/s")

    fig, ax = plt.subplots(2, 2, figsize=(13, 12))
    fig.suptitle("R55 — GPU Physarum: 1,000,000 slime-mold agents grow transport networks",
                 fontsize=14, fontweight="bold")
    _show(ax[0, 0], snaps[early], f"early (t={early}): a diffuse cloud")
    _show(ax[0, 1], snaps[late], f"late (t={late}): emergent branching network")

    a = ax[1, 0]
    a.plot(struct[:, 0], struct[:, 1], "o-", color="#e0245e", lw=2)
    a.set_title("Self-organization: trail structure rises (filaments form)")
    a.set_xlabel("step"); a.set_ylabel("structure ratio  std/mean")

    a = ax[1, 1]
    a.plot(counts, sps, "o-", color="#1d9bf0", lw=2)
    a.set_xscale("log"); a.set_title("GPU throughput vs agent count")
    a.set_xlabel("agents (log)"); a.set_ylabel("steps / second")
    a.text(0.02, 0.05, f"4,000,000 agents @ {int(sps[-1])} steps/s\nstigmergy only — no neighbour search",
           transform=a.transAxes, fontsize=8)

    fig.tight_layout()
    path = OUT / "gpuslime.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
