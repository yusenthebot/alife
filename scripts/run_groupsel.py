"""R42 — group selection and Simpson's paradox.

Cooperation falls within every group (defectors always out-reproduce cooperators
locally) yet rises in the whole population, because cooperator-rich groups out-
produce the rest. Assortment decides whether between-group selection beats within-
group selection.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from dataclasses import replace  # noqa: E402

from alife.groupsel import GroupSelConfig, assortment_sweep, evolve  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r42_groupsel"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = GroupSelConfig()
    hi = evolve(cfg, seed=0)
    lo = evolve(replace(cfg, assortment=0.0), seed=0)
    gens = np.arange(cfg.generations + 1)

    print(f"assorted: global coop {hi['coop_fraction'][0]:.2f} -> {hi['coop_fraction'][-1]:.2f}, "
          f"within-group dp mean {hi['within_group_dp'].mean():+.3f}")
    print(f"random:   global coop -> {lo['coop_fraction'][-1]:.2f}")

    asrt = np.round(np.arange(0, 0.51, 0.05), 2)
    sweep = assortment_sweep(cfg, asrt)

    fig, ax = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle("R42 — group selection: Simpson's paradox (up in the whole, down in every part)",
                 fontsize=14, fontweight="bold")

    a = ax[0, 0]
    a.plot(gens, hi["coop_fraction"], color="#1b7a3d", lw=2, label=f"assorted (a={cfg.assortment})")
    a.plot(gens, lo["coop_fraction"], color="#e0245e", lw=2, label="random groups (a=0)")
    a.axhline(0.5, color="k", lw=0.8, ls=":", alpha=0.6)
    a.set_title("GLOBAL cooperation: rises with assortment, collapses without")
    a.set_xlabel("generation"); a.set_ylabel("cooperator fraction"); a.set_ylim(0, 1); a.legend(fontsize=9)

    a = ax[0, 1]
    a.plot(np.arange(1, cfg.generations + 1), hi["within_group_dp"], color="#f5a623", lw=2)
    a.axhline(0, color="k", lw=0.8, ls=":", alpha=0.7)
    a.fill_between(np.arange(1, cfg.generations + 1), hi["within_group_dp"], 0,
                   color="#f5a623", alpha=0.2)
    a.set_title("WITHIN every group: cooperation always declines (Δ < 0)")
    a.set_xlabel("generation"); a.set_ylabel("mean within-group Δ(coop fraction)")

    a = ax[1, 0]
    a.plot(asrt, sweep, "o-", color="#1d9bf0", lw=2)
    a.set_title("Final cooperation vs assortment (the group-selection threshold)")
    a.set_xlabel("assortment"); a.set_ylabel("final cooperator fraction"); a.set_ylim(-0.02, 1.05)

    a = ax[1, 1]
    a.bar([0], [hi["coop_fraction"][-1] - hi["coop_fraction"][0]], width=0.5,
          color="#1b7a3d", label="global Δ (whole population)")
    a.bar([1], [hi["within_group_dp"].mean()], width=0.5,
          color="#f5a623", label="mean within-group Δ")
    a.axhline(0, color="k", lw=0.8)
    a.set_xticks([0, 1]); a.set_xticklabels(["whole", "every part"])
    a.set_title("The paradox in one view: + globally, − locally")
    a.set_ylabel("Δ cooperator fraction"); a.legend(fontsize=8)

    fig.tight_layout()
    path = OUT / "groupsel.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
