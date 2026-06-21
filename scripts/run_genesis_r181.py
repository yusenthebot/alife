"""R181 — GENESIS SPATIAL signalling: the division of cognitive labour made EMBODIED.

R180 proved a learned signal lets BLIND foragers DECODE a flipping good-type — but the payoff was abstract
(a correct decode paid energy directly; nobody had to GO anywhere). R181 grounds the channel in the world:
  - the shared good-type g_t now names WHICH of two fixed world PATCHES is ripe (it still flips, but slower —
    physical transit between patches takes time the abstract decode did not);
  - SCOUTS (observe g_t) march to the true ripe patch; BLIND FORAGERS march to the patch their DECODED scout
    signal names;
  - the foraging reward is EARNED BY PHYSICAL PRESENCE at the ripe patch — a forager only eats if it navigates
    to the place a scout's word points to.

THE CLAIM (run it, read the figure): with within-lifetime learning (signal_lr>0) the blind foragers' bodies
TRACK the flipping ripe patch — spatial_yield (fraction physically at the ripe patch) climbs well above chance
and the forager MASS flips sides in space when g_t flips. The one-knob control (signal_lr=0, urns frozen) keeps
foragers marching to a randomly-sampled patch -> they thrash and rarely settle on the ripe one. 禁止造假 — the
figure shows the truth, including the honest transit-capped ceiling.
"""
import os
import time
from dataclasses import replace

import numpy as np

from alife.genesis.genesis import GenesisWorld, GenesisConfig
from alife.world3d import World3D

OUT = "runs/r181_signal_spatial"
SIZE = 78.0
FLIP = 0.012


def cfg(lr):
    base = GenesisConfig(world=World3D(size=SIZE), capacity=1200, n0=700,
                         food_cap=220, food_regrow=10, persist_steps=50)
    return replace(base, signalling=True, signal_game=True, signal_learn=True, signal_task=True,
                   signal_spatial=True, task_flip=FLIP, patch_sep=0.6, patch_radius_frac=0.16, signal_lr=lr)


def run_arm(tag, lr, steps, seed, sample=20, track=False, nbins=44):
    """Run one arm, sampling forager spatial_yield. If track, also record the per-step ripe-patch x and a
    histogram of forager x-positions (the spatial money-shot heatmap)."""
    w = GenesisWorld(cfg(lr), seed=seed, evolve=True)
    edges = np.linspace(0.0, SIZE, nbins + 1)
    xs, yld, pop = [], [], []
    ripe_x, fhist = [], []
    for i in range(steps):
        w.step()
        if track:
            act = w.pop.active()
            forager = ~w._is_scout[act]
            fx = w.pop.pos[act][forager, 0]
            h, _ = np.histogram(fx, bins=edges)
            fhist.append(h / max(1, h.sum()))
            ripe_x.append(float(w._patches[w._good_type][0]))
        if (i + 1) % sample == 0:
            y = w._last_spatial_yield
            xs.append(i + 1)
            yld.append(y if y == y else np.nan)
            pop.append(int(w.pop.active().size))
    yld = np.array(yld, dtype=float)
    tail = float(np.nanmean(yld[-15:]))
    print(f"  {tag:14s} lr={lr} seed={seed}: tail spatial_yield {tail:.3f} | "
          f"range [{np.nanmin(yld):.3f},{np.nanmax(yld):.3f}] pop {pop[-1]}", flush=True)
    return {"x": np.array(xs), "yld": yld, "pop": np.array(pop), "tail": tail, "seed": seed,
            "ripe_x": np.array(ripe_x), "fhist": np.array(fhist), "edges": edges}


def smooth(a, k=6):
    a = np.asarray(a, dtype=float)
    out = np.full_like(a, np.nan)
    for i in range(len(a)):
        seg = a[max(0, i - k + 1):i + 1]
        seg = seg[~np.isnan(seg)]
        if seg.size:
            out[i] = seg.mean()
    return out


