"""R180 — GENESIS functional signalling: a DIVISION OF COGNITIVE LABOUR over a NON-STATIONARY world.

R179 proved a learned Lewis convention EMERGES — but over a PRIVATE RANDOM referent bit: no shared world,
no roles, "decode the bit" had no consequence beyond an abstract reward. R180 makes the channel do real WORK
(the Stage-2 -> Stage-3 bridge):
  - a SHARED environmental good-type g_t in {0,1} that FLIPS each step (prob task_flip) -> the world is
    NON-STATIONARY, so no constant policy can win and communication is load-bearing every step;
  - a stable DIVISION OF LABOUR: each agent is a SCOUT (observes g_t) or a BLIND FORAGER (g_t masked to 0);
    a forager can learn the current good-type ONLY by decoding a scout's signal;
  - a correct forager decode pays the foraging reward (real energy -> birth/death), so a blind sub-population
    tracks a changing world and EARNS only through others' signals = functional cooperation.

THE CLAIM (run it, read the figure): with within-lifetime learning (signal_lr>0) the foragers' decode
TRACKS the flipping good-type WELL above chance; the one-knob control (signal_lr=0, urns frozen) cannot
track the flips and stays pinned at chance. The lr=0 control is the adversarial null; robustness across 3
seeds + the tracking overlay (foragers' aggregate decode follows the true g_t step) are the red-team.
禁止造假 — the figure shows the truth, including the honest convention-strength spread.
"""
import os
import time
from dataclasses import replace

import numpy as np

from alife.genesis.genesis import GenesisWorld, GenesisConfig
from alife.world3d import World3D

OUT = "runs/r180_signal_task"


def cfg(lr):
    base = GenesisConfig(world=World3D(size=75.0), capacity=1200, n0=700,
                         food_cap=220, food_regrow=10, persist_steps=50)
    return replace(base, signalling=True, signal_game=True, signal_learn=True, signal_task=True,
                   task_flip=0.03, signal_lr=lr)


def run_arm(tag, lr, steps, seed, sample=20, track=False):
    """Run one arm, sampling forager task_success. If track, also record per-step true g_t + forager decode."""
    w = GenesisWorld(cfg(lr), seed=seed, evolve=True)
    xs, succ, pop = [], [], []
    g_hist, dec_hist = [], []
    for i in range(steps):
        w.step()
        if track:
            g_hist.append(w._good_type)
            dec_hist.append(w._last_forager_decode)
        if (i + 1) % sample == 0:
            s = w._last_task_success
            xs.append(i + 1)
            succ.append(s if s == s else np.nan)
            pop.append(int(w.pop.active().size))
    succ = np.array(succ, dtype=float)
    tail = float(np.nanmean(succ[-15:]))
    print(f"  {tag:14s} lr={lr} seed={seed}: tail task_success {tail:.3f} | "
          f"range [{np.nanmin(succ):.3f},{np.nanmax(succ):.3f}] pop {pop[-1]}", flush=True)
    return {"x": np.array(xs), "succ": succ, "pop": np.array(pop), "tail": tail,
            "g": np.array(g_hist), "dec": np.array(dec_hist)}


def smooth(a, k=15):
    a = np.asarray(a, dtype=float)
    out = np.full_like(a, np.nan)
    for i in range(len(a)):
        lo = max(0, i - k + 1)
        seg = a[lo:i + 1]
        seg = seg[~np.isnan(seg)]
        if seg.size:
            out[i] = seg.mean()
    return out


