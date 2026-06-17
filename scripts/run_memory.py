#!/usr/bin/env python
"""Round 6 — recurrent (memory) brains, and an honest test of whether memory helps.

Evolves recurrent vs memoryless-control brains on central-place foraging (carry
food home to a nest that is only visible when near it) and plots the result.

Honest finding (see progress.md): across the memory tasks tried, evolved memory
did NOT robustly beat the reactive control — reactive foraging strategies stay
competitive and the small GA rarely discovers genuine memory use. This script
produces that comparison rather than a cherry-picked win.

Artifacts into runs/<name>/:
  memory_curves.png   fitness over generations, recurrent vs memoryless
  memory_heldout.png  held-out deposit per seed (the honest, ~parity result)

Usage:
  python scripts/run_memory.py --seeds 3 --name memory
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alife import sensors  # noqa: E402
from alife.brain import RecurrentSpec  # noqa: E402
from alife.evolve import EvolveConfig  # noqa: E402
from alife.memory import evolve_task, nest_forage  # noqa: E402
from alife.neuro import NeuroConfig  # noqa: E402
from alife.world import World  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--pop", type=int, default=160)
    ap.add_argument("--gens", type=int, default=50)
    ap.add_argument("--name", type=str, default="memory")
    args = ap.parse_args()

    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)
    cfg = replace(NeuroConfig(), world=World(240, 240, toroidal=True), sense_range=34.0)
    spec = RecurrentSpec(n_in=sensors.n_inputs(), n_hidden=12, n_out=2)
    ec = EvolveConfig(pop=args.pop, generations=args.gens, eval_steps=340, n_food=260)

    held = {True: [], False: []}
    curves = {True: [], False: []}
    for seed in range(args.seeds):
        for rec in (True, False):
            brains, hist = evolve_task(nest_forage, spec, cfg, ec, recurrent=rec, seed=seed, nest_sense=20.0)
            curves[rec].append(hist[:, 1])
            h = np.mean([nest_forage(brains[:30], spec, cfg, ec.n_food, 340, s, rec, nest_sense=20.0).mean()
                         for s in (55555, 66666, 77777)])
            held[rec].append(h)
            print(f"seed{seed} {'RNN' if rec else 'FF '}: held-out deposit {h:.2f}")

    # fitness curves (mean across seeds)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for rec, color, lbl in [(True, "tab:purple", "recurrent (memory)"), (False, "tab:gray", "memoryless control")]:
        m = np.mean(curves[rec], axis=0)
        ax.plot(m, color=color, lw=2, label=lbl)
    ax.set_title("Central-place foraging: recurrent vs memoryless (fitness over generations)")
    ax.set_xlabel("generation"); ax.set_ylabel("food deposited at nest")
    ax.grid(alpha=0.25); ax.legend()
    fig.tight_layout(); fig.savefig(out / "memory_curves.png", dpi=110); plt.close(fig)

    # held-out bars
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(args.seeds)
    ax.bar(x - 0.2, held[True], 0.4, color="tab:purple", label="recurrent")
    ax.bar(x + 0.2, held[False], 0.4, color="tab:gray", label="memoryless")
    ax.axhline(np.mean(held[True]), color="tab:purple", ls="--", lw=1)
    ax.axhline(np.mean(held[False]), color="tab:gray", ls="--", lw=1)
    ax.set_title(f"Held-out deposit (means: RNN {np.mean(held[True]):.1f} vs FF {np.mean(held[False]):.1f}) — reactive stays competitive")
    ax.set_xlabel("seed"); ax.set_ylabel("food deposited (held-out)")
    ax.set_xticks(x); ax.legend()
    fig.tight_layout(); fig.savefig(out / "memory_heldout.png", dpi=110); plt.close(fig)

    print(f"RECURRENT held mean {np.mean(held[True]):.2f} | memoryless held mean {np.mean(held[False]):.2f}")
    print(f"Artifacts in {out}")


if __name__ == "__main__":
    main()
