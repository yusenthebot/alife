"""R110 — milestone gallery: the R101–R109 arc in one poster.

The real-fluid evolved-swimming trilogy (lattice-Boltzmann, an undulatory swimmer, an evolved gait),
then granular flow, explosive synchronization, KPZ surface growth, earthquakes, gene circuits, and
spatial predator-prey — the post-R100 ambition leap into real physics + a stream of distinct
complex-systems models.
"""

from __future__ import annotations

import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "runs" / "r110_review"

PANELS = [
    ("R101", "Lattice-Boltzmann fluid", "runs/r101_fluid/fluid.png"),
    ("R102", "Undulatory swimmer", "runs/r102_swimmer/swimmer.png"),
    ("R103", "Evolved swimming gait", "runs/r103_evoswim/evoswim.png"),
    ("R104", "Granular hopper (Beverloo)", "runs/r104_granular/granular.png"),
    ("R105", "Explosive synchronization", "runs/r105_explosivesync/explosivesync.png"),
    ("R106", "KPZ surface growth", "runs/r106_kpz/kpz.png"),
    ("R107", "OFC earthquakes", "runs/r107_earthquake/earthquake.png"),
    ("R108", "Gene circuits", "runs/r108_genecircuit/genecircuit.png"),
    ("R109", "Spatial predator-prey", "runs/r109_spatialpredprey/spatialpredprey.png"),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 3, figsize=(20, 11))
    fig.suptitle("alife — frontier arc R101–R109 (real fluid + evolved swimming · granular · "
                 "explosive sync · KPZ · earthquakes · gene circuits · spatial ecology)",
                 fontsize=15, fontweight="bold")
    for ax, (tag, name, rel) in zip(axes.flatten(), PANELS):
        p = ROOT / rel
        if p.exists():
            ax.imshow(plt.imread(p)); ax.set_title(f"{tag} — {name}", fontsize=11, fontweight="bold")
        ax.axis("off")
    fig.tight_layout(rect=[0, 0, 1, 0.985])
    path = OUT / "gallery.png"
    fig.savefig(path, dpi=80, facecolor="white")
    print(f"saved {path} ({len(PANELS)} panels)")


if __name__ == "__main__":
    main()
