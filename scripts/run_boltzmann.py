"""R81 — Restricted Boltzmann machine: a neural network learns to dream (Hinton).

Trained by contrastive divergence on bars-and-stripes images, the RBM learns the distribution
and, run as a Gibbs chain from noise, dreams new VALID bars/stripes it was never shown — while
an untrained net dreams only noise, and the hidden weights become bar/stripe detectors.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.boltzmann import (  # noqa: E402
    bars_and_stripes, train, init_rbm, gibbs_sample, valid_fraction, is_valid_bas,
)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r81_boltzmann"


def _montage(imgs, n, cols, rows):
    """Tile flattened n×n images into one (rows*(n+1), cols*(n+1)) array with separators."""
    g = np.full((rows * (n + 1) + 1, cols * (n + 1) + 1), 0.5)
    for k in range(min(len(imgs), rows * cols)):
        r, c = divmod(k, cols)
        g[1 + r * (n + 1):1 + r * (n + 1) + n, 1 + c * (n + 1):1 + c * (n + 1) + n] = imgs[k].reshape(n, n)
    return g


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    n = 4
    data = bars_and_stripes(n)
    rbm, err = train(data, n_hid=16, epochs=4000, lr=0.1, seed=0)
    rng = np.random.default_rng(0)
    untr = init_rbm(n * n, 16, rng)

    gen = gibbs_sample(rbm, 600, steps=300, seed=1)
    gen_un = gibbs_sample(untr, 600, steps=300, seed=1)
    vf, vf_un = valid_fraction(gen), valid_fraction(gen_un)
    n_distinct = len({tuple(s.tolist()) for s in gen if is_valid_bas(s)})
    print(f"trained dream valid-BAS {vf:.2f} ({n_distinct}/{len(data)} distinct); untrained {vf_un:.3f}; "
          f"random baseline {len(data)/2**(n*n):.4f}")

    # valid-fraction vs training budget
    budgets = [0, 100, 300, 700, 1500, 3000, 5000]
    curve = []
    for b in budgets:
        rb = init_rbm(n * n, 16, np.random.default_rng(0)) if b == 0 else train(data, 16, b, 0.1, seed=0)[0]
        curve.append(valid_fraction(gibbs_sample(rb, 300, steps=250, seed=2)))

    fig = plt.figure(figsize=(16.5, 10))
    fig.suptitle("R81 — Restricted Boltzmann machine: a neural network learns to dream (bars & stripes)",
                 fontsize=14, fontweight="bold")

    ax = fig.add_subplot(2, 3, 1)
    ax.imshow(_montage(data[rng.permutation(len(data))], n, 4, 4), cmap="magma", vmin=0, vmax=1)
    ax.set_title("Training data: bars-and-stripes"); ax.axis("off")

    ax = fig.add_subplot(2, 3, 2)
    ax.imshow(_montage(gen_un, n, 4, 4), cmap="magma", vmin=0, vmax=1)
    ax.set_title(f"UNTRAINED net dreams noise\n(valid {vf_un:.0%})"); ax.axis("off")

    ax = fig.add_subplot(2, 3, 3)
    ax.imshow(_montage(gen[[i for i in range(len(gen)) if is_valid_bas(gen[i])][:16] or [0]], n, 4, 4),
              cmap="magma", vmin=0, vmax=1)
    ax.set_title(f"TRAINED net dreams valid bars/stripes\n(valid {vf:.0%}, {n_distinct}/{len(data)} distinct)")
    ax.axis("off")

    ax = fig.add_subplot(2, 3, 4)
    feats = [rbm.W[:, j] for j in range(16)]
    ax.imshow(_montage(feats, n, 4, 4), cmap="coolwarm")
    ax.set_title("Hidden weights = learned bar/stripe detectors"); ax.axis("off")

    ax = fig.add_subplot(2, 3, 5)
    ax.plot(budgets, curve, "o-", color="#1f7a1f", lw=2)
    ax.axhline(len(data) / 2 ** (n * n), color="#9aa0a6", ls=":", lw=1, label="random baseline")
    ax.set_title("The net learns the distribution\n(valid-dream fraction vs training)")
    ax.set_xlabel("training updates"); ax.set_ylabel("fraction of dreams valid"); ax.set_ylim(0, 1.03)
    ax.legend(fontsize=8); ax.grid(alpha=0.25)

    ax = fig.add_subplot(2, 3, 6)
    ax.bar(["random", "untrained", "trained"], [len(data) / 2 ** (n * n), vf_un, vf],
           color=["#9aa0a6", "#e0245e", "#1f7a1f"])
    ax.set_title("Valid-dream fraction"); ax.set_ylabel("fraction"); ax.set_ylim(0, 1.03)

    fig.tight_layout()
    path = OUT / "boltzmann.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