def render(learn_runs, ctrl, path, emerged):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(18, 5))
    verdict = "FUNCTIONAL" if emerged else "did NOT hold"
    fig.suptitle(
        "R180 GENESIS — FUNCTIONAL signalling = division of cognitive labour over a NON-STATIONARY world: "
        "BLIND foragers track a FLIPPING good-type ONLY by\ndecoding SCOUTS' learned signal (blue, 3 seeds); "
        "the one-knob no-learning control (orange, signal_lr=0) cannot track the flips -> chance. "
        f"[{verdict}]", fontsize=10)

    # Panel A: task_success curves, 3 learn seeds + control
    a = ax[0]
    a.axhline(0.5, color="k", ls=":", lw=1, label="chance (0.5)")
    blues = ["#1f77b4", "#3a8fd0", "#5fb0e8"]
    for r, c in zip(learn_runs, blues):
        a.plot(r["x"], smooth(r["succ"], 6), color=c, lw=2.0, label=f"LEARN seed{r['seed']} (lr=1.5)")
    a.plot(ctrl["x"], smooth(ctrl["succ"], 6), color="#ff7f0e", lw=2.4, ls="--",
           label="control (signal_lr=0)")
    a.set_ylim(0.30, 1.02)
    a.set_title("forager task_success — a functional convention forms with learning", fontsize=9)
    a.set_ylabel("fraction of blind foragers decoding the good-type")
    a.set_xlabel("step"); a.grid(alpha=0.25); a.legend(fontsize=8, loc="lower right")

    # Panel B: the tracking overlay (functional money shot) on the tracked learn seed
    a = ax[1]
    tr = learn_runs[0]
    win = slice(max(0, len(tr["g"]) - 500), None)
    xs = np.arange(len(tr["g"]))[win]
    a.step(xs, tr["g"][win], color="k", lw=1.6, where="post", label="true good-type g_t (flips)")
    a.plot(xs, smooth(tr["dec"][win], 12), color="#1f77b4", lw=2.2,
           label="foragers' aggregate decoded good-type")
    a.axhline(0.5, color="gray", ls=":", lw=1)
    a.set_ylim(-0.08, 1.08)
    a.set_title(f"foragers TRACK the flipping world (seed{tr['seed']}, last 500 steps)", fontsize=9)
    a.set_ylabel("good-type / decoded fraction"); a.set_xlabel("step")
    a.grid(alpha=0.25); a.legend(fontsize=8, loc="center right")

    # Panel C: tail task_success bar summary
    a = ax[2]
    labels = [f"learn s{r['seed']}" for r in learn_runs] + ["control"]
    vals = [r["tail"] for r in learn_runs] + [ctrl["tail"]]
    cols = blues[:len(learn_runs)] + ["#ff7f0e"]
    a.bar(labels, vals, color=cols)
    a.axhline(0.5, color="k", ls=":", lw=1, label="chance (0.5)")
    a.axhline(0.7, color="#2ca02c", ls="--", lw=1, label="functional threshold (0.7)")
    a.set_ylim(0, 1.0)
    a.set_title("tail task_success — learn >> control across seeds", fontsize=9)
    a.set_ylabel("tail forager task_success"); a.grid(alpha=0.25, axis="y"); a.legend(fontsize=8)

    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    steps = 1600
    print(f"--- R180 verify: LEARN (lr=1.5) x3 seeds vs no-learn control (lr=0), {steps} steps each ---",
          flush=True)
    learn_runs = []
    for s in range(3):
        r = run_arm("LEARN", 1.5, steps, seed=s, track=(s == 0))
        r["seed"] = s
        learn_runs.append(r)
    ctrl = run_arm("CONTROL", 0.0, steps, seed=0)
    ctrl["seed"] = 0

    learn_tails = [r["tail"] for r in learn_runs]
    ctrl_tail = ctrl["tail"]
    emerged = bool(min(learn_tails) > 0.6 and np.mean(learn_tails) > 0.7
                   and np.mean(learn_tails) > ctrl_tail + 0.15 and ctrl_tail < 0.6)
    print(f"\n  VERDICT functional={emerged} (expected True)", flush=True)
    print(f"  LEARN tails {[f'{x:.3f}' for x in learn_tails]} mean {np.mean(learn_tails):.3f} | "
          f"CONTROL tail {ctrl_tail:.3f} | asymmetry {np.mean(learn_tails) - ctrl_tail:+.3f}", flush=True)
    render(learn_runs, ctrl, os.path.join(OUT, "signal_task.png"), emerged)
    print(f"\nwrote {OUT}/signal_task.png in {time.time()-t0:.1f}s | FUNCTIONAL={emerged}", flush=True)


if __name__ == "__main__":
    main()
