"""R100 — milestone gallery: the R91–R99 arc in one poster.

Evolved self-propulsion, Turing animal coats, segregation, gene-regulatory order/chaos, chemotaxis,
synchronization, percolation, cultural dissemination, and active-matter phase separation.
"""

from __future__ import annotations

import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "runs" / "r100_review"

PANELS = [
    ("R91", "Evolved self-propulsion", "runs/r91_evoparticle/evoparticle.png"),
    ("R92", "Turing animal coats", "runs/r92_gierermeinhardt/gierermeinhardt.png"),
    ("R93", "Schelling segregation", "runs/r93_schelling/schelling.png"),
    ("R94", "Boolean-net order/chaos", "runs/r94_booleannet/booleannet.png"),
    ("R95", "Bacterial chemotaxis", "runs/r95_chemotaxis/chemotaxis.png"),
    ("R96", "Kuramoto synchronization", "runs/r96_kuramoto/kuramoto.png"),
    ("R97", "Percolation", "runs/r97_percolation/percolation.png"),
    ("R98", "Axelrod culture", "runs/r98_axelrod/axelrod.png"),
    ("R99", "MIPS active matter", "runs/r99_mips/mips.png"),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 3, figsize=(18, 12))
    fig.suptitle("alife — frontier arc R91–R99 (evolved active matter · Turing coats · segregation · "
                 "gene nets · chemotaxis · synchronization · percolation · culture · MIPS)",
                 fontsize=15, fontweight="bold")
    for ax, (tag, name, rel) in zip(axes.flatten(), PANELS):
        p = ROOT / rel
        if p.exists():
            ax.imshow(plt.imread(p)); ax.set_title(f"{tag} — {name}", fontsize=11, fontweight="bold")
        ax.axis("off")
    fig.tight_layout(rect=[0, 0, 1, 0.985])
    path = OUT / "gallery.png"
    fig.savefig(path, dpi=85, facecolor="white")
    print(f"saved {path} ({len(PANELS)} panels)")


if __name__ == "__main__":
    main()
