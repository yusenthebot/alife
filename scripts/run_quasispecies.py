"""R44 — Eigen's error threshold / quasispecies.

A master sequence is maintained only below a critical mutation rate mu_c ~
ln(sigma)/L; above it the population suffers an error catastrophe and delocalises
into a random mutant cloud. The collapse point tracks the ln(sigma) prediction.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from dataclasses import replace  # noqa: E402

from alife.quasispecies import QuasispeciesConfig, evolve, mu_sweep  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r44_quasispecies"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = QuasispeciesConfig()
    mu_c = cfg.mu_c

    mus = np.round(np.arange(0.0, 0.171, 0.01), 3)
    sweep = mu_sweep(cfg, mus)
    below = evolve(cfg, mu=mu_c * 0.4, seed=0)
    above = evolve(cfg, mu=mu_c * 1.5, seed=0)

    print(f"mu_c = ln(sigma)/L = {mu_c:.3f}")
    print(f"below (mu={mu_c*0.4:.3f}): final master {below['final_master']:.2f} | "
          f"above (mu={mu_c*1.5:.3f}): {above['final_master']:.2f}")

    # threshold scales with ln(sigma): measured collapse-mu vs prediction
    sigmas = [2.0, 4.0, 8.0, 16.0]
    pred, meas = [], []
    fine = np.round(np.arange(0.005, 0.22, 0.005), 3)
    for s in sigmas:
        c = replace(cfg, sigma=s)
        sw = mu_sweep(c, fine)
        # measured threshold = largest mu with master_freq still > 0.5
        idx = np.where(sw > 0.5)[0]
        meas.append(float(fine[idx[-1]]) if idx.size else 0.0)
        pred.append(np.log(s) / cfg.loci)

    fig, ax = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle("R44 — Eigen's error threshold: the limit of heredity",
                 fontsize=15, fontweight="bold")

    a = ax[0, 0]
    a.plot(mus, sweep, "o-", color="#1d9bf0", lw=2)
    a.axvline(mu_c, color="#e0245e", lw=1.5, ls="--", label=f"mu_c = ln(σ)/L = {mu_c:.3f}")
    a.set_title("Master sequence collapses at the error threshold")
    a.set_xlabel("mutation rate μ"); a.set_ylabel("master-sequence frequency"); a.legend(fontsize=9)

    a = ax[0, 1]
    gens = np.arange(cfg.generations + 1)
    a.plot(gens, below["master_freq"], color="#1b7a3d", lw=2, label=f"below μ_c (μ={mu_c*0.4:.3f})")
    a.plot(gens, above["master_freq"], color="#e0245e", lw=2, label=f"above μ_c (μ={mu_c*1.5:.3f})")
    a.set_title("Heredity maintained vs error catastrophe")
    a.set_xlabel("generation"); a.set_ylabel("master frequency"); a.set_ylim(-0.02, 1.05); a.legend(fontsize=9)

    a = ax[1, 0]
    hams = [evolve(cfg, mu=m, seed=0)["mean_hamming"] for m in mus]
    a.plot(mus, hams, "o-", color="#7d3cff", lw=2)
    a.axvline(mu_c, color="#e0245e", lw=1.5, ls="--")
    a.axhline(cfg.loci / 2, color="k", lw=0.8, ls=":", alpha=0.6, label="random cloud (L/2)")
    a.set_title("Delocalisation: distance from master jumps to the random baseline")
    a.set_xlabel("mutation rate μ"); a.set_ylabel("mean Hamming distance"); a.legend(fontsize=9)

    a = ax[1, 1]
    a.plot(sigmas, pred, "o-", color="#1d9bf0", lw=2, label="predicted ln(σ)/L")
    a.plot(sigmas, meas, "s--", color="#f5a623", lw=2, label="measured collapse μ")
    a.set_xscale("log", base=2)
    a.set_title("The threshold scales with ln(σ)")
    a.set_xlabel("master fitness advantage σ (log)"); a.set_ylabel("error threshold μ_c"); a.legend(fontsize=9)

    fig.tight_layout()
    path = OUT / "quasispecies.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
