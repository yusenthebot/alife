"""R25 — Sexual selection: Fisherian runaway.

A costly male ornament and a female preference coevolve. Choosy females mate with
ornamented males, so a genetic correlation builds between the two genes and the
ornament runs away from its survival optimum. Turn choice off and it collapses to 0.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.sexsel import SexSelConfig, evolve, preference_sweep  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r25_sexsel"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = SexSelConfig()

    choice = evolve(cfg, female_choice=True, seed=0)
    nochoice = evolve(cfg, female_choice=False, seed=0)
    gens = np.arange(cfg.generations + 1)

    prefs = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    sweep = preference_sweep(cfg, prefs)

    print(f"with choice   : ornament {choice.ornament[0]:+.2f} -> {choice.ornament[-1]:+.2f}, "
          f"preference {choice.preference[0]:+.2f} -> {choice.preference[-1]:+.2f}")
    print(f"without choice: ornament {nochoice.ornament[0]:+.2f} -> {nochoice.ornament[-1]:+.2f}")
    gc = np.nanmean(choice.gene_corr)
    print(f"within-pop genetic corr ornament<->preference (Fisher engine) = {gc:+.3f} "
          f"(no-choice control = {np.nanmean(nochoice.gene_corr):+.3f})")
    print(f"male survival with choice: {choice.survival[0]:.2f} -> {choice.survival[-1]:.2f} "
          f"(ornamented males pay {(1-choice.survival[-1])*100:.0f}% survival cost yet win mates)")
    print(f"preference sweep (final |ornament|): {dict(zip(prefs.tolist(), np.round(sweep,2).tolist()))}")

    fig, ax = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle("R25 — Sexual selection: Fisherian runaway", fontsize=15, fontweight="bold")

    a = ax[0, 0]
    a.plot(gens, choice.ornament, color="#e0245e", lw=2, label="ornament (with choice)")
    a.plot(gens, choice.preference, color="#1d9bf0", lw=2, label="preference (with choice)")
    a.plot(gens, nochoice.ornament, color="#888", lw=2, ls="--", label="ornament (no choice)")
    a.axhline(0, color="k", lw=0.8, alpha=0.4)
    a.set_title("Ornament & preference run away together"); a.set_xlabel("generation")
    a.set_ylabel("mean gene value"); a.legend(fontsize=9)

    a = ax[0, 1]
    a.plot(gens, choice.survival, color="#e0245e", lw=2)
    a.set_title("The cost paradox: ornamented males survive worse")
    a.set_xlabel("generation"); a.set_ylabel("mean male survival"); a.set_ylim(0, 1.05)
    a.text(0.5, 0.1, "yet they win the mating lottery", transform=a.transAxes,
           ha="center", color="#e0245e", fontsize=10)

    a = ax[1, 0]
    a.plot(prefs, sweep, "o-", color="#7d3cff", lw=2)
    a.set_title("Dose-response: stronger preference -> bigger ornament")
    a.set_xlabel("female preference strength"); a.set_ylabel("final |ornament|")

    a = ax[1, 1]
    a.plot(gens, choice.gene_corr, color="#e0245e", lw=2, label="with choice")
    a.plot(gens, nochoice.gene_corr, color="#888", lw=2, ls="--", label="no choice")
    a.axhline(0, color="k", lw=0.8, alpha=0.4)
    a.set_title("Fisher's engine: genetic correlation (linkage disequilibrium)")
    a.set_xlabel("generation"); a.set_ylabel("within-pop corr(ornament, preference)")
    a.legend(fontsize=9)

    fig.tight_layout()
    path = OUT / "sexsel.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
