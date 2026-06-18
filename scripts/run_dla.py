"""R78 — Diffusion-limited aggregation (Witten-Sander): growth into a fractal.

Brownian wanderers freeze on contact with a growing cluster. Because a walker almost always
strikes a tip before reaching an interior fjord, the cluster becomes a self-similar dendrite
(fractal dimension ~1.71 in 2D). Lower sticking lets walkers penetrate deeper -> a denser cluster;
a seed line grows a coral-like forest of competing branches.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.dla import grow, fractal_dimension  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r78_dla"


def _show(ax, res, title, cmap="magma"):
    order = res["order"].astype(float)
    img = np.where(order >= 0, order, np.nan)
    ax.imshow(img, cmap=cmap, interpolation="nearest")
    ax.set_title(title, fontsize=9); ax.axis("off"); ax.set_facecolor("black")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    main_c = grow(size=321, n_particles=9000, seed=0)
    radii, mass, D = fractal_dimension(main_c["occ"], main_c["center"], rmin=6,
                                       rmax=int(main_c["rmax"] * 0.7))
    coral = grow(size=220, n_particles=10000, seed=2, seed_shape="line")
    sticks = [1.0, 0.3, 0.03]
    cl = []
    for st in sticks:
        r = grow(size=171, n_particles=3500, stick=st, seed=1)
        _, _, d = fractal_dimension(r["occ"], r["center"], rmin=6)
        cl.append((st, r, d))
    print(f"main dendrite: placed {main_c['placed']}, D={D:.2f} (asymptotic DLA ~1.71)")
    print(f"sticking D: {[(s, round(d, 2)) for s, _, d in cl]} (lower stick -> denser -> higher D)")

    fig = plt.figure(figsize=(16.5, 10.5))
    fig.suptitle("R78 — Diffusion-limited aggregation (Witten-Sander): Brownian growth into a fractal",
                 fontsize=14, fontweight="bold")

    _show(fig.add_subplot(2, 3, 1), main_c, "DLA dendrite (colour = growth order)\ntips screen the interior", "magma")
    _show(fig.add_subplot(2, 3, 2), coral, "Seed LINE → a coral forest of\ncompeting branches (deposition DLA)", "viridis")

    ax = fig.add_subplot(2, 3, 3)
    ax.loglog(radii, mass, "o", color="#1d9bf0", ms=4)
    xs = np.array([radii.min(), radii.max()])
    ax.loglog(xs, mass[0] * (xs / radii[0]) ** D, "--", color="#e0245e", label=f"D ≈ {D:.2f}")
    ax.set_title("Fractal: mass ∝ r^D (not r²)\nself-similar, mostly empty space")
    ax.set_xlabel("radius r"); ax.set_ylabel("mass within r"); ax.legend(fontsize=9); ax.grid(alpha=0.25, which="both")

    for k, (st, r, d) in enumerate(cl):
        _show(fig.add_subplot(2, 3, 4 + k), r,
              f"stick prob = {st}  →  D ≈ {d:.2f}\n{'ramified' if st == 1.0 else 'denser' if st == 0.3 else 'compact'}",
              "inferno")

    fig.tight_layout()
    path = OUT / "dla.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
