"""R34 — in-situ predator-prey: a living two-species world (no GA).

Prey forage and must dodge predators; predators hunt prey. Both have brains,
energy, reproduction and death. A central Huffaker refuge keeps prey from total
collapse, so the two species coexist with boom-and-bust dynamics. Over time the
prey evolve EVASION (they move away from the nearest predator). Predators begin
competent at pursuit (their sensor points straight at prey) and stay that way —
an honestly asymmetric arms race, reported as the data shows it.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.predeco import PredEcoConfig, run  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r34_predeco"


def _smooth(x, k=7):
    x = np.nan_to_num(np.asarray(x, float))
    return np.convolve(x, np.ones(k) / k, mode="valid")


def _draw_world(a, snap, cfg, title):
    rc = cfg.world / 2.0
    a.add_patch(Circle((rc, rc), cfg.refuge_radius, color="#cfe8cf", alpha=0.6, zorder=1))
    f = snap["food"]
    if len(f):
        a.scatter(f[:, 0], f[:, 1], c="#2ecc71", s=6, alpha=0.6, zorder=2)
    pr = snap["prey"]
    if len(pr):
        a.quiver(pr[:, 0], pr[:, 1], np.cos(snap["preyh"]), np.sin(snap["preyh"]),
                 color="#1d9bf0", scale=40, width=0.004, alpha=0.8, zorder=3)
    pd = snap["pred"]
    if len(pd):
        a.quiver(pd[:, 0], pd[:, 1], np.cos(snap["predh"]), np.sin(snap["predh"]),
                 color="#e0245e", scale=32, width=0.006, alpha=0.95, zorder=4)
    a.set_title(title); a.set_xlim(0, cfg.world); a.set_ylim(0, cfg.world)
    a.set_aspect("equal"); a.set_xticks([]); a.set_yticks([])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = PredEcoConfig(steps=6000)
    r = run(cfg, seed=0, record_every=200)
    snaps = r["snaps"]

    ev = r["evasion"]; pu = r["pursuit"]
    print(f"coexist: prey {int(r['prey'].min())}-{int(r['prey'].max())}, "
          f"pred {int(r['pred'].min())}-{int(r['pred'].max())}")
    print(f"evasion {np.nanmean(ev[:8]):+.3f} -> {np.nanmean(ev[-15:]):+.3f}")
    print(f"pursuit {np.nanmean(pu[:8]):+.3f} -> {np.nanmean(pu[-15:]):+.3f}")

    fig, ax = plt.subplots(2, 2, figsize=(13, 11))
    fig.suptitle("R34 — in-situ predator–prey: coexistence + evolved prey evasion (no GA)",
                 fontsize=14, fontweight="bold")

    a = ax[0, 0]
    a.plot(r["t"], r["prey"], color="#1d9bf0", lw=1.6, label="prey")
    a.plot(r["t"], r["pred"], color="#e0245e", lw=1.6, label="predators")
    a.axhline(cfg.max_pred, color="#e0245e", lw=0.8, ls=":", alpha=0.5, label="predator cap")
    a.set_title("Two species coexist with boom-bust dynamics")
    a.set_xlabel("time step"); a.set_ylabel("population"); a.legend(fontsize=9)

    a = ax[0, 1]
    a.plot(r["t"], r["evasion"], color="#1d9bf0", lw=1, alpha=0.4)
    a.plot(r["t"][6:], _smooth(r["evasion"]), color="#0a3a5c", lw=2.5, label="prey evasion (trend)")
    a.plot(r["t"][6:], _smooth(r["pursuit"]), color="#e0245e", lw=2.5, label="predator pursuit (trend)")
    a.axhline(0, color="k", lw=0.8, ls=":", alpha=0.5)
    a.set_title("Prey EVOLVE evasion; predators start & stay good at pursuit")
    a.set_xlabel("time step"); a.set_ylabel("alignment to nearest (cos)"); a.legend(fontsize=9)

    _draw_world(ax[1, 0], snaps[1], cfg, f"Early (t={snaps[1]['t']})")
    _draw_world(ax[1, 1], snaps[-1], cfg, f"Late (t={snaps[-1]['t']}): prey flee & use the refuge")

    fig.tight_layout()
    path = OUT / "predeco.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
