"""R70 — milestone gallery: the R59–R69 frontier arc in one poster.

Tiles each round's headline figure: GPU local adaptation, GPU Lenia, Particle Life,
autocatalytic sets, hypercycles, L-system development, ant foraging, the edge of chaos,
evolving CA to compute, Physarum transport networks, and Hopfield memory.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "runs" / "r70_review"

PANELS = [
    ("R59", "GPU local adaptation @1M", "runs/r59_gpuecoevo/gpuecoevo.png"),
    ("R60", "GPU Lenia creatures", "runs/r60_gpulenia/gpulenia.png"),
    ("R61", "Particle Life", "runs/r61_particlelife/particlelife.png"),
    ("R62", "Autocatalytic sets (RAF)", "runs/r62_autocatalytic/autocatalytic.png"),
    ("R63", "Hypercycles", "runs/r63_hypercycle/hypercycle.png"),
    ("R64", "L-system development", "runs/r64_lsystem/lsystem.png"),
    ("R65", "Ant-colony foraging", "runs/r65_antcolony/antcolony.png"),
    ("R66", "Edge of chaos", "runs/r66_edgeofchaos/edgeofchaos.png"),
    ("R67", "Evolving CA to compute", "runs/r67_evolveca/evolveca.png"),
    ("R68", "Physarum transport nets", "runs/r68_transport/transport.png"),
    ("R69", "Hopfield memory", "runs/r69_hopfield/hopfield.png"),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cols, rows = 3, 4
    fig, axes = plt.subplots(rows, cols, figsize=(19, 18))
    fig.suptitle("alife — frontier arc R59–R69 (GPU evolution · artificial chemistry · "
                 "development · stigmergy · CA computation · networks · memory)",
                 fontsize=17, fontweight="bold")
    axf = axes.flatten()
    for ax, (tag, name, rel) in zip(axf, PANELS):
        p = ROOT / rel
        if p.exists():
            ax.imshow(plt.imread(p))
            ax.set_title(f"{tag} — {name}", fontsize=11, fontweight="bold")
        ax.axis("off")
    for ax in axf[len(PANELS):]:
        ax.axis("off")
    fig.tight_layout(rect=[0, 0, 1, 0.985])
    path = OUT / "gallery.png"
    fig.savefig(path, dpi=85, facecolor="white")
    print(f"saved {path} ({len(PANELS)} panels)")


if __name__ == "__main__":
    main()
