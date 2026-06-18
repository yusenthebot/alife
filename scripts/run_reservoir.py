"""R73 — Reservoir computing: a random recurrent net learns to dream the Lorenz attractor.

An Echo State Network (fixed random reservoir + trained linear readout) is driven by the Lorenz
system, then run closed-loop on its own output. It tracks the true chaotic trajectory for several
Lyapunov times before chaos separates them, and keeps tracing the same butterfly "climate".
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.reservoir import ESNConfig, fit_and_predict, valid_time  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r73_reservoir"
LYAP = 0.906


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = ESNConfig(n_res=800, spectral_radius=1.2, ridge=1e-6, leak=0.6)
    r = fit_and_predict(cfg, train_len=6000, predict_len=2000, dt=0.02, seed=0)
    g, t = r["gen"], r["true"]
    vt = valid_time(r["gen_n"], r["true_n"], r["dt"])
    tax = np.arange(len(g)) * r["dt"] * LYAP
    err = np.sqrt(np.mean((r["gen_n"] - r["true_n"]) ** 2, axis=1))
    print(f"valid prediction {vt:.1f} Lyapunov times; climate std gen {g.std(0).round(1)} vs true {t.std(0).round(1)}")

    fig = plt.figure(figsize=(16.5, 10))
    fig.suptitle("R73 — Reservoir computing: a random recurrent net learns to dream the Lorenz attractor",
                 fontsize=14, fontweight="bold")

    for k, (dim, lbl) in enumerate([(0, "x"), (2, "z")]):
        ax = fig.add_subplot(2, 3, k + 1)
        ax.plot(tax, t[:, dim], color="#1d9bf0", lw=1.6, label="true Lorenz")
        ax.plot(tax, g[:, dim], color="#e0245e", lw=1.2, ls="--", label="ESN free-run")
        ax.axvline(vt, color="#1f7a1f", ls=":", lw=1.5, label=f"valid ≈ {vt:.1f} λt")
        ax.set_title(f"{lbl}(t): tracks the true chaos, then diverges")
        ax.set_xlabel("Lyapunov time"); ax.set_ylabel(lbl); ax.legend(fontsize=8); ax.set_xlim(0, tax[-1])

    ax = fig.add_subplot(2, 3, 3)
    ax.semilogy(tax, err / (np.sqrt(np.mean(r["true_n"] ** 2)) + 1e-9), color="#9aa0a6", lw=1.5)
    ax.axhline(0.4, color="#e0245e", ls=":", lw=1)
    ax.set_title("Prediction error grows ~exponentially (chaos)")
    ax.set_xlabel("Lyapunov time"); ax.set_ylabel("normalised error (log)"); ax.grid(alpha=0.25, which="both")

    ax = fig.add_subplot(2, 3, 4)
    ax.plot(t[:, 0], t[:, 2], color="#1d9bf0", lw=0.5)
    ax.set_title("True Lorenz attractor (x–z)"); ax.set_xlabel("x"); ax.set_ylabel("z")
    ax.set_facecolor("#0a0a0f")

    ax = fig.add_subplot(2, 3, 5)
    ax.plot(g[:, 0], g[:, 2], color="#e0245e", lw=0.5)
    ax.set_title("ESN-generated attractor (x–z)\nsame butterfly 'climate', self-generated")
    ax.set_xlabel("x"); ax.set_ylabel("z"); ax.set_facecolor("#0a0a0f")

    ax = fig.add_subplot(2, 3, 6, projection="3d")
    ax.plot(g[:, 0], g[:, 1], g[:, 2], color="#ffd23f", lw=0.4)
    ax.set_title("ESN-generated butterfly (3D)")
    ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])

    fig.tight_layout()
    path = OUT / "reservoir.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
