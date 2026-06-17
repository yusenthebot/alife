"""R30 — novelty search beats the objective on a deceptive maze (Lehman & Stanley).

Minimizing distance-to-goal drives creatures into a U-shaped trap and pins them at
the dead-end wall. Rewarding pure behavioral novelty (no goal knowledge) explores
the maze and escapes around the trap to the goal. Same controller, same arena.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.noveltymaze import (  # noqa: E402
    MazeConfig,
    novelty_search,
    objective_search,
    simulate,
    trajectory,
)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r30_noveltymaze"


def _draw_maze(a, cfg):
    for cx, cy, hw, hh in cfg.walls:
        a.add_patch(Rectangle((cx - hw, cy - hh), 2 * hw, 2 * hh, color="#333", zorder=4))
    a.add_patch(Circle(cfg.goal, cfg.goal_radius, color="#2ecc71", alpha=0.5, zorder=3))
    a.scatter(*cfg.start, c="k", marker="s", s=40, zorder=5)
    a.scatter(*cfg.goal, c="#1b7a3d", marker="*", s=120, zorder=5)
    a.set_xlim(-cfg.reach, cfg.reach); a.set_ylim(-cfg.reach, cfg.reach); a.set_aspect("equal")


def _best_genome(result, cfg):
    """Genome in the final population whose final position is closest to the goal."""
    pos, _ = simulate(result["final_pop"], cfg)
    d = np.linalg.norm(pos - np.array(cfg.goal), axis=1)
    return result["final_pop"][int(np.argmin(d))]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = MazeConfig()

    # a seed where the objective gets trapped (typical), novelty escapes
    nv = novelty_search(cfg, seed=1)
    ob = objective_search(cfg, seed=1)
    print(f"novelty reached={nv['reached_gen']} (best dist {nv['best_dist'].min():.1f}) | "
          f"objective reached={ob['reached_gen']} (best dist {ob['best_dist'].min():.1f})")

    # success rate across seeds
    seeds = range(8)
    nv_ok = sum(novelty_search(cfg, s)["reached_gen"] is not None for s in seeds)
    ob_ok = sum(objective_search(cfg, s)["reached_gen"] is not None for s in seeds)
    print(f"success rate: novelty {nv_ok}/{len(seeds)}, objective {ob_ok}/{len(seeds)}")

    nv_traj = trajectory(_best_genome(nv, cfg), cfg)
    ob_traj = trajectory(_best_genome(ob, cfg), cfg)

    fig, ax = plt.subplots(2, 2, figsize=(13, 12))
    fig.suptitle("R30 — novelty search beats the objective on a deceptive maze",
                 fontsize=15, fontweight="bold")

    a = ax[0, 0]
    _draw_maze(a, cfg)
    a.plot(nv_traj[:, 0], nv_traj[:, 1], color="#1d9bf0", lw=2, label="novelty search (escapes)")
    a.plot(ob_traj[:, 0], ob_traj[:, 1], color="#e0245e", lw=2, label="objective (trapped)")
    a.set_title("The trap: objective gets stuck, novelty goes around")
    a.legend(fontsize=9, loc="lower right")

    a = ax[0, 1]
    gens = np.arange(cfg.generations)
    a.plot(gens, np.minimum.accumulate(nv["best_dist"]), color="#1d9bf0", lw=2, label="novelty search")
    a.plot(gens, np.minimum.accumulate(ob["best_dist"]), color="#e0245e", lw=2, label="objective")
    a.axhline(cfg.goal_radius, color="#2ecc71", lw=1, ls="--", label="goal reached")
    a.set_title("Closest approach to goal (best so far)")
    a.set_xlabel("generation"); a.set_ylabel("min distance to goal"); a.legend(fontsize=9)

    a = ax[1, 0]
    _draw_maze(a, cfg)
    arch = nv["archive"]
    a.scatter(arch[:, 0], arch[:, 1], s=4, c="#1d9bf0", alpha=0.25, zorder=2)
    obp, _ = simulate(ob["final_pop"], cfg)
    a.scatter(obp[:, 0], obp[:, 1], s=10, c="#e0245e", alpha=0.6, zorder=3)
    a.set_title("Where they explored (blue=novelty archive, red=objective pop)")

    a = ax[1, 1]
    a.bar([0], [nv_ok], color="#1d9bf0", width=0.6, label="novelty search")
    a.bar([1], [ob_ok], color="#e0245e", width=0.6, label="objective")
    a.set_xticks([0, 1]); a.set_xticklabels(["novelty", "objective"])
    a.set_ylim(0, len(list(seeds))); a.set_ylabel(f"goal reached (of {len(list(seeds))} seeds)")
    a.set_title("Success rate"); a.legend(fontsize=9)

    fig.tight_layout()
    path = OUT / "noveltymaze.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
