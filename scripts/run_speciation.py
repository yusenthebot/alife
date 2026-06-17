#!/usr/bin/env python
"""Round 16 — sympatric speciation: one lineage splitting into two species.

Shows the diet distribution evolving over generations under assortative vs random
mating (both with frequency-dependent disruptive selection).

Artifacts into runs/<name>/:
  speciation.png   diet-vs-generation density (assortative splits into two bands;
                   random collapses to one) + bimodality over time
Usage:
  python scripts/run_speciation.py --name speciation
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alife.speciation import SpeciationConfig, count_species, evolve  # noqa: E402


def density(hist, bins=60):
    edges = np.linspace(0, 1, bins + 1)
    return np.array([np.histogram(g, bins=edges, density=True)[0] for g in hist]).T  # (diet, gen)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--name", type=str, default="speciation")
    args = ap.parse_args()
    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)
    cfg = SpeciationConfig()

    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    for col, (assort, title) in enumerate([(True, "assortative mating"), (False, "random mating")]):
        hist, bc = evolve(cfg, assortative=assort, seed=args.seed)
        dens = density(hist)
        ax = axes[0, col]
        ax.imshow(dens, aspect="auto", origin="lower", extent=[0, len(hist), 0, 1],
                  cmap="magma", interpolation="nearest")
        ax.set_title(f"{title}: diet over generations\n(final species: {count_species(hist[-1])})")
        ax.set_xlabel("generation"); ax.set_ylabel("diet trait")
        ax2 = axes[1, col]
        ax2.plot(bc, color="tab:cyan", lw=1.8)
        ax2.axhline(0.555, color="gray", ls="--", lw=1, label="bimodal threshold")
        ax2.set_ylim(0, 1.05); ax2.set_xlabel("generation"); ax2.set_ylabel("bimodality coeff")
        ax2.grid(alpha=0.25); ax2.legend(fontsize=8)
    fig.suptitle("Sympatric speciation: disruptive selection + assortative mating splits one species into two",
                 fontsize=13)
    fig.tight_layout()
    fig.savefig(out / "speciation.png", dpi=110)
    plt.close(fig)

    for assort in (True, False):
        hist, bc = evolve(cfg, assortative=assort, seed=args.seed)
        print(f"{'assortative' if assort else 'random':12s}: final species = {count_species(hist[-1])}, BC = {bc[-1]:.2f}")
    print(f"Artifacts in {out}")


if __name__ == "__main__":
    main()
