"""R141 — run the GENESIS living world: 3D GIF + analysis panel + checkpoint + red-team.

One sim at a time (host-crash rule); the moderngl context is closed after rendering. Outputs to
runs/r141_genesis/ (gitignored):
  genesis.gif   — the 3D world over a long run (agents coloured by lineage, streaming through food)
  panel.png     — population, foraging-directedness (evolve vs frozen), diversity, generation depth
  checkpoint.npz— resume point (proves the world is persistable for cloud / multi-day runs)

The headline claim — foraging behaviour genuinely EVOLVES — is red-teamed against a frozen-genome
control across multiple seeds (directedness must rise under evolution and stay near baseline frozen).
"""
import os
import sys
import time

import imageio.v2 as imageio
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.genesis.genesis import GenesisConfig, GenesisWorld

OUT = "runs/r141_genesis"
os.makedirs(OUT, exist_ok=True)


def evolve_curve(steps, seed, evolve, every=250):
    """Directedness over time for one world (no rendering) — the red-team measurement."""
    w = GenesisWorld(GenesisConfig(), seed=seed, evolve=evolve)
    xs, dirs = [], []
    for s in range(steps):
        w.step()
        if s % every == 0:
            xs.append(s)
            dirs.append(w.snapshot()["directedness"])
    return np.array(xs), np.array(dirs)


def headline_run(steps, seed=0, render_every=200):
    """The evolving world with 3D rendering + full metric history + checkpoint."""
    from alife.render3d import Renderer3D
    cfg = GenesisConfig()
    w = GenesisWorld(cfg, seed=seed, evolve=True)
    hist = {k: [] for k in ("step", "population", "food", "directedness", "diversity", "max_gen")}
    frames = []
    renderer = Renderer3D(cfg.world, width=720, height=540)
    t0 = time.time()
    for s in range(steps):
        w.step()
        if s % 50 == 0:
            snp = w.snapshot()
            for k in hist:
                hist[k].append(snp[k])
        if s % render_every == 0:
            pos, vel, color, food = w.render_arrays()
            if pos.shape[0]:
                frame = renderer.render(pos, vel, color, cam_angle=s * 0.012,
                                        cam_elev=0.42, food=food)
                frames.append(frame)
    renderer.ctx.release()                                  # close GL context (memory)
    w.save_checkpoint(os.path.join(OUT, "checkpoint.npz"))
    if frames:
        imageio.mimsave(os.path.join(OUT, "genesis.gif"), frames, fps=12, loop=0)
    print(f"headline: {steps} steps in {time.time()-t0:.1f}s, {len(frames)} frames, "
          f"final dir {hist['directedness'][-1]:+.3f} pop {hist['population'][-1]:.0f} "
          f"gen {hist['max_gen'][-1]:.0f}", flush=True)
    return hist


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 16000
    rt_steps = int(sys.argv[2]) if len(sys.argv) > 2 else 6000

    print(f"=== headline evolving run ({steps} steps, 3D render) ===", flush=True)
    hist = headline_run(steps, seed=0)

    print(f"=== red-team: evolve vs frozen, 3 seeds, {rt_steps} steps ===", flush=True)
    evo_finals, frz_finals = [], []
    evo_example = frz_example = None
    for seed in (0, 1, 2):
        xe, de = evolve_curve(rt_steps, seed, evolve=True)
        xf, df = evolve_curve(rt_steps, seed, evolve=False)
        evo_finals.append(de[-3:].mean())
        frz_finals.append(df[-3:].mean())
        if seed == 0:
            evo_example, frz_example = (xe, de), (xf, df)
        print(f"  seed {seed}: evolve {de[-3:].mean():+.3f}  frozen {df[-3:].mean():+.3f}  "
              f"delta {de[-3:].mean()-df[-3:].mean():+.3f}", flush=True)
    evo_finals, frz_finals = np.array(evo_finals), np.array(frz_finals)
    print(f"  MEAN evolve {evo_finals.mean():+.3f} vs frozen {frz_finals.mean():+.3f} "
          f"-> delta {evo_finals.mean()-frz_finals.mean():+.3f}", flush=True)

    # analysis panel
    fig, ax = plt.subplots(2, 3, figsize=(16, 9))
    st = np.array(hist["step"])
    ax[0, 0].plot(st, hist["population"], color="#1f77b4"); ax[0, 0].set_title("population (food-limited)")
    ax[0, 0].set_xlabel("step"); ax[0, 0].set_ylabel("agents")
    ax[0, 1].plot(st, hist["directedness"], color="#2ca02c")
    ax[0, 1].axhline(0, color="k", lw=0.5); ax[0, 1].set_title("foraging directedness evolving (in situ)")
    ax[0, 1].set_xlabel("step")
    ax[0, 2].plot(st, hist["max_gen"], color="#9467bd"); ax[0, 2].set_title("deepest generation (descent)")
    ax[0, 2].set_xlabel("step")
    ax[1, 0].plot(st, hist["food"], color="#8c564b"); ax[1, 0].set_title("food remaining (eaten down -> limiter)")
    ax[1, 0].set_xlabel("step")
    ax[1, 1].plot(st, hist["diversity"], color="#ff7f0e")
    ax[1, 1].set_title("persistent lineage diversity (eff. #)"); ax[1, 1].set_xlabel("step")
    if evo_example:
        ax[1, 2].plot(evo_example[0], evo_example[1], color="#2ca02c", label="evolve")
        ax[1, 2].plot(frz_example[0], frz_example[1], color="#d62728", label="frozen (control)")
        ax[1, 2].axhline(0, color="k", lw=0.5)
        ax[1, 2].set_title(f"RED-TEAM: evolve {evo_finals.mean():+.2f} vs frozen {frz_finals.mean():+.2f}")
        ax[1, 2].set_xlabel("step"); ax[1, 2].legend()
    fig.suptitle("GENESIS R141 — a persistent 3D world where foraging behaviour evolves "
                 "(no GA, no fitness function, in-situ selection)", fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=100)
    print(f"wrote {OUT}/panel.png and {OUT}/genesis.gif", flush=True)


if __name__ == "__main__":
    main()
