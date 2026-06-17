"""R31 — evolving morphology: virtual creatures evolve a body and a gait.

Co-evolves a 2D mass-spring body + its muscle phases for locomotion. Selection
rewards only horizontal distance; the morphology and gait are discovered.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.morphevo import (  # noqa: E402
    I_IDX,
    J_IDX,
    MorphConfig,
    N_NODES,
    evolve,
    simulate,
    _decode,
)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r31_morphevo"


def _draw_creature(a, frame, amp, alpha, color):
    for m, (i, j) in enumerate(zip(I_IDX, J_IDX)):
        lw = 0.8 + 3.0 * abs(amp[m])          # muscles (high amp) drawn thicker
        a.plot([frame[i, 0], frame[j, 0]], [frame[i, 1], frame[j, 1]],
                color=color, lw=lw, alpha=alpha, solid_capstyle="round")
    a.scatter(frame[:, 0], frame[:, 1], s=18, c="k", alpha=alpha, zorder=5)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = MorphConfig()

    res = evolve(cfg, seed=0)
    best = res["best_genome"]
    disp, frames, _ = simulate(best[None, :], cfg, record=True)
    _, amp, _ = _decode(best[None, :], cfg)
    amp = amp[0]
    com_x = np.array([f[:, 0].mean() for f in frames])
    com_y = np.array([f[:, 1].mean() for f in frames])
    print(f"evolved best distance = {res['best'][-1]:.1f} (gen0 {res['best'][0]:.1f})")
    print(f"COM x: {com_x[0]:.1f} -> {com_x[-1]:.1f}; monotone fraction = "
          f"{np.mean(np.diff(com_x) * np.sign(com_x[-1] - com_x[0]) > 0):.2f}")

    fig, ax = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("R31 — evolving morphology: a body and a gait, both evolved",
                 fontsize=15, fontweight="bold")

    # 1) gait snapshots marching across the ground
    a = ax[0, 0]
    n_snap = 7
    idx = np.linspace(0, len(frames) - 1, n_snap).astype(int)
    cmap = plt.get_cmap("viridis")
    for s, fi in enumerate(idx):
        _draw_creature(a, frames[fi], amp, alpha=0.35 + 0.65 * s / (n_snap - 1),
                       color=cmap(s / (n_snap - 1)))
    a.axhline(0, color="#8b5a2b", lw=2)
    a.set_title("Evolved gait: snapshots marching across the ground")
    a.set_xlabel("x"); a.set_ylabel("y"); a.set_aspect("equal")

    # 2) COM trajectory over time (progressive locomotion, not a single lurch)
    a = ax[0, 1]
    ts = np.arange(len(frames)) * cfg.dt
    a.plot(ts, com_x - com_x[0], color="#1d9bf0", lw=2, label="horizontal (x)")
    a.plot(ts, com_y, color="#e0245e", lw=1.5, alpha=0.7, label="height (y)")
    a.set_title("Centre-of-mass over time")
    a.set_xlabel("time (s)"); a.set_ylabel("displacement"); a.legend(fontsize=9)

    # 3) fitness over generations
    a = ax[1, 0]
    gens = np.arange(cfg.generations)
    a.plot(gens, res["best"], color="#1d9bf0", lw=2, label="best")
    a.plot(gens, res["mean"], color="#888", lw=1.5, label="population mean")
    a.set_title("Locomotion distance over evolution")
    a.set_xlabel("generation"); a.set_ylabel("horizontal distance"); a.legend(fontsize=9)

    # 4) diversity of evolved bodies: final-distance distribution across seeds
    a = ax[1, 1]
    rng = np.random.default_rng(7)
    finals = []
    for sd in range(6):
        finals.append(evolve(MorphConfig(generations=80), seed=sd)["best"][-1])
    a.bar(range(len(finals)), finals, color="#7d3cff")
    a.axhline(np.mean(finals), color="k", ls="--", lw=1, label=f"mean {np.mean(finals):.1f}")
    a.set_title("Evolved locomotion distance across 6 independent runs")
    a.set_xlabel("run (seed)"); a.set_ylabel("best distance"); a.legend(fontsize=9)

    fig.tight_layout()
    path = OUT / "morphevo.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
