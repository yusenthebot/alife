"""R33 — the capstone: foraging behavior evolves in situ in one living world.

No generational GA — only life, death and reproduction. Brained creatures forage
in an energy-limited world; over generations they evolve directed foraging. Watch
the population self-regulate at a food-determined carrying capacity while its
behavior sharpens from random wandering into purposeful pursuit of food.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.ecosim import EcoConfig, run  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r33_ecosim"


def _draw_world(a, snap, cfg, title):
    f = snap["food"]
    a.scatter(f[:, 0], f[:, 1], c="#2ecc71", s=10, alpha=0.8, zorder=2, label="food")
    p = snap["pos"]; h = snap["head"]
    a.quiver(p[:, 0], p[:, 1], np.cos(h), np.sin(h), snap["gen"],
             cmap="plasma", scale=35, width=0.004, zorder=3)
    a.set_title(title); a.set_xlim(0, cfg.world); a.set_ylim(0, cfg.world)
    a.set_aspect("equal"); a.set_xticks([]); a.set_yticks([])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = EcoConfig()
    r = run(cfg, seed=1, record_every=200)
    snaps = r["snaps"]
    early = snaps[1]                     # t~200
    late = snaps[-1]                     # t~5800

    d = r["directedness"]
    print(f"directedness: early {np.nanmean(d[:5]):+.3f} -> late {np.nanmean(d[-10:]):+.3f}")
    print(f"population carrying capacity K ~ {int(np.mean(r['pop'][-20:]))} (cap {cfg.max_pop})")
    print(f"deepest lineage: generation {int(r['mean_gen'][-1])}")

    fig, ax = plt.subplots(2, 2, figsize=(13, 12))
    fig.suptitle("R33 — the capstone: foraging behavior evolves in situ (no GA, only life & death)",
                 fontsize=14, fontweight="bold")

    a = ax[0, 0]
    a.plot(r["t"], r["directedness"], color="#1d9bf0", lw=1.5)
    # smoothed trend
    k = 9
    sm = np.convolve(np.nan_to_num(r["directedness"]), np.ones(k) / k, mode="valid")
    a.plot(r["t"][k - 1:], sm, color="#0a3a5c", lw=2.5, label="trend")
    a.axhline(0, color="k", lw=0.8, ls=":", alpha=0.5)
    a.set_title("Behavior evolving: are they moving toward food?")
    a.set_xlabel("time step"); a.set_ylabel("directedness  (cos angle to food)"); a.legend(fontsize=9)

    a = ax[0, 1]
    a.plot(r["t"], r["pop"], color="#7d3cff", lw=2, label="population")
    a.axhline(cfg.max_pop, color="#e0245e", lw=1, ls="--", label=f"cap ({cfg.max_pop})")
    a.set_title("Population self-regulates at a food-limited carrying capacity")
    a.set_xlabel("time step"); a.set_ylabel("alive creatures"); a.set_ylim(0, cfg.max_pop * 1.05)
    a.legend(fontsize=9)

    _draw_world(ax[1, 0], early, cfg, f"Early (t={early['t']}): random wandering")
    _draw_world(ax[1, 1], late, cfg, f"Late (t={late['t']}): directed foraging, lineage gen "
                                     f"{int(late['gen'].mean())}")

    fig.tight_layout()
    path = OUT / "ecosim.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
