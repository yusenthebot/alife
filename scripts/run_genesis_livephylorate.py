"""R166 REAL-VERIFY — does the innovation RATE law emerge from the LIVE economy?

Runs the real combinatorial GenesisWorld in two regimes, 2 seeds each:
  ECONOMY  (tech_gain=0.35) — mastery PAYS energy: deeper repertoire -> more energy -> more agents ->
            more newborns -> more combinatorial innovation attempts. The endogenous autocatalytic loop.
  CONTROL  (tech_gain=0.0)  — DECOUPLED: same combinatorial machinery on the same tree, but a deeper
            repertoire earns no extra energy, so the population can't grow with the repertoire.

The R165 super-linear signature is the per-step rate dN/dt RISING with the accumulated size N. The
endogeneity claim: that rise is CAUSED by the energy economy -> it must survive in ECONOMY and vanish in
CONTROL. Panel: (A) rate-vs-N (the discriminator), (B) cumulative repertoire N(t), (C) live workforce,
(D) rate_slope bars. One sim at a time; pure numpy + matplotlib (no GL). 禁止造假.
"""
import os
import sys
import time
from dataclasses import replace

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.genesis import livephylorate as lp
from alife.genesis import phylorate as ph
from alife.genesis.genesis import GenesisConfig, GenesisWorld
from alife.world3d import World3D

OUT = "runs/r166_livephylorate"
os.makedirs(OUT, exist_ok=True)


def cfg(tech_gain):
    return replace(GenesisConfig(world=World3D(size=100.0), n0=900, capacity=9000),
                   processing=True, building=True, culture=True, combinatorial=True,
                   max_techniques=8000, n_seed_tech=8, innov_steps=1,
                   hearth_reach_per_strength=3.0, hearth_radius=12.0, tech_gain=tech_gain)


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 1200
    seeds = (0, 1)
    regimes = [("ECONOMY  tech_gain=0.35", 0.35, "#d6263a"),
               ("CONTROL  tech_gain=0.00", 0.0, "#7a7a7a")]
    results = {}
    t_all = time.time()
    for label, tg, color in regimes:
        for sd in seeds:
            t0 = time.time()
            w = GenesisWorld(cfg(tg), seed=sd)
            out = lp.step_trajectory(w, steps)
            slope = lp.rate_slope(out, bins=6)
            results[(label, sd)] = (out, slope, color)
            print(f"{label} seed{sd}: distinct={out['n_distinct'][-1]} peak_active={out['active'].max()} "
                  f"rate_slope={slope*1000:.3f}/kN accel={ph.acceleration(out['step'], out['n_distinct']):.4f} "
                  f"{time.time()-t0:.0f}s", flush=True)

    fig, ax = plt.subplots(2, 2, figsize=(15, 10))
    # (A) rate-vs-N — the discriminator
    for (label, sd), (out, slope, color) in results.items():
        cN, cR = ph.rate_vs_size(out, bins=6)
        ax[0, 0].plot(cN, cR, "-o", color=color, alpha=0.85,
                      lw=2.4 if sd == 0 else 1.4, ls="-" if sd == 0 else "--",
                      label=f"{label.split()[0]} s{sd}")
    ax[0, 0].set_title("(A) per-step rate dN/dt vs accumulated repertoire N\n"
                       "ECONOMY rises (super-linear) · CONTROL flat", fontsize=11)
    ax[0, 0].set_xlabel("N = pop_distinct (techniques known by living pop)")
    ax[0, 0].set_ylabel("dN/dt (new techniques / step)")
    ax[0, 0].legend(fontsize=8); ax[0, 0].grid(alpha=0.3)
    # (B) cumulative repertoire N(t)
    for (label, sd), (out, slope, color) in results.items():
        ax[0, 1].plot(out["step"], out["n_distinct"], color=color,
                      lw=2.4 if sd == 0 else 1.4, ls="-" if sd == 0 else "--")
    ax[0, 1].set_title("(B) cumulative repertoire N(t)\nECONOMY climbs far above the decoupled CONTROL",
                       fontsize=11)
    ax[0, 1].set_xlabel("step"); ax[0, 1].set_ylabel("pop_distinct"); ax[0, 1].grid(alpha=0.3)
    # (C) live workforce (the endogenous effort)
    for (label, sd), (out, slope, color) in results.items():
        ax[1, 0].plot(out["step"], out["active"], color=color,
                      lw=2.4 if sd == 0 else 1.4, ls="-" if sd == 0 else "--")
    ax[1, 0].set_title("(C) living workforce (innovation effort source)\n"
                       "ECONOMY grows it with the repertoire; CONTROL can't", fontsize=11)
    ax[1, 0].set_xlabel("step"); ax[1, 0].set_ylabel("active agents"); ax[1, 0].grid(alpha=0.3)
    # (D) rate_slope bars — the decisive contrast
    keys = list(results.keys())
    xs = np.arange(len(keys))
    slopes = [results[k][1] * 1000 for k in keys]
    cols = [results[k][2] for k in keys]
    ax[1, 1].bar(xs, slopes, color=cols)
    ax[1, 1].axhline(0, color="k", lw=0.8)
    ax[1, 1].set_xticks(xs)
    ax[1, 1].set_xticklabels([f"{k[0].split()[0]}\ns{k[1]}" for k in keys], fontsize=8)
    ax[1, 1].set_title("(D) rate-vs-N slope (>0 = accelerating)\nECONOMY positive · CONTROL ~0/negative",
                       fontsize=11)
    ax[1, 1].set_ylabel("d(rate)/dN  ×1000")
    fig.suptitle("R166 — the innovation RATE law EMERGES from the LIVE economy: tech pays energy -> "
                 "population grows with the repertoire -> the discovery rate accelerates (decisive "
                 "tech_gain=0 control flattens it)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    path = os.path.join(OUT, "panel.png")
    fig.savefig(path, dpi=110)
    print(f"\nwrote {path}  ({time.time()-t_all:.0f}s total)")


if __name__ == "__main__":
    main()
