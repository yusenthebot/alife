"""R65 — Ant-colony foraging: stigmergy builds a trail and finds the shortest path.

A spatial colony self-organises a foraging highway between nest and food from purely local
deposit-and-follow rules; the abstract Deneubourg double-bridge shows the colony converging
on the SHORTER of two routes (and, for equal routes, breaking symmetry at random).
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.antcolony import AntConfig, simulate, trail_strength, deneubourg_bridge  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r65_antcolony"


def _show_trail(ax, trail, x, y, nest, foods, title):
    ax.imshow(np.log1p(trail), cmap="inferno", origin="lower")
    ax.scatter(x, y, s=1.2, c="#39d0ff", alpha=0.35)
    ax.scatter(*nest, s=90, c="#39ff7a", marker="s", edgecolors="white", label="nest")
    for fx, fy in foods:
        ax.scatter(fx, fy, s=110, c="#ff4040", marker="*", edgecolors="white")
    ax.set_title(title, fontsize=10); ax.axis("off")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = AntConfig(size=200, n_ants=500)
    r = simulate(cfg, steps=1500, seed=0, record_every=500)
    keys = sorted(r["snaps"])
    on = trail_strength(r["trail"], r["nest"], r["foods"][0])
    off = trail_strength(r["trail"], r["nest"], np.array([20.0, 100.0]))
    print(f"spatial: delivered={r['delivered'][-1]}, trail corridor={on:.1f} vs off-axis={off:.1f}")

    ratios = [1.25, 1.5, 2.0]
    bridges = {ro: deneubourg_bridge(1.0, ro, steps=400, seed=0) for ro in ratios}
    eq = [deneubourg_bridge(1.0, 1.0, steps=400, seed=s) for s in range(8)]
    print(f"short-path P end: {[round(bridges[ro][-1],2) for ro in ratios]}; "
          f"equal-bridge ends: {[round(e[-1],2) for e in eq]}")

    fig = plt.figure(figsize=(16.5, 10))
    fig.suptitle("R65 — Ant-colony foraging: stigmergy builds a trail and finds the shortest path",
                 fontsize=14, fontweight="bold")
    titles = ["t=0: ants leave the nest, no trail", "trail self-organizes", "a focused foraging highway"]
    for c in range(3):
        ax = fig.add_subplot(2, 3, c + 1)
        tr, x, y, lad = r["snaps"][keys[c]]
        _show_trail(ax, tr, x, y, r["nest"], r["foods"], f"{titles[c]} (t={keys[c]})")

    ax = fig.add_subplot(2, 3, 4)
    d = r["delivered"]
    ax.plot(d, color="#1d9bf0", lw=2)
    ax.set_title(f"Foraging accelerates as the trail forms\n({d[-1]} food delivered)")
    ax.set_xlabel("step"); ax.set_ylabel("cumulative food delivered"); ax.grid(alpha=0.25)

    ax = fig.add_subplot(2, 3, 5)
    for ro in ratios:
        ax.plot(bridges[ro], lw=2, label=f"long/short = {ro}")
    ax.axhline(0.5, color="#9aa0a6", ls=":", lw=1)
    ax.set_title("Double bridge: colony locks onto the SHORT path")
    ax.set_xlabel("step"); ax.set_ylabel("P(choose short path)"); ax.set_ylim(0, 1.03)
    ax.legend(fontsize=8); ax.grid(alpha=0.25)

    ax = fig.add_subplot(2, 3, 6)
    for e in eq:
        ax.plot(e, color="#e0245e", lw=1, alpha=0.6)
    ax.axhline(0.5, color="#9aa0a6", ls=":", lw=1)
    ax.set_title("Equal-length control: symmetry breaks at RANDOM\n(each colony fixates on one arm)")
    ax.set_xlabel("step"); ax.set_ylabel("P(choose arm A)"); ax.set_ylim(0, 1.03); ax.grid(alpha=0.25)

    fig.tight_layout()
    path = OUT / "antcolony.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
