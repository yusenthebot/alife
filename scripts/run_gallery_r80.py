"""R80 — milestone gallery: the R71–R79 arc in one poster.

Self-organized criticality (Bak-Sneppen, sandpile), program & strategy evolution (genetic
programming, iterated PD), reservoir computing, NK fitness landscapes, swarm decision-making,
diffusion-limited aggregation, and cellular-Potts tissue sorting.
"""

from __future__ import annotations

import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "runs" / "r80_review"

PANELS = [
    ("R71", "Bak-Sneppen SOC", "runs/r71_baksneppen/baksneppen.png"),
    ("R72", "Genetic programming", "runs/r72_genprog/genprog.png"),
    ("R73", "Reservoir computing", "runs/r73_reservoir/reservoir.png"),
    ("R74", "Abelian sandpile", "runs/r74_sandpile/sandpile.png"),
    ("R75", "Swarm decision", "runs/r75_swarmdecision/swarmdecision.png"),
    ("R76", "NK landscapes", "runs/r76_nklandscape/nklandscape.png"),
    ("R77", "IPD cooperation", "runs/r77_ipd/ipd.png"),
    ("R78", "Diffusion-limited aggregation", "runs/r78_dla/dla.png"),
    ("R79", "Cellular Potts cell-sorting", "runs/r79_cellsort/cellsort.png"),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 3, figsize=(18, 16))
    fig.suptitle("alife — frontier arc R71–R79 (criticality · program & strategy evolution · "
                 "reservoir · fitness landscapes · swarm cognition · fractal growth · tissue)",
                 fontsize=16, fontweight="bold")
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
