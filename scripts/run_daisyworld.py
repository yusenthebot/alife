"""R48 — Daisyworld: life regulates its planet (Watson & Lovelock 1983).

As the star brightens, black daisies (warming) give way to white daisies (cooling)
and hold the planetary temperature nearly constant — emergent homeostasis — while a
lifeless planet heats in lockstep with the sun. Regulation breaks only at extremes.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.daisyworld import DaisyConfig, luminosity_sweep  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r48_daisyworld"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = DaisyConfig()
    Ls = np.round(np.arange(0.6, 1.71, 0.02), 3)
    ta, td, b, w = luminosity_sweep(cfg, Ls)

    viable = (b + w) > 0.05
    print(f"regulated over L={Ls[viable].min()}-{Ls[viable].max()}; "
          f"temp std alive={ta[viable].std():.1f} vs dead={td[viable].std():.1f}")

    fig, ax = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("R48 — Daisyworld: life keeps its planet habitable (Gaia / homeostasis)",
                 fontsize=14, fontweight="bold")

    a = ax[0]
    a.plot(Ls, td, color="#888", lw=2, ls="--", label="bare planet (no life)")
    a.plot(Ls, ta, color="#1b7a3d", lw=2.5, label="Daisyworld (with life)")
    a.axhspan(5, 40, color="#2ecc71", alpha=0.08)
    a.axhline(22.5, color="#2ecc71", lw=0.8, ls=":", alpha=0.7, label="daisy optimum 22.5°C")
    a.set_title("Planetary temperature stays regulated as the sun brightens")
    a.set_xlabel("solar luminosity (×)"); a.set_ylabel("planet temperature (°C)"); a.legend(fontsize=9)

    a = ax[1]
    a.plot(Ls, b, color="#222", lw=2.5, label="black daisies (warm)")
    a.plot(Ls, w, color="#1d9bf0", lw=2.5, label="white daisies (cool)")
    a.fill_between(Ls, b, color="#222", alpha=0.12)
    a.fill_between(Ls, w, color="#1d9bf0", alpha=0.12)
    a.set_title("The mechanism: black→white handoff as it warms")
    a.set_xlabel("solar luminosity (×)"); a.set_ylabel("daisy coverage"); a.legend(fontsize=9)

    fig.tight_layout()
    path = OUT / "daisyworld.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
