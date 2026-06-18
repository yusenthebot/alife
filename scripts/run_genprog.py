"""R72 — Genetic programming: evolution rediscovers a hidden equation (Koza symbolic regression).

Given only (x, y) samples, a tree-GA evolves an expression made of + - * / sin cos and x that
reproduces the data — often recovering the exact formula. The genotype is a program; the search
space is open-ended in size and shape.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.genprog import evolve, eval_tree, stringify  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r72_genprog"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    x = np.linspace(-3, 3, 40)
    targets = [
        ("x² + sin(2x)", x ** 2 + np.sin(2 * x)),
        ("x³ − x² + x", x ** 3 - x ** 2 + x),
        ("x³/3 − x", x ** 3 / 3 - x),
    ]
    runs = []
    for name, y in targets:
        r = evolve(x, y, pop_size=500, gens=60, seed=1)
        runs.append((name, y, r))
        print(f"{name:14s}: RMSE {r['rmse']:.3f}  ->  {stringify(r['best'])[:80]}")

    fig = plt.figure(figsize=(16.5, 10))
    fig.suptitle("R72 — Genetic programming: evolution rediscovers a hidden equation (symbolic regression)",
                 fontsize=14, fontweight="bold")

    for k in range(2):
        name, y, r = runs[k]
        ax = fig.add_subplot(2, 2, k + 1)
        ax.scatter(x, y, s=28, c="#1d9bf0", label="hidden function (data)", zorder=3)
        ax.plot(x, eval_tree(r["best"], x), color="#e0245e", lw=2, label="evolved program")
        expr = stringify(r["best"])
        ax.set_title(f"target {name}   (RMSE {r['rmse']:.3f})\nevolved: {expr[:64]}", fontsize=9)
        ax.set_xlabel("x"); ax.set_ylabel("y"); ax.legend(fontsize=8); ax.grid(alpha=0.25)

    ax = fig.add_subplot(2, 2, 3)
    for name, y, r in runs:
        ax.semilogy(r["history"][:, 0] + 1e-6, lw=2, label=name)
    ax.set_title("Error falls as evolution finds the formula")
    ax.set_xlabel("generation"); ax.set_ylabel("best RMSE (log)"); ax.legend(fontsize=8); ax.grid(alpha=0.25, which="both")

    ax = fig.add_subplot(2, 2, 4)
    for name, y, r in runs:
        ax.plot(r["history"][:, 1], lw=2, label=name)
    ax.set_title("Program size over generations\n(parsimony pressure curbs bloat)")
    ax.set_xlabel("generation"); ax.set_ylabel("nodes in best program"); ax.legend(fontsize=8); ax.grid(alpha=0.25)

    fig.tight_layout()
    path = OUT / "genprog.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
