#!/usr/bin/env python
"""Round 17 — evolution of communication (Lewis signalling game).

From random sender/receiver maps, selection evolves a shared signalling
convention: signals acquire meaning, communication succeeds.

Artifacts into runs/<name>/:
  signals.png   communication success + mutual information(state;signal) over
                generations; final sender map (which signal means which state)
Usage:
  python scripts/run_signals.py --name signals
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

from alife.signals import SignalConfig, evolve  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--name", type=str, default="signals")
    args = ap.parse_args()
    out = Path(__file__).resolve().parent.parent / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)
    cfg = SignalConfig()

    senders, _, succ, mi = evolve(cfg, seed=args.seed)
    k = cfg.k

    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    ax[0].plot(succ, color="tab:green", lw=2, label="communication success")
    ax[0].axhline(1 / k, color="gray", ls="--", lw=1, label=f"chance ({1/k:.2f})")
    ax2 = ax[0].twinx()
    ax2.plot(mi, color="tab:purple", lw=2, label="mutual info I(state;signal)")
    ax2.axhline(np.log2(k), color="tab:purple", ls=":", lw=1, alpha=0.6)
    ax2.set_ylabel("bits", color="tab:purple")
    ax[0].set_title("Communication evolving from scratch")
    ax[0].set_xlabel("generation"); ax[0].set_ylabel("success", color="tab:green")
    ax[0].set_ylim(0, 1.05); ax[0].legend(loc="center right", fontsize=8)

    # final convention: P(signal | state) across the population
    conv = np.zeros((k, k))
    for s in range(k):
        for m in range(k):
            conv[s, m] = (senders[:, s] == m).mean()
    im = ax[1].imshow(conv, cmap="viridis", vmin=0, vmax=1)
    ax[1].set_title("Evolved convention: P(signal | state)")
    ax[1].set_xlabel("signal"); ax[1].set_ylabel("world state")
    ax[1].set_xticks(range(k)); ax[1].set_yticks(range(k))
    fig.colorbar(im, ax=ax[1], fraction=0.046)
    fig.tight_layout(); fig.savefig(out / "signals.png", dpi=110); plt.close(fig)

    print(f"success {succ[0]:.2f}->{succ[-1]:.2f} (chance {1/k:.2f}) | MI {mi[0]:.2f}->{mi[-1]:.2f} bits (max {np.log2(k):.2f})")
    print(f"Artifacts in {out}")


if __name__ == "__main__":
    main()
