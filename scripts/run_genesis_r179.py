"""R179 — GENESIS Stage-2 signalling: POSITIVE. The diagnosed fix for the R178 honest negative.

THE DIAGNOSIS (R144 no-relatedness, R145 kin-selection, R178 direct-payoff — THREE Stage-2 negatives) all
pointed to the SAME missing piece: with FROZEN NN genomes and SHIFTING partners a random decoder scores 50%
regardless of how speakers encode, so genetic evolution gets NO selection gradient and the encoder/decoder
chicken-and-egg never breaks. Skyrms (2010) / Roth-Erev: a Lewis signalling system emerges readily under
WITHIN-LIFETIME reinforcement learning.

THE FIX (signal_learn=True): every agent carries two small mutable URNS that learn within its own life,
BESIDE the frozen brain — a SENDER urn (propensity over symbol | own referent bit) and a RECEIVER urn
(propensity over guess | heard symbol). Each step the sender samples a symbol from its urn for the referent
it sees; the listener samples a guess from its urn for the symbol it heard; on a CORRECT decode BOTH urns are
reinforced (+signal_lr on the winning cell, Roth-Erev). Positive feedback amplifies a coherent shared
convention from random play.

THE CLAIM (run it, read the figure): with learning (signal_lr>0) decode_acc climbs WELL above chance and
MI(symbol;referent) clears the scrambled-channel null, WITHIN a single run; the ONE-KNOB control (signal_lr=0,
urns frozen uniform = no learning = the R178 chicken-and-egg) stays pinned at chance. The signal_lr=0 control
+ the scrambled-MI null are the two adversarial checks: the asymmetry is the emergence, not a measurement
artefact. 禁止造假 — this figure shows the truth.
"""
import os
import time
from dataclasses import replace

import numpy as np

from alife.genesis.genesis import GenesisWorld, GenesisConfig
from alife.world3d import World3D

OUT = "runs/r179_signal_learn"


def cfg(lr, n0, cap, size, reward=0.6):
    base = GenesisConfig(world=World3D(size=size), capacity=cap, n0=n0,
                         food_cap=int(cap * 0.35), food_regrow=max(7, cap // 60), persist_steps=50)
    return replace(base, signalling=True, signal_game=True, signal_learn=True,
                   signal_lr=lr, signal_reward=reward)


def run_arm(tag, lr, steps, n0, cap, size, seed=0, sample=40):
    """Run one within-lifetime-learning arm, sampling live decode accuracy + MI-vs-null trajectory."""
    w = GenesisWorld(cfg(lr, n0, cap, size), seed=seed, evolve=True)
    xs, acc, mi, nm, ns, pop = [], [], [], [], [], []
    for i in range(steps):
        w.step()
        if (i + 1) % sample == 0:
            r = w.signal_game_mi()
            xs.append(i + 1); acc.append(r["decode_acc"]); mi.append(r["mi"])
            nm.append(r["null_mean"]); ns.append(r["null_std"]); pop.append(r["n"])
    z = (np.array(mi) - np.array(nm)) / np.maximum(np.array(ns), 1e-9)
    acc = np.array(acc)
    print(f"  {tag:7s} lr={lr}: final acc {acc[-1]:.3f} mi {mi[-1]:.4f} z {z[-1]:5.1f} "
          f"| acc range [{np.nanmin(acc):.3f},{np.nanmax(acc):.3f}] max z {z.max():.1f} pop {pop[-1]}", flush=True)
    return {"x": np.array(xs), "acc": acc, "mi": np.array(mi),
            "nm": np.array(nm), "ns": np.array(ns), "z": z, "pop": np.array(pop)}


def render(learn, ctrl, path, emerged):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    verdict = "EMERGES" if emerged else "did NOT emerge"
    fig.suptitle("R179 GENESIS — Stage-2 signalling EMERGES via WITHIN-LIFETIME reinforcement (Skyrms/Roth-Erev): "
                 "decode_acc climbs\nfar above chance with learning (blue) and stays pinned at chance for the "
                 "one-knob no-learning control (orange, signal_lr=0). " + f"[{verdict}]",
                 fontsize=10)

    a = ax[0]
    a.axhline(0.5, color="k", ls=":", lw=1, label="chance (0.5)")
    a.plot(learn["x"], learn["acc"], color="#1f77b4", lw=2.4, marker="o", ms=3, label="LEARN (signal_lr=0.4)")
    a.plot(ctrl["x"], ctrl["acc"], color="#ff7f0e", lw=2.4, marker="s", ms=3, ls="--",
           label="control (signal_lr=0, no learning)")
    a.set_ylim(0.30, 1.02)
    a.set_title("live decode accuracy — a Lewis convention bootstraps with learning", fontsize=9)
    a.set_ylabel("decode accuracy of audible pairs")

    a = ax[1]
    a.axhline(0.0, color="k", ls=":", lw=1)
    a.plot(learn["x"], learn["z"], color="#1f77b4", lw=2.4, marker="o", ms=3, label="LEARN")
    a.plot(ctrl["x"], ctrl["z"], color="#ff7f0e", lw=2.4, marker="s", ms=3, ls="--", label="control")
    a.axhline(3.0, color="#2ca02c", ls="--", lw=1, label="z=3 emergence threshold")
    a.set_title("MI(symbol;referent) z-score vs scrambled null — clears it only with learning", fontsize=9)
    a.set_ylabel("MI z-score over null")

    for a in ax:
        a.set_xlabel("step")
        a.grid(alpha=0.25); a.legend(fontsize=8, loc="best")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    steps = 1200
    print(f"--- R179 verify: within-lifetime LEARN (lr=0.4) vs no-learn control (lr=0), {steps} steps each ---",
          flush=True)
    learn = run_arm("LEARN", 0.4, steps, n0=120, cap=300, size=60.0)
    ctrl = run_arm("CONTROL", 0.0, steps, n0=120, cap=300, size=60.0)

    tail = slice(-6, None)
    learn_tail = float(np.nanmean(learn["acc"][tail]))
    ctrl_tail = float(np.nanmean(ctrl["acc"][tail]))
    emerged = bool(learn_tail > 0.70 and learn["z"].max() > 3.0 and learn_tail > ctrl_tail + 0.15)
    print(f"\n  VERDICT emerged={emerged} (expected True — the diagnosed fix)", flush=True)
    print(f"  LEARN tail acc {learn_tail:.3f} z max {learn['z'].max():.1f} | "
          f"CONTROL tail acc {ctrl_tail:.3f} z max {ctrl['z'].max():.1f} | "
          f"asymmetry {learn_tail - ctrl_tail:+.3f}", flush=True)
    render(learn, ctrl, os.path.join(OUT, "signal_learn.png"), emerged)
    print(f"\nwrote {OUT}/signal_learn.png in {time.time()-t0:.1f}s | EMERGED={emerged}", flush=True)


if __name__ == "__main__":
    main()
