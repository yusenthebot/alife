"""R49 — evolutionary branching (adaptive dynamics).

A single trait under frequency-dependent competition converges to the resource
peak, then disruptive selection splits it into diverging lineages — when the
competition kernel is narrower than the resource distribution. Widen competition
and no branching occurs.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from dataclasses import replace  # noqa: E402

from alife.adaptivedyn import AdaptiveDynConfig, evolve, n_clusters  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r49_adaptivedyn"


def _diagram(ax, hist, title):
    g = hist.shape[0]
    gens = np.repeat(np.arange(g), hist.shape[1])
    ax.hist2d(gens, hist.ravel(), bins=[min(g, 220), 120], cmap="inferno")
    ax.set_title(title); ax.set_xlabel("generation"); ax.set_ylabel("trait x")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = AdaptiveDynConfig()
    branch = evolve(cfg, seed=0)
    wide = evolve(replace(cfg, sigma_c=1.6), seed=0)
    print(f"branching (σc={cfg.sigma_c}<σk={cfg.sigma_k}): {n_clusters(branch[-1])} clusters")
    print(f"no branching (σc=1.6>σk={cfg.sigma_k}): {n_clusters(wide[-1])} clusters")

    fig, ax = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("R49 — evolutionary branching: one lineage splits under disruptive competition",
                 fontsize=14, fontweight="bold")
    _diagram(ax[0], branch, f"σc={cfg.sigma_c} < σk={cfg.sigma_k}: the lineage BRANCHES")
    _diagram(ax[1], wide, f"σc=1.6 > σk={cfg.sigma_k}: no branching (one cluster)")
    fig.tight_layout()
    path = OUT / "adaptivedyn.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
