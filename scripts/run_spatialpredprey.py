"""R109 figure — spatial predator-prey: space stabilizes coexistence (pursuit waves)."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.spatialpredprey import simulate, well_mixed, fluctuation, min_density, PPConfig

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r109_spatialpredprey")
os.makedirs(OUT, exist_ok=True)
c = PPConfig(steps=5000)

sp = simulate(c, seed=1, record_every=0)
wm = well_mixed(c, seed=1)

fig = plt.figure(figsize=(15, 4.8), facecolor="white")

# A. spatial prey field (pursuit waves / patches)
axA = fig.add_subplot(1, 3, 1)
im = axA.imshow(sp["U"], cmap="viridis", interpolation="bilinear")
axA.set_title("Prey density field — pursuit waves / patches\n(asynchronous local oscillations)", fontsize=10)
axA.set_xticks([]); axA.set_yticks([])
fig.colorbar(im, ax=axA, fraction=0.046)

# B. global population time series: well-mixed (fragile) vs spatial (stable)
axB = fig.add_subplot(1, 3, 2)
t = np.arange(len(wm["mu"]))
axB.plot(t, wm["mu"], color="#d00000", lw=0.8, label="well-mixed prey (boom-bust)")
axB.plot(t, sp["mu"], color="#1f77b4", lw=1.0, label="spatial prey (global mean)")
axB.axhline(0, color="#aaa", lw=0.8)
axB.set_xlabel("time step"); axB.set_ylabel("global prey density")
axB.set_title("Well-mixed crashes near extinction;\nspatial stays steady & safe", fontsize=10)
axB.legend(fontsize=8.5)

# C. stabilization quantified
axC = fig.add_subplot(1, 3, 3)
labels = ["global\nfluctuation (std)", "minimum\ndensity"]
wmv = [fluctuation(wm["mu"]), min_density(wm["mu"])]
spv = [fluctuation(sp["mu"]), min_density(sp["mu"])]
x = np.arange(2); w = 0.35
axC.bar(x - w / 2, wmv, w, color="#d00000", label="well-mixed")
axC.bar(x + w / 2, spv, w, color="#1f77b4", label="spatial")
axC.set_xticks(x); axC.set_xticklabels(labels)
axC.set_title("Space → smaller swings, higher floor\n(further from extinction)", fontsize=10)
axC.legend(fontsize=9)

fig.suptitle("R109 · Spatial predator-prey (reaction-diffusion) — space rescues coexistence from boom-bust",
             fontsize=12.5, y=1.02)
fig.tight_layout(rect=[0, 0, 1, 0.92])
path = os.path.join(OUT, "spatialpredprey.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
print(f"well-mixed: std={fluctuation(wm['mu']):.3f} min={min_density(wm['mu']):.4f}  "
      f"spatial: std={fluctuation(sp['mu']):.3f} min={min_density(sp['mu']):.4f}  field-std={sp['U'].std():.3f}")
