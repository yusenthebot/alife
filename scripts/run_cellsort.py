"""R79 — Cellular Potts model: tissue sorts itself out by differential adhesion (Steinberg).

A salt-and-pepper mixture of two cell types, evolving by Metropolis copy-attempts on an
adhesion + area-constraint energy, sorts itself into separate tissues — like cells coalesce.
The control (equal adhesion) does NOT sort, proving the mechanism is differential adhesion.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from dataclasses import replace  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.cellsort import CPMConfig, run, type_image  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r79_cellsort"
CMAP = ListedColormap(["#0a0a0f", "#e0245e", "#1d9bf0"])   # medium, type A, type B


def _img(ax, spin, types, title):
    ax.imshow(type_image(spin, types), cmap=CMAP, vmin=0, vmax=2, interpolation="nearest")
    ax.set_title(title, fontsize=10); ax.axis("off")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = CPMConfig(size=84, cell=5, temp=10.0)
    rd = run(cfg, sweeps=700, seed=0, record_every=350)
    eq = run(replace(cfg, J=((0, 16, 16), (16, 8, 8), (16, 8, 8))), sweeps=700, seed=0)
    h0, hd, he = rd["hetero"][0], rd["hetero"][-1], eq["hetero"][-1]
    print(f"differential: hetero {h0:.0f} -> {hd:.0f} ({100*(1-hd/h0):.0f}% sorted)")
    print(f"equal control: hetero {h0:.0f} -> {he:.0f} (no sorting / mixing)")

    fig = plt.figure(figsize=(16.5, 10))
    fig.suptitle("R79 — Cellular Potts model: tissue sorts itself by differential adhesion (Steinberg)",
                 fontsize=14, fontweight="bold")
    keys = sorted(rd["snaps"])
    _img(fig.add_subplot(2, 3, 1), rd["snaps"][keys[0]], rd["types"], "t=0: two cell types intermixed")
    _img(fig.add_subplot(2, 3, 2), rd["snaps"][keys[1]], rd["types"], f"sweep {keys[1]}: domains coalesce")
    _img(fig.add_subplot(2, 3, 3), rd["snaps"][keys[-1]], rd["types"], f"sweep {keys[-1]}: SORTED into tissues")

    _img(fig.add_subplot(2, 3, 4), eq["spin"], eq["types"],
         "Control — EQUAL adhesion: stays mixed\n(no sorting without a type preference)")

    ax = fig.add_subplot(2, 3, (5, 6))
    ax.plot(rd["hetero"], color="#1f7a1f", lw=2, label="differential adhesion (sorts)")
    ax.plot(eq["hetero"], color="#9aa0a6", lw=2, label="equal adhesion (control: mixes)")
    ax.set_title("The sorting metric: contacts between UNLIKE cells\nfalls only when like cells adhere more")
    ax.set_xlabel("Monte Carlo sweep"); ax.set_ylabel("heterotypic (A–B) boundary")
    ax.legend(fontsize=9); ax.grid(alpha=0.25)

    fig.tight_layout()
    path = OUT / "cellsort.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
