"""R35 — evolution in a changing world: tracking a flipping environment.

Two food colours; only one nourishes at a time and which one FLIPS each season.
The population continually re-evolves which colour to chase. The signature is a
sawtooth in approach-bias: maladapted at every flip, re-adapted by season's end.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.ecoseasons import SeasonConfig, run  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r35_ecoseasons"


def _season_shade(a, cfg):
    for s in range(cfg.steps // cfg.season_len + 1):
        x0 = s * cfg.season_len
        a.axvspan(x0, x0 + cfg.season_len, color="#ffd9d9" if s % 2 == 0 else "#d9e4ff", alpha=0.5, lw=0)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = SeasonConfig()
    r = run(cfg, seed=0, record_every=500)

    ab = r["approach_bias"]
    print(f"population survives all flips: {int(r['pop'].min())}-{int(r['pop'].max())}")
    sl = cfg.season_len
    for s in range(1, cfg.steps // sl):
        a = int(s * sl / 50); b = int(((s + 1) * sl) / 50) - 1
        seg = ab[a:b]
        if len(seg) > 4:
            print(f"  flip {s}: approach-bias {np.nanmean(seg[:3]):+.2f} -> {np.nanmean(seg[-3:]):+.2f}")

    fig, ax = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle("R35 — evolution in a changing world: tracking a flipping environment (no GA)",
                 fontsize=14, fontweight="bold")

    a = ax[0, 0]
    _season_shade(a, cfg)
    a.plot(r["t"], r["approach_bias"], color="#222", lw=1.8)
    a.axhline(0, color="k", lw=0.8, ls=":", alpha=0.6)
    a.set_title("The sawtooth: maladapted at each flip, re-adapts by season end")
    a.set_xlabel("time step"); a.set_ylabel("approach-bias (toward good − toward bad)")
    a.text(0.01, 0.95, "pink=red nourishes · blue=blue nourishes", transform=a.transAxes, fontsize=8, va="top")

    a = ax[0, 1]
    _season_shade(a, cfg)
    a.plot(r["t"], r["good_frac"], color="#7d3cff", lw=1.2)
    a.axhline(0.5, color="k", lw=0.8, ls=":", alpha=0.6, label="chance")
    a.set_title("Fraction of meals from the good colour"); a.set_ylim(0, 1)
    a.set_xlabel("time step"); a.set_ylabel("good-meal fraction"); a.legend(fontsize=8)

    a = ax[1, 0]
    _season_shade(a, cfg)
    a.plot(r["t"], r["pop"], color="#1b7a3d", lw=1.8)
    a.set_title("Population survives every environmental flip")
    a.set_xlabel("time step"); a.set_ylabel("alive creatures")

    # snapshots: a red season vs a blue season (late in each, fully adapted)
    a = ax[1, 1]
    snaps = r["snaps"]
    red_snap = [s for s in snaps if s["good_is_red"]][-1]
    blue_snap = [s for s in snaps if not s["good_is_red"]][-1]
    snap = red_snap
    a.scatter(snap["red"][:, 0], snap["red"][:, 1], c="#e0245e", s=12, alpha=0.7, label="red food (good)")
    a.scatter(snap["blue"][:, 0], snap["blue"][:, 1], c="#1d9bf0", s=12, alpha=0.35, label="blue food (poison)")
    a.scatter(snap["pos"][:, 0], snap["pos"][:, 1], c="k", s=5, alpha=0.6, label="creatures")
    a.set_title(f"A red season (t={snap['t']}): creatures hug red, avoid blue")
    a.set_xticks([]); a.set_yticks([]); a.set_aspect("equal"); a.legend(fontsize=7, loc="upper right")

    fig.tight_layout()
    path = OUT / "ecoseasons.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