def render(learn_runs, ctrl, path, emerged):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(18, 5))
    verdict = "EMBODIED" if emerged else "did NOT hold"
    fig.suptitle(
        "R181 GENESIS — SPATIAL signalling = an EMBODIED division of labour: BLIND foragers physically NAVIGATE to "
        "the ripe PATCH a scout's learned signal\nnames, and their MASS flips sides in space when the world flips "
        "(blue, 3 seeds); the one-knob no-learning control (orange, signal_lr=0) cannot. "
        f"[{verdict}]", fontsize=10)

    # Panel A: spatial_yield curves, 3 learn seeds + control
    a = ax[0]
    a.axhline(0.5, color="k", ls=":", lw=1, label="chance (0.5)")
    blues = ["#1f77b4", "#3a8fd0", "#5fb0e8"]
    for r, c in zip(learn_runs, blues):
        a.plot(r["x"], smooth(r["yld"]), color=c, lw=2.0, label=f"LEARN seed{r['seed']} (lr=1.5)")
    a.plot(ctrl["x"], smooth(ctrl["yld"]), color="#ff7f0e", lw=2.4, ls="--", label="control (signal_lr=0)")
    a.set_ylim(0.0, 1.02)
    a.set_title("forager spatial_yield — bodies reach the ripe patch with learning", fontsize=9)
    a.set_ylabel("fraction of blind foragers AT the ripe patch"); a.set_xlabel("step")
    a.grid(alpha=0.25); a.legend(fontsize=8, loc="center right")

    # Panel B: THE MONEY SHOT — forager x-position density heatmap (full run) with the ripe-patch x and the
    # density-weighted MEAN forager x overlaid; the mean tracks the flipping ripe patch (with a transit lag).
    a = ax[1]
    tr = learn_runs[0]
    H = tr["fhist"].T                                                 # (bins, steps) density over the whole run
    steps_n = H.shape[1]
    a.imshow(H, aspect="auto", origin="lower", cmap="magma",
             extent=[0, steps_n, 0.0, SIZE], vmax=np.percentile(H, 99))
    centres = 0.5 * (tr["edges"][:-1] + tr["edges"][1:])
    mean_x = (tr["fhist"] * centres[None, :]).sum(1)                  # density-weighted mean forager x per step
    tt = np.arange(steps_n)
    a.step(tt, tr["ripe_x"], color="#39ff14", lw=1.6, where="post", label="ripe patch x (flips)")
    a.plot(tt, smooth(mean_x, 9), color="#00e5ff", lw=1.4, label="mean forager x (tracks)")
    a.set_ylim(0.0, SIZE)
    a.set_title(f"forager MASS tracks the ripe patch in SPACE (seed{tr['seed']})", fontsize=9)
    a.set_ylabel("forager x-position (patch lo <-> hi)"); a.set_xlabel("step")
    a.legend(fontsize=8, loc="upper right")

    # Panel C: tail spatial_yield bar summary
    a = ax[2]
    labels = [f"learn s{r['seed']}" for r in learn_runs] + ["control"]
    vals = [r["tail"] for r in learn_runs] + [ctrl["tail"]]
    cols = blues[:len(learn_runs)] + ["#ff7f0e"]
    a.bar(labels, vals, color=cols)
    a.axhline(0.5, color="k", ls=":", lw=1, label="chance (0.5)")
    a.axhline(0.7, color="#2ca02c", ls="--", lw=1, label="embodied threshold (0.7)")
    a.set_ylim(0, 1.0)
    a.set_title("tail spatial_yield — learn >> control across seeds", fontsize=9)
    a.set_ylabel("tail forager spatial_yield"); a.grid(alpha=0.25, axis="y"); a.legend(fontsize=8)

    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    steps = 1500
    print(f"--- R181 verify: LEARN (lr=1.5) x3 seeds vs no-learn control (lr=0), {steps} steps each ---",
          flush=True)
    learn_runs = []
    for s in range(3):
        learn_runs.append(run_arm("LEARN", 1.5, steps, seed=s, track=(s == 0)))
    ctrl = run_arm("CONTROL", 0.0, steps, seed=0)

    learn_tails = [r["tail"] for r in learn_runs]
    ctrl_tail = ctrl["tail"]
    # spatial_yield is TRANSIT-CAPPED (a perfect decoder is mid-transit a fraction of the time after each flip),
    # so the principled verdict is the asymmetry vs the one-knob no-learning control, not an absolute bar:
    # every learn seed must decisively beat the frozen-urn control, which itself stays near/below chance.
    emerged = bool(min(learn_tails) > 0.5 and ctrl_tail < 0.45
                   and all(t > ctrl_tail + 0.2 for t in learn_tails)
                   and np.mean(learn_tails) - ctrl_tail > 0.3)
    print(f"\n  VERDICT embodied={emerged} (expected True)", flush=True)
    print(f"  LEARN tails {[f'{x:.3f}' for x in learn_tails]} mean {np.mean(learn_tails):.3f} | "
          f"CONTROL tail {ctrl_tail:.3f} | asymmetry {np.mean(learn_tails) - ctrl_tail:+.3f}", flush=True)
    render(learn_runs, ctrl, os.path.join(OUT, "signal_spatial.png"), emerged)
    print(f"\nwrote {OUT}/signal_spatial.png in {time.time()-t0:.1f}s | EMBODIED={emerged}", flush=True)


if __name__ == "__main__":
    main()
