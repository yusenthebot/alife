"""R53 — the tree of life in the digital soup: lineages, clades, coalescence.

Tags founding lineages in the R51 digital-evolution soup and watches the universal
signatures of an evolving population: clades rise and fall (Muller plot), new
genotypes keep appearing (evolutionary activity), and all survivors coalesce to a
single common ancestor.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.digphylo import PhyloConfig, run  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r53_digphylo"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = PhyloConfig()
    r = run(cfg, seed=0)
    t = r["t"]
    print(f"coalescence: {int(r['n_lineages'][0])} founding lineages -> {int(r['n_lineages'][-1])}")
    print(f"cumulative genotypes explored: {int(r['cum_genotypes'][-1])}")

    fig, ax = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle("R53 — the tree of life in the digital soup (lineages, clades, coalescence)",
                 fontsize=14, fontweight="bold")

    a = ax[0, 0]
    series = np.array([r["lineage_series"][k] for k in range(cfg.n_found)])
    cmap = plt.get_cmap("turbo")
    a.stackplot(t, series, colors=[cmap(k / cfg.n_found) for k in range(cfg.n_found)])
    a.set_title("Muller plot: founding lineages rise & fall, one prevails")
    a.set_xlabel("scheduler sweep"); a.set_ylabel("organisms by lineage"); a.set_xlim(t[0], t[-1])

    a = ax[0, 1]
    a.plot(t, r["n_lineages"], color="#e0245e", lw=2)
    a.axhline(1, color="k", lw=0.8, ls=":", alpha=0.6)
    a.set_title("Coalescence: all survivors trace to ONE common ancestor")
    a.set_xlabel("scheduler sweep"); a.set_ylabel("surviving founding lineages")

    a = ax[1, 0]
    a.plot(t, r["cum_genotypes"], color="#1b7a3d", lw=2, label="cumulative genotypes seen")
    a.plot(t, r["n_genotypes"], color="#1d9bf0", lw=1.5, label="genotypes alive now")
    a.set_title("Ongoing evolutionary activity: genotypes keep being discovered")
    a.set_xlabel("scheduler sweep"); a.set_ylabel("distinct genomes"); a.legend(fontsize=9)

    a = ax[1, 1]
    a.plot(t, 100 * r["top_lineage"], color="#7d3cff", lw=2)
    a.set_title("Dominant lineage's share of the population")
    a.set_xlabel("scheduler sweep"); a.set_ylabel("% of population"); a.set_ylim(0, 105)

    fig.tight_layout()
    path = OUT / "digphylo.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
