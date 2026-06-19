"""R104 figure — granular hopper: constant-rate discharge & Beverloo's law."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dataclasses import replace

from alife.granular import simulate, discharge_rate, HopperConfig

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r104_granular")
os.makedirs(OUT, exist_ok=True)
cfg = HopperConfig(steps=3500)
cache = os.path.join(OUT, "hopper.npz")

# snapshot early in the drain (fuller hopper, grains funnelling toward the orifice)
snap = simulate(replace(cfg, steps=550), seed=2)
spos = snap["pos"]; spos = spos[spos[:, 1] > -10]              # drop recycled-away grains

# cumulative curves for two orifices (constant rate = linear)
runs = {D: simulate(replace(cfg, orifice=D), seed=1) for D in (8, 14)}

# Beverloo + jamming (cap at D=15: a wider opening drains this hopper too fast to time a steady rate)
Ds = np.array([3, 5, 7, 9, 11, 13, 15])
rates = np.array([discharge_rate(simulate(replace(cfg, orifice=float(D)), seed=1)) for D in Ds])
np.savez(cache, Ds=Ds, rates=rates)

fig = plt.figure(figsize=(15, 4.8), facecolor="white")

axA = fig.add_subplot(1, 3, 1)
axA.scatter(spos[:, 0], spos[:, 1], s=6, c="#c08a30")
axA.axhline(0, color="k", lw=1)
axA.plot([cfg.width / 2 - cfg.orifice / 2, cfg.width / 2 + cfg.orifice / 2], [0, 0], color="w", lw=2)
axA.set_title("Hopper draining through an orifice", fontsize=10.5)
axA.set_aspect("equal"); axA.set_xlim(0, cfg.width); axA.set_ylim(-12, spos[:, 1].max() + 4); axA.set_xticks([]); axA.set_yticks([])

axB = fig.add_subplot(1, 3, 2)
for D, c in zip((8, 14), ("#1f77b4", "#e76f51")):
    cum = runs[D]["cum"]
    axB.plot(cum, color=c, label=f"orifice {D}")
axB.set_xlabel("time step"); axB.set_ylabel("grains discharged (cumulative)")
axB.set_title("Constant-rate flow (straight line)\n— unlike a liquid, which slows as it empties", fontsize=10)
axB.legend(fontsize=9); axB.grid(alpha=0.3)

axC = fig.add_subplot(1, 3, 3)
axC.plot(Ds, rates, "o-", color="#6a040f")
axC.axvspan(0, 4, color="#eee", alpha=0.8)
axC.text(1.3, rates.max() * 0.5, "jams", fontsize=9, color="#888", rotation=90)
axC.set_xlabel("orifice width D (grain diameters ≈ D/2)"); axC.set_ylabel("discharge rate (grains/step)")
axC.set_title("Beverloo: rate rises super-linearly with opening", fontsize=10.5)
axC.grid(alpha=0.3)

fig.suptitle("R104 · Granular hopper (DEM) — constant-rate discharge & Beverloo's law (an hourglass keeps time)",
             fontsize=12.5, y=1.02)
fig.tight_layout(rect=[0, 0, 1, 0.92])
path = os.path.join(OUT, "granular.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
cum8 = runs[8]["cum"]; rising = cum8 < cum8.max() - 2
t = np.arange(len(cum8))[rising]; fit = np.polyfit(t, cum8[rising], 1)
r2 = 1 - ((cum8[rising] - np.polyval(fit, t)).var() / cum8[rising].var())
print(f"orifice8 linearity R2={r2:.3f}  Beverloo rates={[round(r,3) for r in rates]}  Ds={list(Ds)}")
