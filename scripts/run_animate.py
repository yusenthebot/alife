"""R43 — the animation showcase: watch the living world evolve.

The project's stated wish was to *watch* a pool of little things grow intelligent,
with captivating visuals. Forty rounds of static analysis figures have proven the
science; this renders it as motion. We animate the R33 in-situ ecosystem — brained
creatures foraging, reproducing and dying with no GA — colouring each by its
lineage generation so you can literally watch directed foraging sweep through the
population over time.

Output: runs/r43_animation/ecosystem.gif  (+ a few sample frames as PNG)
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import imageio.v2 as imageio  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.ecosim import EcoConfig, run  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r43_animation"


def _render(snap, cfg, gmax):
    fig = plt.figure(figsize=(6, 6), dpi=90)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("#0b0b16")
    f = snap["food"]
    if len(f):
        ax.scatter(f[:, 0], f[:, 1], s=14, c="#2ecc71", alpha=0.8, zorder=2)
    p = snap["pos"]; h = snap["head"]
    if len(p):
        ax.quiver(p[:, 0], p[:, 1], np.cos(h), np.sin(h), np.clip(snap["gen"], 0, gmax),
                  cmap="plasma", scale=32, width=0.005, zorder=3)
    ax.set_xlim(0, cfg.world); ax.set_ylim(0, cfg.world)
    ax.set_xticks([]); ax.set_yticks([])
    ax.text(0.02, 0.97, f"t={snap['t']}  n={len(p)}  maxgen={int(snap['gen'].max()) if len(p) else 0}",
            transform=ax.transAxes, color="w", fontsize=11, va="top")
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()
    plt.close(fig)
    return buf


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = EcoConfig(steps=6000)
    r = run(cfg, seed=1, record_every=40)
    snaps = r["snaps"]
    gmax = max(1, max(int(s["gen"].max()) if len(s["pos"]) else 0 for s in snaps))
    print(f"{len(snaps)} frames, max lineage gen {gmax}")

    frames = [_render(s, cfg, gmax) for s in snaps]
    gif = OUT / "ecosystem.gif"
    imageio.mimsave(gif, frames, fps=15, loop=0)
    # sample frames for inspection
    for label, idx in [("early", 2), ("mid", len(frames) // 2), ("late", len(frames) - 1)]:
        imageio.imwrite(OUT / f"frame_{label}.png", frames[idx])
    size_kb = gif.stat().st_size / 1024
    print(f"saved {gif} ({size_kb:.0f} KB, {len(frames)} frames)")
    print(f"directedness {np.nanmean(r['directedness'][:5]):+.2f} -> {np.nanmean(r['directedness'][-10:]):+.2f}")


if __name__ == "__main__":
    main()
