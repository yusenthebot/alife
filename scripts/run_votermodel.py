"""R82 — The voter model: coarsening with and without surface tension.

The VOTER rule (copy a random neighbour) coarsens into rough, fractal opinion domains — no
surface tension; the MAJORITY rule (adopt the local majority) pulls boundaries straight into
smooth round domains that grow fast. The interface-density decay and the mean-opinion drift
distinguish the two.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.votermodel import run, ensemble_mag_drift  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r82_votermodel"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    steps = 600
    rv = run(180, steps, "voter", seed=0, record_every=300)
    rm = run(180, steps, "majority", seed=0, noise=0.03, record_every=300)
    print(f"interface @t={steps}: voter {rv['interface'][-1]:.3f}, majority {rm['interface'][-1]:.3f} "
          f"(majority < voter = surface tension)")

    fig = plt.figure(figsize=(16.5, 11))
    fig.suptitle("R82 — The voter model: coarsening WITHOUT surface tension (vs majority, WITH)",
                 fontsize=14, fontweight="bold")
    gs = fig.add_gridspec(3, 3, height_ratios=[1, 1, 0.9], hspace=0.3, wspace=0.1)
    keys = sorted(rv["snaps"])
    for c, k in enumerate(keys):
        ax = fig.add_subplot(gs[0, c]); ax.imshow(rv["snaps"][k], cmap="RdBu", vmin=-1, vmax=1)
        ax.set_title(f"VOTER  t={k}" + ("  — rough, fractal domains" if c == len(keys) - 1 else ""),
                     fontsize=9); ax.axis("off")
    for c, k in enumerate(keys):
        ax = fig.add_subplot(gs[1, c]); ax.imshow(rm["snaps"][k], cmap="RdBu", vmin=-1, vmax=1)
        ax.set_title(f"MAJORITY  t={k}" + ("  — smooth, round domains" if c == len(keys) - 1 else ""),
                     fontsize=9); ax.axis("off")

    ax = fig.add_subplot(gs[2, 0:2])
    ax.plot(rv["interface"], color="#e0245e", lw=2, label="voter (no surface tension)")
    ax.plot(rm["interface"], color="#1f7a1f", lw=2, label="majority (surface tension)")
    ax.set_title("Interface density (boundary length): majority collapses fast, voter crawls")
    ax.set_xlabel("step"); ax.set_ylabel("fraction of unlike bonds"); ax.legend(fontsize=9); ax.grid(alpha=0.25)

    ax = fig.add_subplot(gs[2, 2])
    vf = ensemble_mag_drift(96, 400, "voter", trials=14, seed=1)
    mf = ensemble_mag_drift(96, 400, "majority", trials=14, seed=1)
    ax.scatter(np.zeros_like(vf), vf, c="#e0245e", s=18, label=f"voter (mean {vf.mean():+.2f})")
    ax.scatter(np.ones_like(mf), mf, c="#1f7a1f", s=18, label=f"majority (mean {mf.mean():+.2f})")
    ax.axhline(0, color="#9aa0a6", ls=":", lw=1)
    ax.set_title("Mean opinion (14 runs):\nvoter driftless (conserved)", fontsize=9)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["voter", "majority"]); ax.set_ylabel("final magnetization")
    ax.set_ylim(-1.05, 1.05); ax.legend(fontsize=7)

    path = OUT / "votermodel.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
