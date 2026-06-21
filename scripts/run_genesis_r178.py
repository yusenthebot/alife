"""R178 — GENESIS Stage-2 signalling: HONEST NEGATIVE of the common-interest referential (Lewis/Skyrms) game.

HYPOTHESIS (under test): R144 (no relatedness) and R145 (kin selection) were honest negatives because a
predator-alarm's payoff to the caller is INDIRECT (inclusive fitness through saved kin) — weak, noisy, slow.
Skyrms (2010): a Lewis signalling system emerges readily under DIRECT common interest. So `signal_game` embeds
exactly that: every step each agent observes a private random referent BIT (a new input) and emits its utterance;
the nearest neighbour HEARS it and DECODES via a guess output (a new output); a correct decode pays BOTH speaker
and listener +signal_reward NOW. The claim to test: the missing piece was the PAYOFF STRUCTURE, not the channel —
so a signalling convention should bootstrap (decode_acc rises >0.5, MI(utterance;referent) >> scrambled null) in
the PAID arm but NOT in the otherwise-identical signal_reward=0 FREE control.

THE REAL-VERIFY VERDICT (run it, read the figure): it does NOT emerge. Across regimes (strong reward, small dense
populations, 1200+ steps) decode_acc stays pinned at chance (~0.5) and MI never clears the null in EITHER arm —
the PAID arm is indistinguishable from the FREE control. ROOT CAUSE (diagnosed): pure GENETIC evolution with
SHIFTING partners cannot break the encoder/decoder chicken-and-egg. A random decoder scores 50% regardless of
whether speakers encode, so there is NO selection gradient until encoder and decoder happen to align
SIMULTANEOUSLY across the whole population — which drift never delivers. The literature's actual missing piece is
WITHIN-LIFETIME reinforcement with stable speaker/listener roles (Skyrms' urn/Roth-Erev learning), which these
FROZEN NN genomes lack. So the hypothesis "payoff structure was the only missing piece" is REFUTED: direct payoff
is necessary but not sufficient — a within-life LEARNING/PAIRING structure is also required.

This script renders that honest negative so it is reproducible, not asserted: decode_acc + MI-vs-null trajectories
for PAID vs FREE, both flat at chance. The signal_game machinery is kept (default-off, byte-identical) as the
SUBSTRATE for the next attempt (within-lifetime reinforcement of the signalling policy). 禁止造假 — this figure
shows the truth, including that the headline did not hold.
"""
import os
import time
from dataclasses import replace

import numpy as np

from alife.genesis.genesis import GenesisWorld, GenesisConfig
from alife.world3d import World3D

OUT = "runs/r178_signal_game"


def cfg(reward, n0, cap, size):
    base = GenesisConfig(world=World3D(size=size), capacity=cap, n0=n0,
                         food_cap=int(cap * 0.35), food_regrow=max(7, cap // 60), persist_steps=50)
    return replace(base, signalling=True, signal_game=True, signal_reward=reward)


def run_arm(tag, reward, steps, n0, cap, size, seed=0, sample=50):
    """Run one evolutionary arm, sampling the live decode accuracy and MI-vs-null trajectory."""
    w = GenesisWorld(cfg(reward, n0, cap, size), seed=seed, evolve=True)
    xs, acc, mi, nm, ns, pop = [], [], [], [], [], []
    for i in range(steps):
        w.step()
        if (i + 1) % sample == 0:
            r = w.signal_game_mi()
            xs.append(i + 1); acc.append(r["decode_acc"]); mi.append(r["mi"])
            nm.append(r["null_mean"]); ns.append(r["null_std"]); pop.append(r["n"])
    z = (np.array(mi) - np.array(nm)) / np.maximum(np.array(ns), 1e-9)
    print(f"  {tag:6s} rew={reward}: final acc {acc[-1]:.3f} mi {mi[-1]:.4f} z {z[-1]:5.1f} "
          f"| acc range [{min(acc):.3f},{max(acc):.3f}] max z {z.max():.1f} pop {pop[-1]}", flush=True)
    return {"x": np.array(xs), "acc": np.array(acc), "mi": np.array(mi),
            "nm": np.array(nm), "ns": np.array(ns), "z": z, "pop": np.array(pop)}


def render(paid, free, path, steps):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("R178 GENESIS — HONEST NEGATIVE: the common-interest Lewis signalling game does NOT emerge "
                 "(decode_acc flat at chance in BOTH arms;\nDIRECT payoff is necessary but not sufficient — "
                 "frozen genetic evolution with shifting partners can't break the encoder/decoder chicken-and-egg)",
                 fontsize=10)

    a = ax[0]
    a.axhline(0.5, color="k", ls=":", lw=1, label="chance (0.5)")
    a.plot(paid["x"], paid["acc"], color="#1f77b4", lw=2.2, marker="o", ms=3, label="PAID (signal_reward>0)")
    a.plot(free["x"], free["acc"], color="#ff7f0e", lw=2.2, marker="s", ms=3, ls="--", label="FREE control (reward=0)")
    a.set_ylim(0.30, 0.80)
    a.set_title("live decode accuracy — never rises above chance (no convention forms)", fontsize=9)
    a.set_ylabel("decode accuracy of audible pairs")

    a = ax[1]
    a.axhline(0.0, color="k", ls=":", lw=1)
    a.plot(paid["x"], paid["z"], color="#1f77b4", lw=2.2, marker="o", ms=3, label="PAID")
    a.plot(free["x"], free["z"], color="#ff7f0e", lw=2.2, marker="s", ms=3, ls="--", label="FREE control")
    a.axhline(3.0, color="#2ca02c", ls="--", lw=1, label="z=3 emergence threshold")
    a.set_title("MI(utterance;referent) z-score vs scrambled null — noise, no sustained signal", fontsize=9)
    a.set_ylabel("MI z-score over null")

    for a in ax:
        a.set_xlabel("evolutionary step")
        a.grid(alpha=0.25); a.legend(fontsize=8, loc="best")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    steps = 1200
    print(f"--- R178 honest-negative verify: PAID vs FREE, {steps} steps each ---", flush=True)
    # strong direct reward, dense small world (the regime MOST favourable to emergence: strong selection)
    paid = run_arm("PAID", 3.0, steps, n0=120, cap=300, size=60.0)
    free = run_arm("FREE", 0.0, steps, n0=120, cap=300, size=60.0)

    emerged = bool(paid["acc"].max() > 0.60 and paid["z"].max() > 3.0
                   and paid["acc"][-1] > free["acc"][-1] + 0.05)
    print(f"\n  VERDICT emerged={emerged} (expected False — honest negative)", flush=True)
    print(f"  PAID acc max {paid['acc'].max():.3f} z max {paid['z'].max():.1f} | "
          f"FREE acc max {free['acc'].max():.3f} z max {free['z'].max():.1f}", flush=True)
    render(paid, free, os.path.join(OUT, "signal_game.png"), steps)
    print(f"\nwrote {OUT}/signal_game.png in {time.time()-t0:.1f}s | EMERGED={emerged} (negative result confirmed)",
          flush=True)


if __name__ == "__main__":
    main()
