"""R115 figure — chimera states: coherence and incoherence coexisting in one symmetric oscillator ring."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dataclasses import replace

from alife.chimera import (
    ChimeraConfig, run, local_order, global_order, coherent_fraction,
)

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r115_chimera")
os.makedirs(OUT, exist_ok=True)

cfg = ChimeraConfig(N=256, kappa=4.0, alpha=1.46, steps=4000, seed=1)
r = run(cfg, record_every=20)
theta, snaps = r["theta"], r["snaps"]
R = local_order(theta)
ctrl = run(replace(cfg, global_coupling=True))            # all-to-all control -> full sync
Rctrl = local_order(ctrl["theta"])
Rspace = np.array([local_order(s) for s in snaps])        # local order over space & time
x = np.arange(cfg.N)
print(f"chimera: global R={global_order(theta):.2f}  R range [{R.min():.2f},{R.max():.2f}]  "
      f"coherent fraction={coherent_fraction(theta):.2f}  | control global R={global_order(ctrl['theta']):.2f}")

fig = plt.figure(figsize=(14.5, 8.4), facecolor="white")

axA = fig.add_subplot(2, 2, 1)
axA.scatter(x, theta, s=7, c=R, cmap="viridis", vmin=0, vmax=1)
axA.set_xlabel("oscillator index (ring position)"); axA.set_ylabel("phase  theta")
axA.set_title("Snapshot: a smooth COHERENT arc beside a\nscattered INCOHERENT arc — one ring, both at once",
              fontsize=10.5)
axA.set_ylim(0, 2 * np.pi)

axB = fig.add_subplot(2, 2, 2)
axB.plot(x, R, color="#3a0ca3", lw=1.8, label="chimera (nonlocal coupling)")
axB.plot(x, Rctrl, color="#999", lw=1.4, ls="--", label="control: all-to-all -> full sync")
axB.axhline(1.0, color="#ccc", lw=0.8)
axB.set_xlabel("ring position"); axB.set_ylabel("local order parameter  R")
axB.set_title("Local coherence: plateau (R~1, locked) +\ndip (R<1, drifting) — the chimera signature",
              fontsize=10.5)
axB.set_ylim(0, 1.05); axB.legend(fontsize=8.5, loc="lower center"); axB.grid(alpha=0.3)

axC = fig.add_subplot(2, 2, 3)
T = snaps.shape[0] * 20 * cfg.dt
im = axC.imshow(Rspace, aspect="auto", cmap="magma", vmin=0, vmax=1,
                origin="lower", extent=[0, cfg.N, 0, T])
axC.set_xlabel("ring position"); axC.set_ylabel("time")
axC.set_title("Space-time of local order: the incoherent\nband (dark) stays put — the split persists", fontsize=10.5)
fig.colorbar(im, ax=axC, fraction=0.046, pad=0.04).set_label("R", fontsize=9)

axD = fig.add_subplot(2, 2, 4)
im2 = axD.imshow(np.sin(snaps), aspect="auto", cmap="twilight",
                 origin="lower", extent=[0, cfg.N, 0, T])
axD.set_xlabel("ring position"); axD.set_ylabel("time")
axD.set_title("Space-time of sin(phase): smooth waves in the\ncoherent region, scramble in the incoherent one",
              fontsize=10.5)
fig.colorbar(im2, ax=axD, fraction=0.046, pad=0.04).set_label("sin(theta)", fontsize=9)

fig.suptitle("R115 · Chimera states — identical, symmetrically nonlocally-coupled oscillators "
             "spontaneously split into coexisting coherent + incoherent domains (Kuramoto-Battogtokh 2002)",
             fontsize=11.5, y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "chimera.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
