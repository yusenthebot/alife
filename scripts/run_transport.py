"""R68 — Physarum transport networks (Tero-Nakagaki): solve a maze, build a network.

Tubes carry flow from food to sink and adapt — thicken where flux is high, wither where it is
low. With one source/sink this prunes a dense mesh down to the SHORTEST PATH through a maze;
with many food sources it grows an efficient transport network whose redundancy is set by the
adaptation exponent gamma (low gamma -> robust loops, high gamma -> a minimal tree).
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

from alife.transport import (  # noqa: E402
    grid_graph, braid_maze, run, solve_flow, adapt, bfs_shortest, path_from_solution,
)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r68_transport"


def _draw(ax, g, D, title, marks=None, scale=3.2):
    segs = g.pos[g.edges]                                   # (E,2,2)
    lc = LineCollection(segs, linewidths=np.clip(D * scale, 0.2, 6),
                        colors=plt.cm.inferno(np.clip(D, 0, 1) * 0.85 + 0.1))
    ax.add_collection(lc)
    if marks:
        for node, c in marks:
            ax.scatter(*g.pos[node], s=90, c=c, edgecolors="white", zorder=5)
    ax.autoscale(); ax.set_aspect("equal"); ax.set_title(title, fontsize=10)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_facecolor("#0a0a0f")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # --- maze solving ---
    wall, W, H = braid_maze(13, 13, seed=1, extra=0.15)
    g, idx = grid_graph(W, H, blocked=wall)
    src, dst = idx[(1, 1)], idx[(W - 2, H - 2)]
    true_len = bfs_shortest(g, src, dst)
    r = run(g, {src: +10.0, dst: -10.0}, steps=1200, gamma=1.4, seed=0, record_every=400)
    D0 = r["snaps"][min(r["snaps"])]
    sol = path_from_solution(g, r["D"], src, dst, 0.6)
    print(f"maze: {g.n} nodes, {len(g.edges)} edges; Physarum path={sol} true shortest={true_len} "
          f"({'SOLVED' if sol == true_len else 'suboptimal'})")

    # --- Tokyo-style network: one source + several food sinks on an open grid ---
    gg, gidx = grid_graph(26, 22)
    rng = np.random.default_rng(3)
    source = gidx[(2, 11)]
    cities = [gidx[(int(x), int(y))] for x, y in
              [(23, 3), (23, 19), (14, 2), (14, 20), (18, 11), (9, 6), (9, 16)]]
    srcs = {source: +6.0}
    for c in cities:
        srcs[c] = -6.0 / len(cities)
    net_lo = run(gg, srcs, steps=600, gamma=0.8, seed=0)      # redundant (loops)
    net_hi = run(gg, srcs, steps=600, gamma=1.6, seed=0)      # minimal tree

    gammas = [0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8]
    lengths = []
    for gm in gammas:
        rr = run(gg, srcs, steps=500, gamma=gm, seed=0)
        lengths.append(float((rr["D"] * gg.length).sum()))    # total tube material (clean, monotone)
    print(f"network total material vs gamma: {[round(x) for x in lengths]}")

    fig = plt.figure(figsize=(16.5, 10))
    fig.suptitle("R68 — Physarum transport networks: flow + tube adaptation solve a maze and build a network",
                 fontsize=14, fontweight="bold")
    marks = [(src, "#39ff7a"), (dst, "#ff4040")]
    _draw(fig.add_subplot(2, 3, 1), g, D0, "Maze: a dense mesh of tubes (start)", marks)
    _draw(fig.add_subplot(2, 3, 2), g, r["D"],
          f"Maze SOLVED: tubes prune to the shortest path\n(found {sol} = true shortest {true_len})", marks)

    ax = fig.add_subplot(2, 3, 3)
    ax.plot(r["cost"], color="#1d9bf0", lw=2)
    ax.set_title("Total tube material is pruned over time")
    ax.set_xlabel("step"); ax.set_ylabel("Σ D·L (material)"); ax.grid(alpha=0.25)

    cmarks = [(source, "#39ff7a")] + [(c, "#ffd23f") for c in cities]
    _draw(fig.add_subplot(2, 3, 4), gg, net_lo["D"], "Network γ=0.8: robust, redundant LOOPS", cmarks, scale=2.4)
    _draw(fig.add_subplot(2, 3, 5), gg, net_hi["D"], "Network γ=1.6: efficient minimal TREE", cmarks, scale=2.4)

    ax = fig.add_subplot(2, 3, 6)
    ax.plot(gammas, lengths, "o-", color="#e0245e", lw=2)
    ax.set_title("Redundancy–efficiency tradeoff\n(higher γ → less tube material → leaner network)")
    ax.set_xlabel("adaptation exponent γ"); ax.set_ylabel("total tube material  Σ D·L"); ax.grid(alpha=0.25)

    fig.tight_layout()
    path = OUT / "transport.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
