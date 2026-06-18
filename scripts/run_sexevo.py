"""R37 — the evolution of sex: Muller's ratchet.

Under deleterious mutation pressure, an asexual population's least-loaded class is
irreversibly lost click by click, so mean load climbs without bound and fitness
erodes. Sexual recombination reconstitutes clean genotypes, holding load at
mutation-selection balance. Same mutation rate, same selection — only recombination
differs.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.sexevo import SexEvoConfig, evolve  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r37_sexevo"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = SexEvoConfig()
    asex = evolve(cfg, sexual=False, seed=0)
    sex = evolve(cfg, sexual=True, seed=0)
    gens = np.arange(cfg.generations + 1)
    balance = cfg.mut_rate / cfg.sel

    print(f"asexual mean load {asex['mean_load'][0]:.0f} -> {asex['mean_load'][-1]:.0f}")
    print(f"sexual  mean load {sex['mean_load'][0]:.0f} -> {sex['mean_load'][-1]:.0f} (U/s balance ~{balance:.0f})")
    print(f"asexual min-class (ratchet) {asex['min_load'][0]} -> {asex['min_load'][-1]}; "
          f"sexual min-class -> {sex['min_load'][-1]}")

    finals_a = [evolve(cfg, False, s)["mean_load"][-1] for s in range(5)]
    finals_s = [evolve(cfg, True, s)["mean_load"][-1] for s in range(5)]

    fig, ax = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle("R37 — the evolution of sex: Muller's ratchet", fontsize=15, fontweight="bold")

    a = ax[0, 0]
    a.plot(gens, asex["mean_load"], color="#e0245e", lw=2, label="asexual")
    a.plot(gens, sex["mean_load"], color="#1d9bf0", lw=2, label="sexual")
    a.axhline(balance, color="#1d9bf0", lw=1, ls="--", alpha=0.6, label="mutation-selection balance")
    a.set_title("Mean mutation load climbs without bound (asexual)")
    a.set_xlabel("generation"); a.set_ylabel("mean deleterious mutations"); a.legend(fontsize=9)

    a = ax[0, 1]
    a.plot(gens, asex["min_load"], color="#e0245e", lw=2, label="asexual")
    a.plot(gens, sex["min_load"], color="#1d9bf0", lw=2, label="sexual")
    a.set_title("The ratchet clicks: least-loaded class (asexual can only climb)")
    a.set_xlabel("generation"); a.set_ylabel("mutations in the cleanest genome"); a.legend(fontsize=9)

    a = ax[1, 0]
    a.plot(gens, asex["mean_fitness"], color="#e0245e", lw=2, label="asexual")
    a.plot(gens, sex["mean_fitness"], color="#1d9bf0", lw=2, label="sexual")
    a.set_title("Fitness erodes without sex")
    a.set_xlabel("generation"); a.set_ylabel("mean fitness  (1-s)^load"); a.legend(fontsize=9)

    a = ax[1, 1]
    a.bar(np.arange(5) - 0.2, finals_a, width=0.4, color="#e0245e", label="asexual")
    a.bar(np.arange(5) + 0.2, finals_s, width=0.4, color="#1d9bf0", label="sexual")
    a.set_title("Final load across 5 seeds (sex purges the load)")
    a.set_xlabel("seed"); a.set_ylabel("final mean load"); a.legend(fontsize=9)

    fig.tight_layout()
    path = OUT / "sexevo.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
