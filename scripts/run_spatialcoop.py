"""R38 — spatial reciprocity: cooperation survives by clustering (Nowak & May 1992).

A lattice prisoner's dilemma. On the grid, cooperators form clusters and persist;
reshuffle the players each step (well-mixed) and cooperation collapses to zero.
Same game, same temptation — only locality differs.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.spatialcoop import SpatialCoopConfig, b_sweep, run  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r38_spatialcoop"
CMAP = mcolors.ListedColormap(["#1a1a2e", "#1d9bf0"])   # defector dark, cooperator blue


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = SpatialCoopConfig()
    sp = run(cfg, well_mixed=False, seed=0)
    wm = run(cfg, well_mixed=True, seed=0)

    bs = np.round(np.arange(1.3, 2.01, 0.1), 2)
    sweep = b_sweep(cfg, bs)

    print(f"spatial coop final {np.mean(sp['coop_fraction'][-30:]):.2f} | "
          f"well-mixed {np.mean(wm['coop_fraction'][-30:]):.3f}")
    print(f"b-sweep (spatial): {dict(zip(bs.tolist(), np.round(sweep, 2).tolist()))}")

    fig, ax = plt.subplots(2, 2, figsize=(13, 11))
    fig.suptitle("R38 — spatial reciprocity: cooperation survives by clustering (Nowak-May)",
                 fontsize=14, fontweight="bold")

    a = ax[0, 0]
    a.plot(sp["coop_fraction"], color="#1d9bf0", lw=2, label="lattice (spatial)")
    a.plot(wm["coop_fraction"], color="#e0245e", lw=2, label="reshuffled (well-mixed)")
    a.set_title(f"Cooperation persists on the lattice, collapses well-mixed (b={cfg.b})")
    a.set_xlabel("round"); a.set_ylabel("cooperator fraction"); a.set_ylim(0, 1); a.legend(fontsize=9)

    a = ax[0, 1]
    a.plot(bs, sweep, "o-", color="#1d9bf0", lw=2, label="lattice")
    a.axhline(0, color="#e0245e", lw=1.5, ls="--", label="well-mixed (→0)")
    a.set_title("Steady cooperation vs temptation b")
    a.set_xlabel("temptation b"); a.set_ylabel("steady cooperator fraction"); a.legend(fontsize=9)

    a = ax[1, 0]
    a.imshow(sp["snaps"][cfg.steps], cmap=CMAP, vmin=0, vmax=1, interpolation="nearest")
    a.set_title(f"Lattice at t={cfg.steps}: cooperator clusters (blue) persist")
    a.set_xticks([]); a.set_yticks([])

    a = ax[1, 1]
    a.imshow(wm["snaps"][cfg.steps], cmap=CMAP, vmin=0, vmax=1, interpolation="nearest")
    a.set_title(f"Well-mixed at t={cfg.steps}: cooperation wiped out")
    a.set_xticks([]); a.set_yticks([])

    fig.tight_layout()
    path = OUT / "spatialcoop.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
