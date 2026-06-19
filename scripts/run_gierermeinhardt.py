"""R92 figure — Gierer-Meinhardt activator-inhibitor: Turing spots, intrinsic wavelength, mechanism.

Same chemistry: a slow activator + a fast inhibitor make spots with an intrinsic wavelength, so spot
count scales with coat area; geometry sets the arrangement. (Murray's clean spots-vs-stripes-by-
geometry did not reproduce in this spot regime — see module docstring; an honest negative.)
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.gierermeinhardt import run, count_spots, stripe_index, GMConfig

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r92_gierermeinhardt")
os.makedirs(OUT, exist_ok=True)
cfg = GMConfig()
CMAP = "copper"

# A. a 2D coat -> spots (the activator field)
square = run((130, 130), cfg, seed=1)

# B. intrinsic wavelength: spot count scales with area
sizes = [50, 70, 90, 110, 140]
areas = [s * s for s in sizes]
spots = [count_spots(run((s, s), cfg, seed=2)) for s in sizes]

# C. the mechanism: activator (sharp peaks) vs inhibitor (broad halos), anti-correlated
a_field, h_field = run((90, 90), cfg, seed=3, return_h=True)

# D. geometry sets arrangement: wide square (many rows) vs narrow strip (one row, elongated)
strip = run((12, 200), cfg, seed=4)

fig = plt.figure(figsize=(15, 8.6), facecolor="white")

axA = fig.add_subplot(2, 2, 1)
axA.imshow(square, cmap=CMAP, interpolation="bilinear")
axA.set_title(f"Activator-inhibitor coat → Turing spots ({count_spots(square)})", fontsize=10.5)
axA.axis("off")

axB = fig.add_subplot(2, 2, 2)
axB.plot(areas, spots, "o-", color="#8a5a2b")
m, b = np.polyfit(areas, spots, 1)
axB.plot(areas, np.array(areas) * m + b, "--", color="#c9a06a", lw=1)
axB.set_xlabel("coat area (cells)"); axB.set_ylabel("number of spots")
axB.set_title(f"Intrinsic wavelength: spots ∝ area\n(~{m*1000:.1f} spots / 1000 cells, constant spacing)", fontsize=10.5)
axB.grid(alpha=0.3)

axC = fig.add_subplot(2, 2, 3)
# show activator and inhibitor side by side at matching scale
both = np.concatenate([a_field / a_field.max(), np.ones((90, 4)),
                       h_field / h_field.max()], axis=1)
axC.imshow(both, cmap="magma", interpolation="bilinear")
axC.set_title(f"Mechanism: sharp ACTIVATOR (left) + broader INHIBITOR (right)\n"
              f"inhibitor diffuses {cfg.Dh/cfg.Da:.0f}× faster → long-range inhibition sets the wavelength",
              fontsize=10.5)
axC.axis("off")

axD = fig.add_subplot(2, 2, 4)
axD.imshow(strip, cmap=CMAP, interpolation="bilinear", aspect="auto")
axD.set_title(f"Geometry sets arrangement: a narrow strip → a single row of spots\n"
              f"(elongation {stripe_index(strip):.2f} vs {stripe_index(square):.2f} on the square)", fontsize=10.5)
axD.axis("off")

fig.suptitle("R92 · Gierer–Meinhardt activator-inhibitor — Turing spots with an intrinsic wavelength",
             fontsize=13, y=1.0)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "gierermeinhardt.png")
fig.savefig(path, dpi=110, bbox_inches="tight")
print("saved", path)
print(f"square spots={count_spots(square)}  area-scaling spots={spots}  Dh/Da={cfg.Dh/cfg.Da:.0f}")
