"""R66 — The edge of chaos: searching the SPACE of cellular-automaton rules.

As Langton's lambda rises, 2D life-like CA dynamics cross from ORDERED (freeze/die) through
a narrow COMPLEX regime (Conway-like worlds with gliders and structures) into CHAOS (noise).
Complex rules are RARE and live only at intermediate lambda — the edge of chaos — and a blind
search of the rule space rediscovers Life-like worlds there.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.edgeofchaos import (  # noqa: E402
    Rule, CONWAY, lam, run, metrics, lambda_sweep, search_complex_rules,
)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r66_edgeofchaos"

ORDERED = Rule((4,), (2, 3, 4))             # freezes to sparse static structures
CHAOTIC = Rule((2, 3), (5, 6, 7, 8))        # boils into noise


def _grid(ax, rule, title, seed=0):
    r = run(rule, size=120, steps=200, seed=seed)
    m = metrics(rule, steps=200, seed=seed)
    ax.imshow(r["grid"], cmap="binary", interpolation="nearest")
    ax.set_title(f"{title}\nB{rule.born}/S{rule.survive}  λ={lam(rule):.2f}  "
                 f"act={m['activity']:.2f} dens={m['density']:.2f}", fontsize=9)
    ax.set_xticks([]); ax.set_yticks([])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    lams, A, D, F = lambda_sweep(np.linspace(0.05, 0.95, 19), per_lambda=28, seed=1)
    top, all_lam = search_complex_rules(n_samples=1800, seed=0, top=6)
    edge = lams[np.argmax(F)]
    print(f"frac-complex peaks at lambda={edge:.2f}; Conway lambda={lam(CONWAY):.2f}")
    print("discovered complex rules:")
    for c, rule, m in top:
        print(f"  B{rule.born}/S{rule.survive} lambda={m['lambda']:.2f} cx={c:.2f}")

    fig = plt.figure(figsize=(16.5, 10))
    fig.suptitle("R66 — The edge of chaos: complex CA worlds live between order and chaos (Langton's λ)",
                 fontsize=14, fontweight="bold")

    _grid(fig.add_subplot(2, 3, 1), ORDERED, "ORDERED: freezes to static")
    _grid(fig.add_subplot(2, 3, 2), CONWAY, "COMPLEX: Conway's Life (gliders, structures)")
    _grid(fig.add_subplot(2, 3, 3), CHAOTIC, "CHAOTIC: boils into noise")

    ax = fig.add_subplot(2, 3, 4)
    ax.plot(lams, D, "o-", color="#1d9bf0", lw=2, label="density")
    ax.plot(lams, A, "o-", color="#9aa0a6", lw=1.5, label="activity")
    ax.set_title("Order parameter: dynamics fill up as λ rises")
    ax.set_xlabel("Langton's λ = (|B|+|S|)/18"); ax.set_ylabel("steady-state value")
    ax.legend(fontsize=8); ax.grid(alpha=0.25)

    ax = fig.add_subplot(2, 3, 5)
    ax.fill_between(lams, F, color="#e0245e", alpha=0.35)
    ax.plot(lams, F, "o-", color="#e0245e", lw=2)
    ax.axvline(lam(CONWAY), color="#1f7a1f", ls="--", lw=1.5, label=f"Conway λ={lam(CONWAY):.2f}")
    ax.set_title("Complexity is RARE and lives at the EDGE\n(fraction of random rules that are complex)")
    ax.set_xlabel("Langton's λ"); ax.set_ylabel("fraction complex"); ax.legend(fontsize=8); ax.grid(alpha=0.25)

    _grid(fig.add_subplot(2, 3, 6), top[0][1],
          "DISCOVERED by blind search:\na new Life-like world at the edge")

    fig.tight_layout()
    path = OUT / "edgeofchaos.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
