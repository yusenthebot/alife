"""R77 — The evolution of cooperation: iterated Prisoner's Dilemma strategy evolution.

Memory-1 strategies, exact Markov-chain payoffs. An Axelrod tournament rewards reciprocity; under
error TFT is fragile (vendettas) while WSLS/Pavlov self-corrects; and in a well-mixed population
the evolution of cooperation is bistable — it can climb to cooperation or collapse to defection.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.ipd import NAMED, tournament, stationary_payoff, evolve  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r77_ipd"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    names, score, mean = tournament(NAMED)
    order = np.argsort(mean)[::-1]
    print("tournament:", [(names[i], round(mean[i], 2)) for i in order])

    eps = np.linspace(0.0, 0.2, 21)
    tft = [stationary_payoff(NAMED["TFT"], NAMED["TFT"], max(e, 1e-4))[2] for e in eps]
    wsls = [stationary_payoff(NAMED["WSLS"], NAMED["WSLS"], max(e, 1e-4))[2] for e in eps]

    runs = [evolve(pop_size=120, gens=160, seed=s) for s in range(8)]
    finals = np.array([r["coop"][-1] for r in runs])
    print(f"evolution finals (8 seeds): {finals.round(2)}  -> bistable (some coop, some defect)")

    fig = plt.figure(figsize=(16.5, 10))
    fig.suptitle("R77 — The evolution of cooperation: iterated Prisoner's Dilemma strategies",
                 fontsize=14, fontweight="bold")

    ax = fig.add_subplot(2, 2, 1)
    ax.barh([names[i] for i in order][::-1], [mean[i] for i in order][::-1], color="#1d9bf0")
    ax.axvline(1.0, color="#9aa0a6", ls=":", lw=1, label="all-defect payoff (P)")
    ax.axvline(3.0, color="#1f7a1f", ls=":", lw=1, label="all-cooperate (R)")
    ax.set_title("Axelrod tournament: reciprocators thrive\n(ALLD only wins by exploiting unconditional cooperators)")
    ax.set_xlabel("mean payoff vs the field"); ax.legend(fontsize=8)

    ax = fig.add_subplot(2, 2, 2)
    ax.plot(eps, tft, "o-", color="#e0245e", lw=2, label="TFT vs TFT")
    ax.plot(eps, wsls, "o-", color="#1f7a1f", lw=2, label="WSLS vs WSLS")
    ax.set_title("Noise breaks Tit-for-Tat (vendettas), not WSLS\n(self-correcting Pavlov stays cooperative)")
    ax.set_xlabel("implementation error rate"); ax.set_ylabel("cooperation rate")
    ax.set_ylim(0, 1.03); ax.legend(fontsize=8); ax.grid(alpha=0.25)

    ax = fig.add_subplot(2, 2, 3)
    for r in runs:
        c = r["coop"][-1]
        ax.plot(r["coop"], lw=1.5, color="#1f7a1f" if c > 0.5 else "#e0245e", alpha=0.7)
    ax.set_title("Well-mixed evolution is BISTABLE\n(green runs climb to cooperation, red collapse to defection)")
    ax.set_xlabel("generation"); ax.set_ylabel("mean cooperation"); ax.set_ylim(0, 1.03); ax.grid(alpha=0.25)

    ax = fig.add_subplot(2, 2, 4)
    coop_run = max(runs, key=lambda r: r["coop"][-1])
    comp = coop_run["composition"]; arch = coop_run["archetypes"]
    for k, a in enumerate(arch):
        ax.plot(comp[:, k], lw=2, label=a)
    ax.set_title("A cooperative run: ALLD dies out, reciprocators (TFT/WSLS/GRIM) take over")
    ax.set_xlabel("generation"); ax.set_ylabel("population fraction"); ax.legend(fontsize=8, ncol=2); ax.set_ylim(0, 1.03)

    fig.tight_layout()
    path = OUT / "ipd.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
