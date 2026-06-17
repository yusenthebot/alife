"""R26 — the memory win: evolve FF vs RNN on a task where memory provably wins.

Delayed-cue latch: a cue at t=0, then blanks, then a decision step whose observation
is identical for both cue directions. Feedforward brains are pinned at chance (0.5)
by construction; recurrent brains latch the cue and reach ~1.0. This is the rematch
for R6's honest negative (alife/memory.py) — with a task that actually requires memory.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.memory_task import (  # noqa: E402
    MemoryTaskConfig,
    delay_sweep,
    evolve,
    hidden_trace,
)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r26_memory"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = MemoryTaskConfig(delay=4, generations=120)

    seeds = list(range(5))
    ff_seeds = np.array([evolve(cfg, recurrent=False, seed=s).held_out for s in seeds])
    rnn_results = [evolve(cfg, recurrent=True, seed=s) for s in seeds]
    rnn_seeds = np.array([r.held_out for r in rnn_results])
    ff = evolve(cfg, recurrent=False, seed=0)
    rnn = rnn_results[0]

    delays = np.array([1, 2, 4, 8, 16, 32])
    ff_sw, rnn_sw = delay_sweep(MemoryTaskConfig(generations=120), delays, seed=0)

    tr_pos = hidden_trace(rnn, +1.0, cfg.delay)
    tr_neg = hidden_trace(rnn, -1.0, cfg.delay)

    print(f"delay={cfg.delay} (5 seeds): FF held-out={ff_seeds.mean():.2f}+-{ff_seeds.std():.2f} (chance) "
          f"| RNN held-out={rnn_seeds.mean():.2f}+-{rnn_seeds.std():.2f}")
    print(f"delay sweep   FF : {dict(zip(delays.tolist(), np.round(ff_sw,2).tolist()))}")
    print(f"delay sweep   RNN: {dict(zip(delays.tolist(), np.round(rnn_sw,2).tolist()))}")
    sep = np.linalg.norm(tr_pos - tr_neg, axis=1)
    print(f"hidden-state separation (||h+ - h-||) over time: {np.round(sep,2).tolist()}")

    fig, ax = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle("R26 — the memory win: a task where reactive brains provably fail",
                 fontsize=15, fontweight="bold")

    a = ax[0, 0]
    a.bar([0], [rnn_seeds.mean()], color="#1d9bf0", width=0.6, label="RNN (memory)")
    a.bar([1], [ff_seeds.mean()], color="#e0245e", width=0.6, label="FF (reactive)")
    a.scatter(np.zeros_like(rnn_seeds), rnn_seeds, color="#0a3a5c", zorder=3, s=25)
    a.scatter(np.ones_like(ff_seeds), ff_seeds, color="#5c0a1a", zorder=3, s=25)
    a.axhline(0.5, color="k", lw=0.8, ls=":", alpha=0.6, label="chance")
    a.set_xticks([0, 1]); a.set_xticklabels(["RNN", "FF"])
    a.set_ylim(0.4, 1.05); a.set_title(f"Held-out accuracy, 5 seeds (delay={cfg.delay})")
    a.set_ylabel("held-out accuracy"); a.legend(fontsize=9)

    a = ax[0, 1]
    a.plot(delays, rnn_sw, "o-", color="#1d9bf0", lw=2, label="RNN (memory)")
    a.plot(delays, ff_sw, "o-", color="#e0245e", lw=2, label="FF (reactive)")
    a.axhline(0.5, color="k", lw=0.8, ls=":", alpha=0.6)
    a.set_xscale("log", base=2); a.set_ylim(0.4, 1.05)
    a.set_title("Held-out accuracy vs memory delay")
    a.set_xlabel("delay (blank steps, log2)"); a.set_ylabel("held-out accuracy"); a.legend(fontsize=9)

    a = ax[1, 0]
    a.plot(np.arange(len(sep)), sep, "o-", color="#7d3cff", lw=2)
    a.axvspan(-0.3, 0.3, color="orange", alpha=0.2)
    a.text(0.0, sep.max() * 0.95, "cue", ha="center", fontsize=9, color="darkorange")
    a.axvspan(len(sep) - 1.3, len(sep) - 0.7, color="green", alpha=0.15)
    a.text(len(sep) - 1, sep.max() * 0.95, "decide", ha="center", fontsize=9, color="green")
    a.set_title("Memory made visible: hidden state holds the cue")
    a.set_xlabel("time step"); a.set_ylabel("||h(cue=+1) - h(cue=-1)||")

    a = ax[1, 1]
    im = a.imshow(np.vstack([tr_pos.T, np.full((1, tr_pos.shape[0]), np.nan), tr_neg.T]),
                  aspect="auto", cmap="RdBu", vmin=-1, vmax=1)
    a.set_title("Evolved RNN hidden units (top: cue +1, bottom: cue -1)")
    a.set_xlabel("time step"); a.set_ylabel("hidden unit")
    fig.colorbar(im, ax=a, fraction=0.046, pad=0.04)

    fig.tight_layout()
    path = OUT / "memory.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
