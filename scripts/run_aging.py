#!/usr/bin/env python
"""Round 20 — evolution of aging (Medawar/Williams).

Evolves age-specific intrinsic survival under different extrinsic mortality and
shows senescence emerging — and setting in earlier when extrinsic mortality is
higher (the force of selection declines faster with age).

Artifacts into runs/<name>/:
  aging.png   evolved survival-by-age curves for several extrinsic mortalities
Usage:
  python scripts/run_aging.py --name aging
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

from alife.aging import AgingConfig, evolve  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--name", type=str, default="aging")
    args = ap.parse_args()
    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)
    cfg = AgingConfig()

    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    ages = np.arange(cfg.max_age)
    for m, color in [(0.05, "tab:blue"), (0.15, "tab:green"), (0.35, "tab:red")]:
        s = evolve(cfg, extrinsic_mortality=m, seed=args.seed)
        ax[0].plot(ages, s, "-o", ms=3, color=color, label=f"extrinsic mortality {m}")
        ax[1].plot(ages, 1 - s, "-o", ms=3, color=color, label=f"extrinsic mortality {m}")
    ax[0].set_title("Evolved intrinsic survival by age (senescence)")
    ax[0].set_xlabel("age"); ax[0].set_ylabel("intrinsic survival prob"); ax[0].set_ylim(0, 1.02)
    ax[0].grid(alpha=0.25); ax[0].legend()
    ax[1].set_title("Intrinsic mortality rises with age — faster under high extrinsic mortality")
    ax[1].set_xlabel("age"); ax[1].set_ylabel("intrinsic mortality (1 - survival)"); ax[1].set_ylim(0, 1.02)
    ax[1].grid(alpha=0.25); ax[1].legend()
    fig.suptitle("Evolution of aging: Williams' prediction — higher extrinsic mortality, earlier senescence", fontsize=13)
    fig.tight_layout(); fig.savefig(out / "aging.png", dpi=110); plt.close(fig)

    for m in (0.05, 0.35):
        s = evolve(cfg, extrinsic_mortality=m, seed=args.seed)
        onset = np.where(s < 0.5)[0]
        print(f"extrinsic m={m}: senescence onset age = {int(onset[0]) if onset.size else cfg.max_age}")
    print(f"Artifacts in {out}")


if __name__ == "__main__":
    main()
