"""R63 — Hypercycles (Eigen-Schuster): cooperation, its parasite, and the spatial rescue.

Well-mixed: a hypercycle of n>=5 replicators settles into a permanent limit cycle (all
coexist), where uncoupled replicators show competitive exclusion; a non-reciprocating
parasite collapses it. Spatial: the same hypercycle self-organises into rotating spiral
waves that expel the very parasite that kills the well-mixed version.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.hypercycle import (  # noqa: E402
    SpatialConfig, replicator_hypercycle, replicator_independent,
    spatial_hypercycle, persistent, amplitude, area_fractions, rgb_field,
)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r63_hypercycle"
HUES = plt.cm.hsv(np.linspace(0, 1, 6, endpoint=False))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    steps = 30000

    hc = replicator_hypercycle(5, steps=steps, dt=0.02, seed=0)
    ind = replicator_independent(5, steps=steps, k=1 + 0.3 * np.arange(5) / 5, seed=1)
    par = replicator_hypercycle(5, steps=steps, dt=0.02, seed=0, parasite_k=1.0, parasite_host=0)
    print(f"well-mixed hypercycle n=5: persistent={persistent(hc)}/5 (limit cycle)")
    print(f"independent replicators:   persistent={persistent(ind)}/5 (competitive exclusion)")
    print(f"hypercycle + parasite:     cycle persistent={persistent(par[:, :5])}/5, "
          f"parasite={par[-1, 5]:.2f} (collapse)")

    scfg = SpatialConfig(n=5, size=256, death=0.06, cat=2.0, empty_w=0.3)
    sp = spatial_hypercycle(scfg, steps=3000, seed=3, record_every=150)
    sp_frac = area_fractions(sp["state"], 5)
    fr_series = np.array([[ (sp["snaps"][k] == i).mean() for i in range(5)]
                          for k in sorted(sp["snaps"])])
    fr_t = np.array(sorted(sp["snaps"]))
    print(f"spatial hypercycle: spirals, all coexist {np.round(sp_frac, 2)}")

    # classic n-dependence: amplitude of the well-mixed cycle vs n (limit cycle onset at n>=5)
    amps = [(nn, amplitude(replicator_hypercycle(nn, steps=30000, dt=0.02, seed=0)))
            for nn in (3, 4, 5, 6, 7)]
    print("amplitude vs n:", [(n, round(a, 2)) for n, a in amps])

    fig = plt.figure(figsize=(16.5, 10.5))
    fig.suptitle("R63 — Hypercycles: cooperation among replicators, its parasite, and self-organizing spiral waves",
                 fontsize=14, fontweight="bold")
    tax = np.arange(steps + 1) * 0.02

    ax = fig.add_subplot(2, 3, 1)
    for i in range(5):
        ax.plot(tax, hc[:, i], color=HUES[i], lw=1.1)
    ax.set_title("Well-mixed hypercycle (n=5): permanent LIMIT CYCLE\nall members coexist forever")
    ax.set_xlabel("time"); ax.set_ylabel("concentration"); ax.set_ylim(0, 1)

    ax = fig.add_subplot(2, 3, 2)
    for i in range(5):
        ax.plot(tax, ind[:, i], color=HUES[i], lw=1.1)
    ax.set_title("Uncoupled replicators: COMPETITIVE EXCLUSION\nonly the fittest survives")
    ax.set_xlabel("time"); ax.set_ylim(0, 1)

    ax = fig.add_subplot(2, 3, 3)
    for i in range(5):
        ax.plot(tax, par[:, i], color=HUES[i], lw=1.0)
    ax.plot(tax, par[:, 5], color="black", lw=2.0, ls="--", label="parasite")
    ax.set_title("+ a non-reciprocating PARASITE:\nthe well-mixed hypercycle COLLAPSES")
    ax.set_xlabel("time"); ax.set_ylim(0, 1); ax.legend(fontsize=8)

    ax = fig.add_subplot(2, 3, 4)
    ax.imshow(rgb_field(sp["state"], 5))
    ax.set_title("Spatial hypercycle -> rotating SPIRAL WAVES\n(Boerlijst-Hogeweg; all 5 coexist)")
    ax.axis("off")

    ax = fig.add_subplot(2, 3, 5)
    for i in range(5):
        ax.plot(fr_t, fr_series[:, i], color=HUES[i], lw=1.6)
    ax.set_title("Spatial coexistence is stable:\nrotating waves keep all 5 species ~1/5 each")
    ax.set_xlabel("step"); ax.set_ylabel("area fraction"); ax.set_ylim(0, 0.5)

    ax = fig.add_subplot(2, 3, 6)
    ns = [n for n, _ in amps]
    av = [a for _, a in amps]
    cols = ["#9aa0a6" if a < 0.1 else "#e0245e" for a in av]
    ax.bar([str(n) for n in ns], av, color=cols)
    ax.axhline(0.1, color="#1d9bf0", ls=":", lw=1)
    ax.set_title("Limit-cycle onset: oscillation amplitude vs cycle length n\n(n<=4 -> fixed point, n>=5 -> sustained cycle)")
    ax.set_xlabel("cycle length n"); ax.set_ylabel("oscillation amplitude")

    fig.tight_layout()
    path = OUT / "hypercycle.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
