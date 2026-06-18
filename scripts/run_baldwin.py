"""R41 — the Baldwin effect (Hinton & Nowlan 1987).

Learning smooths a needle-in-a-haystack fitness landscape so evolution can climb
it; then the learned plasticity is genetically assimilated into fixed genes. With
learning the correct alleles sweep to fixation and the "?"s vanish; without
learning the population stays blind.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.baldwin import BaldwinConfig, evolve  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r41_baldwin"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = BaldwinConfig()
    L = evolve(cfg, learning=True, seed=0)
    N = evolve(cfg, learning=False, seed=0)
    gens = np.arange(cfg.generations + 1)

    print(f"learning: correct {L['correct'][0]:.2f}->{L['correct'][-1]:.2f}, "
          f"plastic {L['plastic'][0]:.2f}->{L['plastic'][-1]:.2f}, solvable -> {L['solvable'][-1]:.2f}")
    print(f"no-learning: correct {N['correct'][0]:.2f}->{N['correct'][-1]:.2f}, solvable -> {N['solvable'][-1]:.2f}")

    fig, ax = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle("R41 — the Baldwin effect: learning guides evolution, then is assimilated",
                 fontsize=14, fontweight="bold")

    a = ax[0, 0]
    a.plot(gens, L["correct"], color="#1b7a3d", lw=2, label="fixed-correct (1)")
    a.plot(gens, L["plastic"], color="#f5a623", lw=2, label="plastic (?)")
    a.plot(gens, L["wrong"], color="#e0245e", lw=2, label="fixed-wrong (0)")
    a.set_title("With learning: assimilation (? → fixed-correct)")
    a.set_xlabel("generation"); a.set_ylabel("allele frequency"); a.set_ylim(0, 1); a.legend(fontsize=9)

    a = ax[0, 1]
    a.plot(gens, L["solvable"], color="#1d9bf0", lw=2, label="with learning")
    a.plot(gens, N["solvable"], color="#e0245e", lw=2, label="no learning")
    a.set_title("Fraction of population that can reach the target")
    a.set_xlabel("generation"); a.set_ylabel("solvable fraction"); a.set_ylim(-0.02, 1.05); a.legend(fontsize=9)

    a = ax[1, 0]
    a.plot(gens, L["correct"], color="#1b7a3d", lw=2, label="with learning")
    a.plot(gens, N["correct"], color="#e0245e", lw=2, label="no learning")
    a.axhline(0.5, color="k", lw=0.8, ls=":", alpha=0.6, label="chance (blind)")
    a.set_title("Correct-allele frequency: learning lets selection climb")
    a.set_xlabel("generation"); a.set_ylabel("fixed-correct fraction"); a.legend(fontsize=9)

    a = ax[1, 1]
    a.plot(gens, L["max_fit"], color="#1d9bf0", lw=2, label="with learning")
    a.plot(gens, N["max_fit"], color="#e0245e", lw=2, label="no learning")
    a.set_title("Best fitness found (needle = 20)")
    a.set_xlabel("generation"); a.set_ylabel("max fitness"); a.legend(fontsize=9)

    fig.tight_layout()
    path = OUT / "baldwin.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
