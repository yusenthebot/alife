"""R64 — Development & diversity: L-system plants and the morphospace they fill.

A tiny rewrite rule unfolds into a plant (development); different rules are different
species (diversity); and since no single shape is "best" for an isolated plant, MAP-Elites
illuminates the whole (slenderness, branchiness) morphospace — a botanical garden of forms
discovered from random grammars.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.gridspec import GridSpec  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.lsystem import (  # noqa: E402
    LSConfig, Genome, phenotype, turtle, expand, map_elites, descriptors, SPECIES,
)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r64_lsystem"


def _draw(ax, segs, color="#1f7a1f", lw=0.5):
    if len(segs):
        ax.add_collection(LineCollection(segs.reshape(-1, 2, 2), colors=color, linewidths=lw))
        ax.autoscale(); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = LSConfig(depth=5)

    r = map_elites(cfg, grid=(10, 10), iters=7000, seed=0)
    G = r["grid"][0]
    print(f"MAP-Elites morphospace coverage {r['coverage']:.0%} ({len(r['archive'])}/{G*G} cells)")
    for name, g in SPECIES.items():
        d = descriptors(phenotype(g, cfg))
        print(f"  {name:13s} slender={d[0]:.2f} branchy={d[1]:.2f} tips={d[2]}")

    fig = plt.figure(figsize=(16.5, 15))
    fig.suptitle("R64 — Development & diversity: L-system plants and the morphospace evolution fills",
                 fontsize=15, fontweight="bold")
    outer = GridSpec(3, 1, height_ratios=[1.0, 1.0, 3.2], hspace=0.18, figure=fig)

    # 1) developmental cascade of one rule
    casc = outer[0].subgridspec(1, 5, wspace=0.05)
    tree = SPECIES["tree"]
    for d in range(1, 6):
        ax = fig.add_subplot(casc[d - 1])
        _draw(ax, turtle(expand(tree.rule, d, cfg.max_len), tree.angle, cfg.step), lw=0.6)
        ax.set_title(f"iteration {d}", fontsize=9)
    fig.text(0.5, 0.93, "DEVELOPMENT: one rule unfolds from a seed into a plant",
             ha="center", fontsize=11, fontweight="bold")

    # 2) species gallery
    gal = outer[1].subgridspec(1, 6, wspace=0.05)
    for k, (name, g) in enumerate(SPECIES.items()):
        ax = fig.add_subplot(gal[k])
        _draw(ax, phenotype(g, cfg), lw=0.5)
        ax.set_title(name, fontsize=9)
    fig.text(0.5, 0.715, "DIVERSITY: different grammars are different species",
             ha="center", fontsize=11, fontweight="bold")

    # 3) MAP-Elites morphospace: a grid of evolved plants by (slenderness, branchiness)
    ms = outer[2].subgridspec(G, G, wspace=0.04, hspace=0.04)
    for (i, j), (_, g) in r["archive"].items():
        ax = fig.add_subplot(ms[G - 1 - j, i])     # x=slenderness right, y=branchiness up
        _draw(ax, phenotype(g, cfg), lw=0.35)
    fig.text(0.5, 0.565, "OPEN-ENDED MORPHOSPACE: MAP-Elites fills (slenderness →, branchiness ↑) "
             f"with diverse evolved plants  [{r['coverage']:.0%} of cells]",
             ha="center", fontsize=11, fontweight="bold")

    path = OUT / "lsystem.png"
    fig.savefig(path, dpi=110, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
