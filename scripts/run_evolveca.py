"""R67 — Evolving cellular automata to COMPUTE (Mitchell-Crutchfield-Das).

The SYNCHRONIZATION task: a GA evolves a 1D CA's rule table so that, from ANY random start,
the whole lattice drives itself into a global blink-in-unison oscillation — and it does so via
emergent defect "particles" that travel and annihilate. Shown alongside the density-
classification task as the honest HARD sibling that the same GA cannot crack (no perfect local
rule exists). Computation discovered by evolution, not designed.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.evolveca import (  # noqa: E402
    CAConfig, evolve, fitness, sync_fitness, sync_rate, spacetime, random_rule,
    final_accuracy, hard_accuracy,
)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r67_evolveca"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = CAConfig(r=3, width=149)

    # --- synchronization task (the GA reliably solves this) ---
    rsync = evolve(cfg, pop_size=100, gens=50, n_ics=80, seed=2, fitness_fn=sync_fitness)
    sr = sync_rate(rsync["best"], cfg, 4000)
    sr0 = sync_rate(random_rule(np.random.default_rng(0), cfg.r), cfg, 4000)
    print(f"sync: random rule {sr0:.3f} -> evolved {sr:.3f}")

    # --- density classification (the hard sibling the GA cannot truly crack) ---
    # train on easy (uniform-density) ICs: the GA masters those yet still fails the hard global task
    rden = evolve(cfg, pop_size=80, gens=40, n_ics=100, seed=1,
                  fitness_fn=lambda rule, c, n, rng: fitness(rule, c, n, rng, hard_frac=0.0))
    easy = final_accuracy(rden["best"], cfg, 3000)
    hard = hard_accuracy(rden["best"], cfg, 3000)
    trivial = hard_accuracy(np.ones(1 << (2 * cfg.r + 1), np.int8), cfg, 3000)
    print(f"density: evolved easy={easy:.3f} HARD={hard:.3f}; trivial(all-1) hard={trivial:.3f}")

    fig = plt.figure(figsize=(16.5, 10))
    fig.suptitle("R67 — Evolving cellular automata to COMPUTE: a GA discovers global synchronization",
                 fontsize=14, fontweight="bold")

    seeds = [1, 5, 13]
    titles = ["random start → global SYNC", "another start → global SYNC",
              "a hard start → two out-of-phase domains (not yet)"]
    for c in range(3):
        ax = fig.add_subplot(2, 3, c + 1)
        st = spacetime(rsync["best"], cfg, density=0.5, steps=200, seed=seeds[c])
        ax.imshow(st, cmap="inferno", aspect="auto", interpolation="nearest")
        ax.set_title(titles[c], fontsize=9); ax.set_xlabel("cell"); ax.set_ylabel("time")

    ax = fig.add_subplot(2, 3, 4)
    h = rsync["history"]
    ax.plot(h[:, 0], color="#1d9bf0", lw=2, label="best")
    ax.plot(h[:, 1], color="#9aa0a6", lw=1.5, label="population mean")
    ax.set_title("Synchronization fitness evolves from chance to ~1")
    ax.set_xlabel("generation"); ax.set_ylabel("fraction of ICs synchronized")
    ax.set_ylim(0, 1.03); ax.legend(fontsize=8); ax.grid(alpha=0.25)

    ax = fig.add_subplot(2, 3, 5)
    ax.bar(["random\nrule", "evolved\nCA"], [sr0, sr], color=["#9aa0a6", "#1f7a1f"])
    ax.set_title(f"Held-out synchronization rate\n(evolved {sr:.0%} of random starts reach sync)")
    ax.set_ylabel("fraction synchronized"); ax.set_ylim(0, 1.03)

    ax = fig.add_subplot(2, 3, 6)
    ax.bar(["evolved\non EASY ICs", "same rule\non HARD ICs", "trivial\nbaseline"],
           [easy, hard, trivial], color=["#1f7a1f", "#e0245e", "#9aa0a6"])
    ax.axhline(0.5, color="#9aa0a6", ls=":", lw=1)
    ax.set_title("Density classification — the HARD sibling\n(GA masters easy ICs but FAILS the hard global task)")
    ax.set_ylabel("classification accuracy"); ax.set_ylim(0, 1.03)

    fig.tight_layout()
    path = OUT / "evolveca.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
