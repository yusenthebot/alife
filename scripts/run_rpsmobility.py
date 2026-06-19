"""R111 figure — spatial RPS: mobility threshold for biodiversity (Reichenbach-Mobilia-Frey)."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

from alife.rpsmobility import run, survival_curve, n_survivors

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r111_rpsmobility")
os.makedirs(OUT, exist_ok=True)
CMAP = ListedColormap(["#ffffff", "#e63946", "#2a9d8f", "#457b9d"])   # empty, A, B, C

lo = run(L=150, mobility=3.0, steps=700, seed=2)       # coexistence (spiral regime)
hi = run(L=150, mobility=45.0, steps=700, seed=2)      # past threshold -> collapse
ms, surv = survival_curve(np.array([1, 3, 6, 10, 16, 24, 34, 46]), L=100, steps=600, seed=4, reps=3)

fig = plt.figure(figsize=(15, 4.8), facecolor="white")

axA = fig.add_subplot(1, 3, 1)
axA.imshow(lo["grid"], cmap=CMAP, vmin=0, vmax=3, interpolation="nearest")
axA.set_title(f"Low mobility (=3): spiral waves,\nall 3 coexist (survivors {n_survivors(lo)})", fontsize=10.5)
axA.set_xticks([]); axA.set_yticks([])

axB = fig.add_subplot(1, 3, 2)
axB.imshow(hi["grid"], cmap=CMAP, vmin=0, vmax=3, interpolation="nearest")
axB.set_title(f"High mobility (=45): spirals merge,\nbiodiversity lost (survivors {n_survivors(hi)})", fontsize=10.5)
axB.set_xticks([]); axB.set_yticks([])

axC = fig.add_subplot(1, 3, 3)
axC.plot(ms, surv, "o-", color="#6a040f")
axC.axhline(3, color="#2a9d8f", ls=":", lw=1, label="all 3 coexist")
axC.axhline(1, color="#e63946", ls=":", lw=1, label="biodiversity lost")
axC.set_xlabel("mobility (mixing per generation)"); axC.set_ylabel("surviving species")
axC.set_title("Critical mobility: diversity collapses\nwhen mixing exceeds a threshold", fontsize=10.5)
axC.set_ylim(0.8, 3.2); axC.legend(fontsize=8.5); axC.grid(alpha=0.3)

fig.suptitle("R111 · Spatial rock-paper-scissors — mobility destroys biodiversity past a threshold (RMF 2007)",
             fontsize=12.5, y=1.02)
fig.tight_layout(rect=[0, 0, 1, 0.92])
path = os.path.join(OUT, "rpsmobility.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
print(f"low-mob survivors={n_survivors(lo)}  high-mob survivors={n_survivors(hi)}  survival curve={list(surv)}")
