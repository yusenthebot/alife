"""R61 — Particle Life: organisms from an asymmetric force matrix.

A random sprinkle of typed particles + a small asymmetric K x K attraction matrix +
hard short-range repulsion -> membranes, cells and wandering aggregates self-assemble.
Different matrices grow different artificial biota; an all-repulsive matrix stays a gas.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.particlelife import (  # noqa: E402
    ParticleLifeConfig, run, random_matrix, aggregation,
)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r61_particlelife"
COLORS = np.array([
    [0.93, 0.18, 0.34], [0.11, 0.61, 0.94], [0.30, 0.85, 0.39],
    [0.99, 0.77, 0.18], [0.72, 0.40, 0.95], [0.20, 0.85, 0.80],
])


def _scatter(ax, pos, typ, world, title, s=2.0):
    ax.scatter(pos[:, 0], pos[:, 1], c=COLORS[typ], s=s, linewidths=0)
    ax.set_xlim(0, world); ax.set_ylim(0, world)
    ax.set_title(title, fontsize=10); ax.set_xticks([]); ax.set_yticks([])
    ax.set_facecolor("#0a0a0f")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = ParticleLifeConfig(n=12000, types=5, steps=600)

    # one good matrix, recorded over time
    rng = np.random.default_rng(3)
    M = random_matrix(cfg.types, rng)
    r = run(cfg, M, seed=0, record_every=120)
    snaps = r["snaps"]; keys = sorted(snaps)
    dens = cfg.n / cfg.world ** 2
    exp_unif = dens * np.pi * (cfg.r_inner * 1.5) ** 2
    agg = aggregation(cfg, r)
    print(f"Particle Life {cfg.n} particles, {cfg.types} types, {cfg.steps} steps")
    print(f"aggregation {agg:.1f} neighbours vs uniform-gas {exp_unif:.1f} "
          f"-> {agg/exp_unif:.1f}x clumped into structures")

    # two more matrices -> distinct biota
    biota = []
    for s in (7, 11):
        Mi = random_matrix(cfg.types, np.random.default_rng(s))
        ri = run(cfg, Mi, seed=0)
        biota.append((s, ri, aggregation(cfg, ri)))

    # gas control: all-repulsive matrix -> no structure
    Mg = -np.abs(random_matrix(cfg.types, np.random.default_rng(1)))
    rg = run(cfg, Mg, seed=0)
    agg_gas = aggregation(cfg, rg)
    print(f"gas control (all-repulsive): aggregation {agg_gas:.1f} (~uniform = no structure)")

    fig, ax = plt.subplots(2, 3, figsize=(16.5, 11))
    fig.suptitle("R61 — Particle Life: organisms self-assemble from an asymmetric force matrix",
                 fontsize=14, fontweight="bold")
    _scatter(ax[0, 0], *snaps[keys[0]], cfg.world, f"t={keys[0]}: random sprinkle (gas)")
    _scatter(ax[0, 1], *snaps[keys[len(keys) // 2]], cfg.world,
             f"t={keys[len(keys)//2]}: structures condense")
    _scatter(ax[0, 2], r["pos"], r["typ"], cfg.world,
             f"t={cfg.steps}: organisms ({agg/exp_unif:.0f}x clumped)")
    _scatter(ax[1, 0], biota[0][1]["pos"], biota[0][1]["typ"], cfg.world,
             f"matrix B: distinct biota ({biota[0][2]/exp_unif:.0f}x)")
    _scatter(ax[1, 1], biota[1][1]["pos"], biota[1][1]["typ"], cfg.world,
             f"matrix C: distinct biota ({biota[1][2]/exp_unif:.0f}x)")
    _scatter(ax[1, 2], rg["pos"], rg["typ"], cfg.world,
             f"all-repulsive control: stays a gas ({agg_gas/exp_unif:.1f}x)")
    fig.tight_layout()
    path = OUT / "particlelife.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
