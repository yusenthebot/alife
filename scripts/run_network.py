"""R83 — Network science: scale-free networks from preferential attachment, and their Achilles heel.

Growth + preferential attachment (Barabasi-Albert) yields a scale-free degree distribution with
giant hubs, unlike an Erdos-Renyi random graph's bell-shaped Poisson. Scale-free nets are robust
to random failure but fragile to a targeted attack on the hubs; random graphs degrade alike.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.network import (  # noqa: E402
    ba_graph, er_graph, degrees, ccdf, powerlaw_exponent, attack_curve, spring_layout,
)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r83_network"


def _draw(ax, edges, n, title, color):
    pos = spring_layout(edges, n, iters=250, seed=1)
    deg = degrees(edges, n)
    seg = pos[edges]
    ax.add_collection(LineCollection(seg, colors="#888", linewidths=0.3, alpha=0.5))
    ax.scatter(pos[:, 0], pos[:, 1], s=8 + 2.2 * deg, c=color, edgecolors="white", linewidths=0.3, zorder=3)
    ax.set_title(title, fontsize=10); ax.set_xticks([]); ax.set_yticks([]); ax.autoscale()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    n, m = 4000, 2
    ba = ba_graph(n, m, seed=0)
    er = er_graph(n, len(ba), seed=0)
    eb = powerlaw_exponent(ba, n); ee = powerlaw_exponent(er, n)
    db, de = degrees(ba, n), degrees(er, n)
    print(f"BA: CCDF slope {eb:.2f} (scale-free ~ -2), max degree {db.max()} (hub)")
    print(f"ER: CCDF slope {ee:.2f} (steep, no heavy tail), max degree {de.max()}")

    fig = plt.figure(figsize=(16.5, 10))
    fig.suptitle("R83 — Network science: scale-free networks (preferential attachment) and their Achilles heel",
                 fontsize=14, fontweight="bold")

    ax = fig.add_subplot(2, 3, 1)
    kb, cb = ccdf(ba, n); ke, ce = ccdf(er, n)
    ax.loglog(kb, cb, "o-", color="#e0245e", ms=3, lw=1, label=f"Barabasi-Albert (slope {eb:.1f})")
    ax.loglog(ke, ce, "o-", color="#1d9bf0", ms=3, lw=1, label="Erdos-Renyi (random)")
    ax.set_title("Degree distribution P(K≥k): BA is a power law\n(scale-free), ER falls off fast (Poisson)")
    ax.set_xlabel("degree k"); ax.set_ylabel("P(K ≥ k)"); ax.legend(fontsize=8); ax.grid(alpha=0.25, which="both")

    nv = 160
    _draw(fig.add_subplot(2, 3, 2), ba_graph(nv, m, seed=0), nv, "Barabasi-Albert: a few giant HUBS", "#e0245e")
    _draw(fig.add_subplot(2, 3, 3), er_graph(nv, nv * m, seed=0), nv, "Erdos-Renyi: homogeneous, no hubs", "#1d9bf0")

    fr = np.linspace(0, 0.5, 21)
    for col, (edges, name) in enumerate([(ba, "Barabasi-Albert (scale-free)"), (er, "Erdos-Renyi (random)")]):
        ax = fig.add_subplot(2, 3, 4 + col)
        ax.plot(fr, attack_curve(edges, n, fr, "random", seed=1), color="#1f7a1f", lw=2, label="random failure")
        ax.plot(fr, attack_curve(edges, n, fr, "targeted"), color="#e0245e", lw=2, label="targeted (hubs first)")
        ax.set_title(f"{name}:\n" + ("robust to random, FRAGILE to hub attack" if col == 0 else "degrades similarly either way"))
        ax.set_xlabel("fraction of nodes removed"); ax.set_ylabel("giant component fraction")
        ax.set_ylim(0, 1.02); ax.legend(fontsize=8); ax.grid(alpha=0.25)

    ax = fig.add_subplot(2, 3, 6)
    f15 = 0.15
    vals = [attack_curve(ba, n, [f15], "random", seed=1)[0], attack_curve(ba, n, [f15], "targeted")[0],
            attack_curve(er, n, [f15], "random", seed=1)[0], attack_curve(er, n, [f15], "targeted")[0]]
    ax.bar(["BA\nrandom", "BA\ntargeted", "ER\nrandom", "ER\ntargeted"], vals,
           color=["#1f7a1f", "#e0245e", "#7ab96f", "#f06e85"])
    ax.set_title(f"Giant component after removing {f15:.0%} of nodes\n(only BA-targeted collapses)")
    ax.set_ylabel("giant component fraction"); ax.set_ylim(0, 1.02)

    fig.tight_layout()
    path = OUT / "network.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
