"""R74 — The abelian sandpile (Bak-Tang-Wiesenfeld): self-organized criticality on a lattice.

A slowly-driven sandpile self-organizes to a critical state (mean height ≈2.1) where avalanche
sizes follow a power law; and because toppling is abelian, a single huge point source relaxes
into a deterministic self-similar fractal.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.sandpile import point_source, drive_soc, add_grain, avalanche_powerlaw  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r74_sandpile"
CMAP = ListedColormap(["#0a0a2a", "#1d6fb8", "#37c0a6", "#ffd23f"])   # heights 0,1,2,3


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    frac, topples = point_source(255, 60000)
    print(f"fractal: 255^2, 60k grains -> {topples} topplings, footprint {(frac > 0).mean():.2f}")

    sizes, gp, mh = drive_soc(64, warmup=5000, measure=25000, seed=0)
    centers, pdf, slope = avalanche_powerlaw(sizes, smin=1, smax=8000)
    print(f"SOC: mean height {mh:.2f} (critical ~2.1); avalanche power-law slope {slope:.2f}")

    # mean-height self-organization while driving an empty lattice
    g = np.zeros((64, 64), dtype=np.int64)
    htrace = []
    rng = np.random.default_rng(1)
    for k in range(9000):
        g, _ = add_grain(g, int(rng.integers(64)), int(rng.integers(64)))
        if k % 50 == 0:
            htrace.append(g.mean())

    fig = plt.figure(figsize=(16.5, 10))
    fig.suptitle("R74 — The abelian sandpile (Bak-Tang-Wiesenfeld): self-organized criticality & fractal order",
                 fontsize=14, fontweight="bold")

    ax = fig.add_subplot(2, 2, 1)
    ax.imshow(frac, cmap=CMAP, interpolation="nearest")
    ax.set_title("Point source relaxes to a self-similar FRACTAL\n(60k grains; heights 0–3, abelian)")
    ax.set_xticks([]); ax.set_yticks([])

    ax = fig.add_subplot(2, 2, 2)
    c = 255 // 2
    ax.imshow(frac[c - 55:c + 55, c - 55:c + 55], cmap=CMAP, interpolation="nearest")
    ax.set_title("Zoom: the same motifs recur at smaller scale")
    ax.set_xticks([]); ax.set_yticks([])

    ax = fig.add_subplot(2, 2, 3)
    if len(centers):
        ax.loglog(centers, pdf, "o", color="#e0245e", ms=6)
        xs = np.array([centers.min(), centers.max()])
        ax.loglog(xs, pdf[0] * (xs / centers[0]) ** slope, "--", color="#9aa0a6",
                  label=f"power law, slope {slope:.2f}")
        ax.legend(fontsize=9)
    ax.set_title("Avalanche sizes are SCALE-FREE (power law)\n— self-organized criticality")
    ax.set_xlabel("avalanche size (topplings)"); ax.set_ylabel("probability density")
    ax.grid(alpha=0.25, which="both")

    ax = fig.add_subplot(2, 2, 4)
    ax.plot(np.arange(len(htrace)) * 50, htrace, color="#1d9bf0", lw=2)
    ax.axhline(2.1, color="#e0245e", ls="--", lw=1.5, label="critical density ≈ 2.1")
    ax.set_title("The pile drives ITSELF to the critical density\n(no parameter tuned)")
    ax.set_xlabel("grains added"); ax.set_ylabel("mean height"); ax.legend(fontsize=9); ax.grid(alpha=0.25)

    fig.tight_layout()
    path = OUT / "sandpile.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
