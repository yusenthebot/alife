"""R39 — rock-paper-scissors: space keeps biodiversity alive.

On a lattice the three non-transitive species form rotating spiral waves and
coexist; well-mixed, one species fixates and diversity dies. Same game, only
locality differs.
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

from alife.rps import RPSConfig, diversity, run  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r39_rps"
CMAP = mcolors.ListedColormap(["#e0245e", "#1d9bf0", "#f5c518"])   # rock / paper / scissors


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = RPSConfig()
    sp = run(cfg, well_mixed=False, seed=0)
    wm = run(cfg, well_mixed=True, seed=0)
    print(f"lattice min-species {diversity(sp):.3f} (coexist) | well-mixed {diversity(wm):.3f} (fixation)")

    fig, ax = plt.subplots(2, 2, figsize=(13, 11))
    fig.suptitle("R39 — rock-paper-scissors: local dispersal preserves biodiversity",
                 fontsize=14, fontweight="bold")
    names = ["rock", "paper", "scissors"]; cols = ["#e0245e", "#1d9bf0", "#f5c518"]

    a = ax[0, 0]
    for k in range(3):
        a.plot(sp["fractions"][:, k], color=cols[k], lw=2, label=names[k])
    a.set_title("Lattice: all three species coexist (~1/3 each)")
    a.set_xlabel("step"); a.set_ylabel("fraction"); a.set_ylim(0, 1); a.legend(fontsize=9)

    a = ax[0, 1]
    for k in range(3):
        a.plot(wm["fractions"][:, k], color=cols[k], lw=2, label=names[k])
    a.set_title("Well-mixed: one species fixates, diversity dies")
    a.set_xlabel("step"); a.set_ylabel("fraction"); a.set_ylim(0, 1); a.legend(fontsize=9)

    a = ax[1, 0]
    a.imshow(sp["snaps"][cfg.steps], cmap=CMAP, vmin=0, vmax=2, interpolation="nearest")
    a.set_title(f"Lattice at t={cfg.steps}: all three persist in interwoven domains")
    a.set_xticks([]); a.set_yticks([])

    a = ax[1, 1]
    a.imshow(wm["snaps"][cfg.steps], cmap=CMAP, vmin=0, vmax=2, interpolation="nearest")
    a.set_title(f"Well-mixed at t={cfg.steps}: a single species remains")
    a.set_xticks([]); a.set_yticks([])

    fig.tight_layout()
    path = OUT / "rps.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
