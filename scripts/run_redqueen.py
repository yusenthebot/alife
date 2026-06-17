#!/usr/bin/env python
"""Round 22 — Red Queen host-parasite coevolution.

Shows allele frequencies oscillating forever (never converging) and parasites
lagging behind hosts — the Red Queen.

Artifacts into runs/<name>/:
  redqueen.png   host & parasite allele frequencies over time + host-vs-parasite lag
Usage:
  python scripts/run_redqueen.py --name redqueen
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

from alife.redqueen import RedQueenConfig, evolve, host_parasite_lag, oscillation_strength  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--name", type=str, default="redqueen")
    args = ap.parse_args()
    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)
    cfg = RedQueenConfig()
    H, P = evolve(cfg, seed=args.seed)

    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    for i in range(cfg.k):
        ax[0].plot(H[:, i], lw=1.4, label=f"host allele {i}")
    ax[0].set_title("Host allele frequencies oscillate forever (never converge)")
    ax[0].set_xlabel("generation"); ax[0].set_ylabel("frequency"); ax[0].set_ylim(0, 1)
    ax[0].grid(alpha=0.25); ax[0].legend(fontsize=8, ncol=2)

    ax[1].plot(H[:, 0], color="tab:blue", lw=1.8, label="host allele 0")
    ax[1].plot(P[:, 0], color="tab:red", lw=1.8, label="parasite allele 0 (chasing)")
    ax[1].set_title(f"Parasites lag hosts by ~{host_parasite_lag(H, P)} generations")
    ax[1].set_xlabel("generation"); ax[1].set_ylabel("frequency"); ax[1].set_ylim(0, 1)
    ax[1].grid(alpha=0.25); ax[1].legend(fontsize=9)
    fig.suptitle("Red Queen: host-parasite coevolution that never settles", fontsize=13)
    fig.tight_layout(); fig.savefig(out / "redqueen.png", dpi=110); plt.close(fig)

    print(f"oscillation std {oscillation_strength(H):.3f} | parasite lag {host_parasite_lag(H, P)} gens")
    print(f"Artifacts in {out}")


if __name__ == "__main__":
    main()
