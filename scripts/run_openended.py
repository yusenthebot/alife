"""R28 — open-endedness: MAP-Elites illuminates a behavior space.

Discovers a diverse repertoire of movement styles (straight sprinters -> loopy
wanderers, in every direction) instead of optimizing one objective. Contrasts
quality-diversity (fills the behavior grid) against objective-only search (collapses).
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.cm as cm  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.openended import (  # noqa: E402
    OpenEndedConfig,
    archive_trajectory,
    map_elites,
    objective_ga,
)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r28_openended"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = OpenEndedConfig(iters=400)
    g = cfg.grid
    total = g * g

    archive, cov_me = map_elites(cfg, seed=0)
    obj_pos, obj_curv, cov_obj = objective_ga(cfg, seed=0)

    print(f"MAP-Elites coverage={cov_me[-1]}/{total} ({100*cov_me[-1]/total:.0f}%) "
          f"QD-score={sum(v[0] for v in archive.values()):.0f}")
    print(f"objective-only coverage={cov_obj[-1]}/{total} ({100*cov_obj[-1]/total:.0f}%)")

    # reconstruct the quality grid from the archive
    qgrid = np.full((g, g), np.nan)
    for cell, (q, _, _) in archive.items():
        qgrid[cell // g, cell % g] = q

    fig, ax = plt.subplots(2, 2, figsize=(13, 11))
    fig.suptitle("R28 — open-endedness: MAP-Elites illuminates a behavior space",
                 fontsize=15, fontweight="bold")

    a = ax[0, 0]
    im = a.imshow(qgrid.T, origin="lower", aspect="auto", cmap="viridis",
                  extent=[-180, 180, 0, cfg.curv_max])
    a.set_title("Illuminated map: reach (quality) per behavior style")
    a.set_xlabel("final heading (deg)"); a.set_ylabel("path curviness (rad/step)")
    fig.colorbar(im, ax=a, fraction=0.046, pad=0.04, label="displacement (norm)")

    a = ax[0, 1]
    # sample archived elites across the grid and replay their trajectories
    cells = list(archive.keys())
    rng = np.random.default_rng(1)
    pick = rng.choice(len(cells), size=min(160, len(cells)), replace=False)
    cmap = plt.get_cmap("plasma")
    for k in pick:
        cell = cells[k]
        ci = cell % g
        traj = archive_trajectory(archive[cell][1], cfg)
        a.plot(traj[:, 0], traj[:, 1], lw=0.7, alpha=0.6, color=cmap(ci / g))
    a.scatter([0], [0], c="k", s=20, zorder=5)
    a.set_title("The repertoire: 160 discovered movement styles")
    a.set_xlabel("x"); a.set_ylabel("y"); a.set_aspect("equal")
    sm = cm.ScalarMappable(cmap=cmap); sm.set_array([0, cfg.curv_max])
    fig.colorbar(sm, ax=a, fraction=0.046, pad=0.04, label="curviness")

    a = ax[1, 0]
    its = np.arange(len(cov_me))
    a.plot(its, 100 * cov_me / total, color="#1d9bf0", lw=2, label="MAP-Elites (quality-diversity)")
    a.plot(its, 100 * cov_obj / total, color="#e0245e", lw=2, label="objective-only GA")
    a.set_title("Behavior-space coverage over search")
    a.set_xlabel("iteration"); a.set_ylabel("% of behavior grid filled")
    a.set_ylim(0, 105); a.legend(fontsize=9)

    a = ax[1, 1]
    # objective-only collapses to one behavior; ME fills it
    me_ang = np.array([(c // g) / g * 360 - 180 for c in archive])
    me_cv = np.array([(c % g) / g * cfg.curv_max for c in archive])
    a.scatter(me_ang, me_cv, s=8, c="#1d9bf0", alpha=0.4, label="MAP-Elites archive")
    obj_ang = np.degrees(np.arctan2(obj_pos[:, 1], obj_pos[:, 0]))
    a.scatter(obj_ang, np.clip(obj_curv, 0, cfg.curv_max), s=18, c="#e0245e",
              alpha=0.7, label="objective-only final pop")
    a.set_title("Objective-only collapses; QD fills the space")
    a.set_xlabel("final heading (deg)"); a.set_ylabel("path curviness"); a.legend(fontsize=9)

    fig.tight_layout()
    path = OUT / "openended.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
