"""R59 — local adaptation at a million-genome scale (GPU spatial evolution).

A million agents across a world of biomes (a static trait-favouring field T) evolve
in situ by local selection. The genetic map comes to mirror the environmental map:
each region's population converges on its locally-favoured genotype.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.gpuecoevo import EcoEvoConfig, _T_numpy, run  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r59_gpuecoevo"


def _gene_map(arr, W, n=96):
    x, y, g = arr[:, 0], arr[:, 1], arr[:, 2]
    sm, _, _ = np.histogram2d(y, x, bins=n, range=[[0, W], [0, W]], weights=g)
    cnt, _, _ = np.histogram2d(y, x, bins=n, range=[[0, W], [0, W]])
    return sm / np.maximum(cnt, 1)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = EcoEvoConfig(n_agents=1_000_000, generations=120)
    r = run(cfg, seed=0, record_every=40)
    print(f"gene-environment correlation: {r['corr'][0]:.3f} -> {r['corr'][-1]:.3f}")
    keys = sorted(r["snaps"])

    fig, ax = plt.subplots(2, 2, figsize=(13, 12))
    fig.suptitle("R59 — local adaptation at a million-genome scale (GPU spatial evolution)",
                 fontsize=14, fontweight="bold")

    a = ax[0, 0]
    a.imshow(_T_numpy(cfg.world), cmap="coolwarm", origin="lower", vmin=0, vmax=1)
    a.set_title("The environment: T(x,y) — locally-favoured trait (biomes)")
    a.set_xticks([]); a.set_yticks([])

    a = ax[0, 1]
    a.imshow(_gene_map(r["final"], cfg.world), cmap="coolwarm", origin="lower", vmin=0, vmax=1)
    a.set_title(f"Evolved gene-map (gen {cfg.generations}): it MIRRORS the environment")
    a.set_xticks([]); a.set_yticks([])

    a = ax[1, 0]
    a.imshow(_gene_map(r["snaps"][keys[0]], cfg.world), cmap="coolwarm", origin="lower", vmin=0, vmax=1)
    a.set_title(f"Gene-map at gen {keys[0]}: random (no adaptation yet)")
    a.set_xticks([]); a.set_yticks([])

    a = ax[1, 1]
    a.plot(r["gen"], r["corr"], color="#1b7a3d", lw=2)
    a.set_title("Gene-environment correlation (local adaptation)")
    a.set_xlabel("generation"); a.set_ylabel("corr(gene, local T)"); a.set_ylim(0, 1.05)

    fig.tight_layout()
    path = OUT / "gpuecoevo.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
