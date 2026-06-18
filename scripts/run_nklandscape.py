"""R76 — NK fitness landscapes (Kauffman): ruggedness, trapping, and the complexity catastrophe.

One knob K (epistasis) tunes a genome's fitness landscape from a single smooth peak (K=0, any
hill-climb finds the global optimum) to an exponentially rugged mountain range where adaptive
walks get trapped on ever-poorer local optima — the complexity catastrophe.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.nklandscape import survey, make_landscape, adaptive_walk  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r76_nklandscape"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    N = 15
    Ks = [0, 1, 2, 4, 6, 8, 11, 14]
    rows = survey(N, Ks, walks=120, instances=5, seed=1)
    K = np.array([r["K"] for r in rows])
    nopt = np.array([r["n_optima"] for r in rows])
    fg = np.array([r["frac_global"] for r in rows])
    reached = np.array([r["mean_opt"] for r in rows])
    gopt = np.array([r["global"] for r in rows])
    print("K, #optima, frac_global, reached, global, gap")
    for r in rows:
        print(f"  {r['K']:2d} {r['n_optima']:7.0f} {r['frac_global']:.2f} {r['mean_opt']:.3f} "
              f"{r['global']:.3f} {r['global']-r['mean_opt']:.3f}")

    fig = plt.figure(figsize=(16.5, 10))
    fig.suptitle("R76 — NK fitness landscapes (Kauffman): ruggedness, trapping & the complexity catastrophe",
                 fontsize=14, fontweight="bold")

    ax = fig.add_subplot(2, 2, 1)
    ax.semilogy(K, np.maximum(nopt, 1), "o-", color="#1d9bf0", lw=2)
    ax.set_title("Ruggedness explodes: # local optima vs epistasis K")
    ax.set_xlabel("epistasis K"); ax.set_ylabel("number of local optima (log)"); ax.grid(alpha=0.25, which="both")

    ax = fig.add_subplot(2, 2, 2)
    ax.plot(K, fg, "o-", color="#e0245e", lw=2)
    ax.set_title("Adaptive walks get TRAPPED:\nfraction reaching the global optimum")
    ax.set_xlabel("epistasis K"); ax.set_ylabel("fraction reaching global"); ax.set_ylim(0, 1.03); ax.grid(alpha=0.25)

    ax = fig.add_subplot(2, 2, 3)
    ax.plot(K, gopt, "o-", color="#1f7a1f", lw=2, label="global optimum (exists)")
    ax.plot(K, reached, "o-", color="#e0245e", lw=2, label="reached by adaptive walk")
    ax.fill_between(K, reached, gopt, color="#e0245e", alpha=0.12)
    ax.set_title("Complexity catastrophe: the gap between what EXISTS\nand what evolution can REACH widens with K")
    ax.set_xlabel("epistasis K"); ax.set_ylabel("fitness"); ax.legend(fontsize=8); ax.grid(alpha=0.25)

    ax = fig.add_subplot(2, 2, 4)
    rng = np.random.default_rng(7)
    for Kd, col in [(0, "#1f7a1f"), (2, "#1d9bf0"), (14, "#e0245e")]:
        L = make_landscape(N, Kd, seed=10 + Kd)
        for w in range(5):
            _, tr = adaptive_walk(L, rng.integers(0, 2, N).astype(np.int8))
            ax.plot(tr, color=col, lw=1.4, alpha=0.7, label=f"K={Kd}" if w == 0 else None)
    ax.set_title("Adaptive walks: climb then stall at a local optimum\n(higher K → shorter climb, lower peak)")
    ax.set_xlabel("hill-climb step"); ax.set_ylabel("fitness"); ax.legend(fontsize=8); ax.grid(alpha=0.25)

    fig.tight_layout()
    path = OUT / "nklandscape.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
