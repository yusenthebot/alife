"""R45 — morphogenesis: Gray-Scott reaction-diffusion patterns.

Renders the classic regimes — spots that divide (mitosis), coral, stripes,
travelling waves — from the same two-chemical system, varying only feed/kill.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.reactiondiff import REGIMES, ReactionDiffConfig, pattern_strength, run_regime  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r45_reactiondiff"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = ReactionDiffConfig(steps=16000)

    fig, ax = plt.subplots(2, 2, figsize=(11, 11.6))
    fig.suptitle("R45 — morphogenesis: Turing patterns from two reacting chemicals (Gray-Scott)",
                 fontsize=14, fontweight="bold")
    for a, name in zip(ax.ravel(), REGIMES):
        r = run_regime(name, cfg, seed=0)
        F, k = REGIMES[name]
        a.imshow(r["V"], cmap="inferno", interpolation="bilinear")
        a.set_title(f"{name}  (F={F}, k={k})  ·  std(V)={pattern_strength(r['V']):.3f}", fontsize=10)
        a.set_xticks([]); a.set_yticks([])
        print(f"{name}: std(V)={pattern_strength(r['V']):.3f}")

    fig.tight_layout()
    path = OUT / "reactiondiff.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
