"""R71 — Bak-Sneppen co-evolution: self-organized criticality & punctuated equilibrium.

The least-fit species (and its neighbours) is repeatedly replaced. With no tuning the ecosystem
self-organizes to a critical state: fitnesses pile up above a threshold f_c≈0.667, activity comes
in power-law avalanches, and evolution proceeds by long stasis punctuated by sudden bursts.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.baksneppen import (  # noqa: E402
    run, avalanche_sizes, power_law_fit, threshold_estimate, activity_spacetime, F_C_1D,
)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r71_baksneppen"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    n, steps = 400, 600_000
    r = run(n=n, steps=steps, seed=0)
    fc = threshold_estimate(r["min_trace"])
    grid, _ = activity_spacetime(n, steps, seed=0)
    f0 = 0.62
    sizes = avalanche_sizes(r["min_trace"], f0)
    centers, pdf, slope = power_law_fit(sizes, smin=1, smax=50_000)
    print(f"f_c estimate {fc:.3f} (theory {F_C_1D}); final dist frac>{F_C_1D}={ (r['f']>F_C_1D).mean():.2f}")
    print(f"avalanches @f0={f0}: {len(sizes)}, max {sizes.max()}, power-law slope {slope:.2f}")

    fig = plt.figure(figsize=(16.5, 10))
    fig.suptitle("R71 — Bak-Sneppen co-evolution: self-organized criticality & punctuated equilibrium",
                 fontsize=14, fontweight="bold")

    ax = fig.add_subplot(2, 2, 1)
    ax.imshow(grid > 0, cmap="inferno", aspect="auto", interpolation="nearest")
    ax.set_title("Activity space-time: avalanches burst & spread,\nlong quiet stasis between (punctuated equilibrium)")
    ax.set_xlabel("species (ring)"); ax.set_ylabel("time →")

    ax = fig.add_subplot(2, 2, 2)
    ax.hist(r["f"], bins=50, color="#1d9bf0", alpha=0.85)
    ax.axvline(F_C_1D, color="#e0245e", ls="--", lw=2, label=f"f_c ≈ {F_C_1D}")
    ax.set_title("Self-organized gap: fitnesses pile up ABOVE f_c\n(no parameter was tuned to make this)")
    ax.set_xlabel("species fitness"); ax.set_ylabel("count"); ax.legend(fontsize=9)

    ax = fig.add_subplot(2, 2, 3)
    if len(centers):
        ax.loglog(centers, pdf, "o", color="#e0245e", ms=6)
        xs = np.array([centers.min(), centers.max()])
        ax.loglog(xs, pdf[0] * (xs / centers[0]) ** slope, "--", color="#9aa0a6",
                  label=f"power law, slope {slope:.2f}")
    ax.set_title("Avalanche sizes are SCALE-FREE (power law)\n— the signature of self-organized criticality")
    ax.set_xlabel("avalanche size"); ax.set_ylabel("probability density"); ax.legend(fontsize=9)
    ax.grid(alpha=0.25, which="both")

    ax = fig.add_subplot(2, 2, 4)
    seg = r["min_trace"][300_000:308_000]
    ax.plot(seg, lw=0.8, color="#1f7a1f")
    ax.axhline(F_C_1D, color="#e0245e", ls="--", lw=1.5, label=f"f_c ≈ {F_C_1D}")
    ax.set_title("Punctuated equilibrium (zoom): the min fitness creeps up,\nthen an avalanche crashes it — stasis then bursts")
    ax.set_xlabel("step (8k-window)"); ax.set_ylabel("selected min fitness"); ax.legend(fontsize=9)

    fig.tight_layout()
    path = OUT / "baksneppen.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
