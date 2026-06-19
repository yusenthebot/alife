"""R90 — milestone gallery: the R81–R89 arc in one poster.

Neural dreaming (RBM), opinion dynamics (voter), the two pillars of network science (scale-free +
small-world) and epidemics on them, the canonical equilibrium phase transition (Ising), emergent
traffic jams, excitable spiral waves, and a major evolutionary transition (division of labor).
"""

from __future__ import annotations

import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "runs" / "r90_review"

PANELS = [
    ("R81", "RBM — neural dreaming", "runs/r81_boltzmann/boltzmann.png"),
    ("R82", "Voter model", "runs/r82_votermodel/votermodel.png"),
    ("R83", "Scale-free networks", "runs/r83_network/network.png"),
    ("R84", "Epidemics on networks", "runs/r84_epidemic/epidemic.png"),
    ("R85", "Ising phase transition", "runs/r85_ising/ising.png"),
    ("R86", "Traffic phantom jams", "runs/r86_traffic/traffic.png"),
    ("R87", "Small-world networks", "runs/r87_smallworld/smallworld.png"),
    ("R88", "Excitable spiral waves", "runs/r88_excitable/excitable.png"),
    ("R89", "Division of labor", "runs/r89_divlabor/divlabor.png"),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 3, figsize=(18, 16))
    fig.suptitle("alife — frontier arc R81–R89 (neural dreaming · opinion dynamics · network science "
                 "· epidemics · Ising · traffic jams · spiral waves · major transition)",
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
