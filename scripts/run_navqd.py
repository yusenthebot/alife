"""R29 — open-ended navigation: MAP-Elites discovers routes around obstacles.

Creatures sense the nearest obstacle and navigate; their behavior is where they
end up. Quality-diversity fills the navigable arena (weaving around walls, reaching
the shadows behind them); objective-only search collapses onto a single spot.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.navqd import (  # noqa: E402
    NavConfig,
    archive_trajectory,
    map_elites,
    objective_ga,
    reachable_mask,
)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r29_navqd"


def _draw_obstacles(a, cfg, color="#333", alpha=1.0):
    for cx, cy, r in cfg.obstacles:
        a.add_patch(Circle((cx, cy), r, color=color, alpha=alpha, zorder=4))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = NavConfig(iters=500)
    g = cfg.grid
    free = reachable_mask(cfg); nfree = int(free.sum())

    archive, cov_me = map_elites(cfg, seed=0)
    obj_pos, cov_obj = objective_ga(cfg, seed=0)

    print(f"MAP-Elites filled={cov_me[-1]} cells ({100*cov_me[-1]/nfree:.0f}% of {nfree} navigable)")
    print(f"objective-only filled={cov_obj[-1]} ({100*cov_obj[-1]/nfree:.0f}%)")

    fig, ax = plt.subplots(2, 2, figsize=(13, 12))
    fig.suptitle("R29 — open-ended navigation: MAP-Elites discovers routes around obstacles",
                 fontsize=15, fontweight="bold")

    # 1) trajectory fan weaving around obstacles
    a = ax[0, 0]
    cells = list(archive.keys())
    rng = np.random.default_rng(2)
    pick = rng.choice(len(cells), size=min(140, len(cells)), replace=False)
    cmap = plt.get_cmap("turbo")
    for k in pick:
        cell = cells[k]
        ang = np.arctan2(archive[cell][2][1], archive[cell][2][0])
        traj = archive_trajectory(archive[cell][1], cfg)
        a.plot(traj[:, 0], traj[:, 1], lw=0.7, alpha=0.6, color=cmap((ang + np.pi) / (2 * np.pi)))
    _draw_obstacles(a, cfg)
    a.scatter([0], [0], c="k", s=25, zorder=5)
    a.set_title("140 discovered routes (weaving around the walls)")
    a.set_xlim(-cfg.reach, cfg.reach); a.set_ylim(-cfg.reach, cfg.reach)
    a.set_aspect("equal"); a.set_xlabel("x"); a.set_ylabel("y")

    # 2) coverage grid takes the shape of the obstacle field
    a = ax[0, 1]
    filled = np.zeros((g, g))
    for c in archive:
        filled[c // g, c % g] = 1.0
    ext = [-cfg.reach, cfg.reach, -cfg.reach, cfg.reach]
    a.imshow(filled.T, origin="lower", extent=ext, cmap="Blues", vmin=0, vmax=1.4)
    _draw_obstacles(a, cfg, color="#c0392b", alpha=0.5)
    a.set_title("Behavior coverage = the navigable space")
    a.set_xlabel("end x"); a.set_ylabel("end y"); a.set_aspect("equal")

    # 3) coverage over search
    a = ax[1, 0]
    its = np.arange(len(cov_me))
    a.plot(its, 100 * cov_me / nfree, color="#1d9bf0", lw=2, label="MAP-Elites (quality-diversity)")
    a.plot(its, 100 * cov_obj / nfree, color="#e0245e", lw=2, label="objective-only GA")
    a.axhline(100, color="k", lw=0.8, ls=":", alpha=0.5)
    a.set_title("Navigable-space coverage over search")
    a.set_xlabel("iteration"); a.set_ylabel("% of navigable cells reached")
    a.set_ylim(0, 115); a.legend(fontsize=9)

    # 4) efficiency map: detours around obstacles cost efficiency
    a = ax[1, 1]
    qgrid = np.full((g, g), np.nan)
    for c, (q, _, _) in archive.items():
        qgrid[c // g, c % g] = q
    im = a.imshow(qgrid.T, origin="lower", extent=ext, cmap="viridis", vmin=0, vmax=1)
    _draw_obstacles(a, cfg, color="#c0392b", alpha=0.6)
    a.set_title("Path efficiency per cell (detours behind walls cost)")
    a.set_xlabel("end x"); a.set_ylabel("end y"); a.set_aspect("equal")
    fig.colorbar(im, ax=a, fraction=0.046, pad=0.04, label="displacement / path-length")

    fig.tight_layout()
    path = OUT / "navqd.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
