#!/usr/bin/env python
"""Round 18 — evolution of evolvability: the mutation rate itself evolves.

Static environment vs moving optimum, plotting how the evolved mutation rate
(sigma) diverges: down in stability, high under change.

Artifacts into runs/<name>/:
  evolvability.png   median sigma + mean fitness over generations, static vs moving
Usage:
  python scripts/run_evolvability.py --name evolvability
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alife.evolvability import EvolvabilityConfig, evolve  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--name", type=str, default="evolvability")
    args = ap.parse_args()
    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)
    cfg = EvolvabilityConfig()

    s_static, f_static = evolve(cfg, moving=False, seed=args.seed)
    s_moving, f_moving = evolve(cfg, moving=True, seed=args.seed)

    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    ax[0].plot(s_static, color="tab:blue", lw=2, label="static environment")
    ax[0].plot(s_moving, color="tab:red", lw=2, label="moving optimum")
    ax[0].set_title("Evolved mutation rate (sigma) over generations")
    ax[0].set_xlabel("generation"); ax[0].set_ylabel("median sigma (mutation rate)")
    ax[0].grid(alpha=0.25); ax[0].legend()
    ax[1].plot(f_static, color="tab:blue", lw=2, label="static")
    ax[1].plot(f_moving, color="tab:red", lw=2, label="moving")
    ax[1].set_title("Mean fitness over generations")
    ax[1].set_xlabel("generation"); ax[1].set_ylabel("fitness"); ax[1].set_ylim(0, 1.05)
    ax[1].grid(alpha=0.25); ax[1].legend()
    fig.suptitle("Evolution of evolvability: mutation rate falls in stability, stays high under change", fontsize=13)
    fig.tight_layout(); fig.savefig(out / "evolvability.png", dpi=110); plt.close(fig)

    print(f"STATIC sigma -> {s_static[-1]:.3f} (fit {f_static[-1]:.2f}) | MOVING sigma -> {s_moving[-1]:.3f} (fit {f_moving[-1]:.2f})")
    print(f"Artifacts in {out}")


if __name__ == "__main__":
    main()
