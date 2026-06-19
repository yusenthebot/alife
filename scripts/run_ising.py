"""R85 — The Ising model: the order-disorder phase transition (Metropolis Monte Carlo).

Sweeping temperature, the spin lattice undergoes a sharp transition at T_c≈2.269: spontaneous
magnetisation below T_c (a global direction emerges from a symmetric rule), critical fluctuations
spanning all scales at T_c (the susceptibility diverges), and thermal disorder above.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.ising import sweep_temperature, run, TC  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r85_ising"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    T, M, X, E = sweep_temperature(size=64, temps=np.linspace(1.4, 3.4, 26), equil=400, measure=400, seed=0)
    tc_meas = T[np.argmax(X)]
    print(f"Onsager T_c={TC:.3f}; measured chi-peak T_c={tc_meas:.2f}; |M| {M[0]:.2f}->{M[-1]:.2f}")

    snaps = {Tlbl: run(160, Tv, sweeps=400, seed=1)["spin"]
             for Tlbl, Tv in [("ordered (T<Tc)", 1.8), ("critical (T≈Tc)", TC), ("disordered (T>Tc)", 3.0)]}

    fig = plt.figure(figsize=(16.5, 10))
    fig.suptitle("R85 — The Ising model: spontaneous magnetisation and the order-disorder phase transition",
                 fontsize=14, fontweight="bold")

    for c, (lbl, sp) in enumerate(snaps.items()):
        ax = fig.add_subplot(2, 3, c + 1)
        ax.imshow(sp, cmap="binary", vmin=-1, vmax=1, interpolation="nearest")
        ax.set_title(lbl, fontsize=10); ax.axis("off")

    ax = fig.add_subplot(2, 3, 4)
    ax.plot(T, M, "o-", color="#1d9bf0", lw=2)
    ax.axvline(TC, color="#e0245e", ls="--", lw=1.5, label=f"T_c ≈ {TC:.2f}")
    ax.set_title("Spontaneous magnetisation vanishes at T_c\n(order → disorder)")
    ax.set_xlabel("temperature T"); ax.set_ylabel("|magnetisation|"); ax.legend(fontsize=9); ax.grid(alpha=0.25)

    ax = fig.add_subplot(2, 3, 5)
    ax.plot(T, X, "o-", color="#e0245e", lw=2)
    ax.axvline(TC, color="#1d9bf0", ls="--", lw=1.5, label=f"T_c ≈ {TC:.2f}")
    ax.set_title("Susceptibility diverges at T_c\n(critical fluctuations at all scales)")
    ax.set_xlabel("temperature T"); ax.set_ylabel("χ = N·Var(m)/T"); ax.legend(fontsize=9); ax.grid(alpha=0.25)

    ax = fig.add_subplot(2, 3, 6)
    ax.plot(T, E, "o-", color="#1f7a1f", lw=2)
    ax.axvline(TC, color="#e0245e", ls="--", lw=1.5)
    ax.set_title("Energy per spin rises through the transition")
    ax.set_xlabel("temperature T"); ax.set_ylabel("energy / spin"); ax.grid(alpha=0.25)

    fig.tight_layout()
    path = OUT / "ising.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
