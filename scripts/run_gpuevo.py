"""R57 — natural selection at a million-genome scale (GPU evolution).

A million genomes on a rugged 4-peak fitness landscape, evolved by parallel
tournament selection on the GPU. With no gradient, the population discovers the
peaks and concentrates on the global optimum — selection at megascale.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.gpuevo import GLOBAL, PEAKS, GpuEvoConfig, run  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r57_gpuevo"


def _landscape(span):
    g = np.linspace(-span, span, 200)
    X, Y = np.meshgrid(g, g)
    F = np.zeros_like(X)
    for cx, cy, h, w in PEAKS:
        F += h * np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / (2 * w * w))
    return X, Y, F


def _show(a, genes, cfg, title):
    X, Y, F = _landscape(cfg.span)
    a.contourf(X, Y, F, levels=14, cmap="Greys")
    idx = np.linspace(0, len(genes) - 1, min(20000, len(genes))).astype(int)
    a.scatter(genes[idx, 0], genes[idx, 1], s=2, c="#e0245e", alpha=0.25)
    a.scatter([GLOBAL[0]], [GLOBAL[1]], marker="*", s=160, c="#1d9bf0", zorder=5)
    a.set_title(title); a.set_xlim(-cfg.span, cfg.span); a.set_ylim(-cfg.span, cfg.span)
    a.set_xticks([]); a.set_yticks([])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = GpuEvoConfig(n_agents=1_000_000, generations=60)
    r = run(cfg, seed=0, record_every=3)
    print(f"mean fitness {r['mean_fit'][0]:.3f} -> {r['mean_fit'][-1]:.3f}; "
          f"frac on global peak {r['frac_global'][0]:.2f} -> {r['frac_global'][-1]:.2f}; "
          f"{int(r['steps_per_s'])} gen/s at 1M genomes")
    snaps = r["snaps"]; keys = sorted(snaps)

    fig, ax = plt.subplots(2, 2, figsize=(13, 12))
    fig.suptitle("R57 — natural selection at a million-genome scale (GPU evolution)",
                 fontsize=14, fontweight="bold")
    _show(ax[0, 0], snaps[keys[0]], cfg, f"gen {keys[0]}: a million genomes scattered at random")
    mid = keys[len(keys) // 4]
    _show(ax[0, 1], snaps[mid], cfg, f"gen {mid}: peaks discovered (★ = global optimum)")

    a = ax[1, 0]
    a.plot(r["gen"], r["mean_fit"], color="#1b7a3d", lw=2, label="mean fitness")
    a.plot(r["gen"], r["max_fit"], color="#888", lw=1.5, ls="--", label="max fitness")
    a.axhline(max(p[2] for p in PEAKS), color="#1d9bf0", lw=0.8, ls=":", label="global optimum")
    a.set_title("Population climbs the rugged landscape")
    a.set_xlabel("generation"); a.set_ylabel("fitness"); a.legend(fontsize=9)

    a = ax[1, 1]
    a.plot(r["gen"], r["frac_global"], color="#e0245e", lw=2)
    a.set_title("Fraction of the million on the GLOBAL optimum")
    a.set_xlabel("generation"); a.set_ylabel("fraction"); a.set_ylim(0, 1.05)

    fig.tight_layout()
    path = OUT / "gpuevo.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
