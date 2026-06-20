"""R143 — GENESIS co-evolutionary arms race: 3D GIF + boom-bust panel + evasion red-team.

A second evolved-neural species (red predators) hunts the prey; prey gain a predator-sense channel and
evolve EVASION. Headline: a living predator-prey ecology (boom-bust cycles, no extinction) where prey
flee-directedness evolves above a frozen-genome control. One sim at a time; GL context released.
"""
import os
import sys
import time
from dataclasses import replace

import imageio.v2 as imageio
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.genesis.genesis import GenesisConfig, GenesisWorld

OUT = "runs/r143_predators"
os.makedirs(OUT, exist_ok=True)
N_PRED = 120


def flee_curve(steps, seed, evolve, every=250):
    w = GenesisWorld(replace(GenesisConfig(), n_predators0=N_PRED), seed=seed, evolve=evolve)
    xs, flee = [], []
    for s in range(steps):
        w.step()
        if s % every == 0:
            xs.append(s); flee.append(w.snapshot()["flee"])
    snp = w.snapshot()
    return np.array(xs), np.array(flee), snp["population"], snp["predators"]


def headline(steps, seed=0, render_every=200):
    from alife.render3d import Renderer3D
    cfg = replace(GenesisConfig(), n_predators0=N_PRED)
    w = GenesisWorld(cfg, seed=seed, evolve=True)
    hist = {x: [] for x in ("step", "population", "predators", "flee", "directedness")}
    frames = []
    r = Renderer3D(cfg.world, width=720, height=540)
    t0 = time.time()
    for s in range(steps):
        w.step()
        if s % 50 == 0:
            snp = w.snapshot()
            for x in hist:
                hist[x].append(snp[x])
        if s % render_every == 0:
            pos, vel, col, food = w.render_arrays()        # prey (lineage colours) + predators (red)
            if pos.shape[0]:
                frames.append(r.render(pos, vel, col, cam_angle=s * 0.012, cam_elev=0.42, food=food))
    r.ctx.release()
    if frames:
        imageio.mimsave(os.path.join(OUT, "predators.gif"), frames, fps=12, loop=0)
    print(f"headline: {steps} steps {time.time()-t0:.1f}s -> prey {hist['population'][-1]:.0f} "
          f"pred {hist['predators'][-1]:.0f} flee {hist['flee'][-1]:+.3f}", flush=True)
    return hist


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 16000
    rt = int(sys.argv[2]) if len(sys.argv) > 2 else 9000
    print(f"=== headline arms-race run ({steps} steps, 3D) ===", flush=True)
    h = headline(steps)

    print(f"=== red-team: prey evasion evolve vs frozen, 3 seeds, {rt} steps ===", flush=True)
    evo_w, frz_w = [], []          # windowed (2nd-half mean) flee — denoises the boom-bust swings
    coexist = []
    ex_evo = ex_frz = None
    for seed in (0, 1, 2):
        xe, fe, pe, qe = flee_curve(rt, seed, True)
        xf, ff, pf, qf = flee_curve(rt, seed, False)
        ev, fr = fe[len(fe) // 2:].mean(), ff[len(ff) // 2:].mean()
        evo_w.append(ev); frz_w.append(fr)
        coexist.append(pe > 0 and qe > 0)
        if seed == 0:
            ex_evo, ex_frz = (xe, fe), (xf, ff)
        print(f"  seed {seed}: evolve flee {ev:+.3f}  frozen {fr:+.3f}  coexist={pe > 0 and qe > 0} "
              f"(prey {pe:.0f}/pred {qe:.0f})", flush=True)
    print(f"  MEAN evolve {np.mean(evo_w):+.3f} vs frozen {np.mean(frz_w):+.3f}; "
          f"coexisted {sum(coexist)}/3 seeds", flush=True)

    fig, ax = plt.subplots(2, 2, figsize=(15, 9))
    st = np.array(h["step"])
    ax[0, 0].plot(st, h["population"], color="#2ca02c", label="prey")
    ax[0, 0].plot(st, h["predators"], color="#d62728", label="predators")
    ax[0, 0].set_title("predator-prey populations (boom-bust coexistence)"); ax[0, 0].legend()
    ax[0, 1].plot(st, h["flee"], color="#1f77b4"); ax[0, 1].axhline(0, color="k", lw=0.5)
    ax[0, 1].set_title("prey flee-directedness evolving (in situ)")
    ax[1, 0].plot(st, h["directedness"], color="#9467bd"); ax[1, 0].axhline(0, color="k", lw=0.5)
    ax[1, 0].set_title("prey foraging directedness (still evolves)")
    if ex_evo is not None:
        ax[1, 1].plot(ex_evo[0], ex_evo[1], color="#2ca02c", label="evolve")
        ax[1, 1].plot(ex_frz[0], ex_frz[1], color="#d62728", label="frozen (control)")
        ax[1, 1].axhline(0, color="k", lw=0.5)
        ax[1, 1].set_title(f"RED-TEAM evasion: evolve {np.mean(evo_w):+.2f} vs frozen {np.mean(frz_w):+.2f} "
                           f"({sum(coexist)}/3 coexist)")
        ax[1, 1].legend()
    fig.suptitle("GENESIS R143 — co-evolutionary arms race: predators hunt, prey evolve evasion",
                 fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=100)
    print(f"wrote {OUT}/predators.gif and {OUT}/panel.png", flush=True)


if __name__ == "__main__":
    main()
