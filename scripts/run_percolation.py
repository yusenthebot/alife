"""R97 figure — percolation: the connectivity transition at p_c ≈ 0.593."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.percolation import (occupy, label_clusters, spans, sweep_p,
                               cluster_size_distribution, PC_2D)

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r97_percolation")
os.makedirs(OUT, exist_ok=True)


def colored(grid):
    """RGB image: background white, the spanning cluster red, other clusters blue-ish by size."""
    lbl, n = label_clusters(grid)
    img = np.ones((*grid.shape, 3))
    if n:
        top = set(lbl[0][lbl[0] > 0]); bot = set(lbl[-1][lbl[-1] > 0])
        span_ids = top & bot
        sizes = np.bincount(lbl.ravel())
        for i in range(1, n + 1):
            m = lbl == i
            if i in span_ids:
                img[m] = [0.84, 0.19, 0.15]                # spanning cluster: red
            else:
                shade = 0.35 + 0.5 * (1 - min(sizes[i] / grid.size, 0.3) / 0.3)
                img[m] = [shade, shade, 0.9]               # finite clusters: blue-grey
    return img


L = 160
below = occupy(L, 0.55, seed=1)
above = occupy(L, 0.62, seed=1)

fig = plt.figure(figsize=(15, 8.6), facecolor="white")

axA = fig.add_subplot(2, 3, 1)
axA.imshow(colored(below)); axA.set_title(f"p=0.55 < p_c — only small clusters\n(spanning: {spans(below)})", fontsize=10.5)
axA.axis("off")
axB = fig.add_subplot(2, 3, 2)
axB.imshow(colored(above)); axB.set_title(f"p=0.62 > p_c — a spanning cluster (red)\n(spanning: {spans(above)})", fontsize=10.5)
axB.axis("off")

axC = fig.add_subplot(2, 3, 3)
ps = np.linspace(0.45, 0.75, 22)
for Lc, c in zip((40, 80, 160), ("#90be6d", "#43aa8b", "#277da1")):
    _, sp = sweep_p(ps, size=Lc, trials=40, seed=2, measure="span")
    axC.plot(ps, sp, "-", color=c, label=f"L={Lc}")
axC.axvline(PC_2D, color="crimson", ls="--", lw=1)
axC.text(PC_2D + 0.005, 0.1, f"p_c={PC_2D:.3f}", color="crimson", fontsize=8.5)
axC.set_xlabel("occupation probability p"); axC.set_ylabel("spanning probability")
axC.set_title("Spanning transition sharpens with size", fontsize=10.5)
axC.legend(fontsize=8.5); axC.grid(alpha=0.3)

axD = fig.add_subplot(2, 3, 4)
pp, lf = sweep_p(ps, size=160, trials=30, seed=4, measure="frac")
axD.plot(pp, lf, "o-", color="#5a189a")
axD.axvline(PC_2D, color="crimson", ls="--", lw=1)
axD.set_xlabel("occupation probability p"); axD.set_ylabel("largest-cluster fraction")
axD.set_title("Order parameter rises at p_c", fontsize=10.5)
axD.grid(alpha=0.3)

axE = fig.add_subplot(2, 3, (5, 6))
for p, c, lab in [(0.50, "#8d99ae", "p=0.50 (below): cutoff"), (PC_2D, "#d00000", f"p=p_c: power law")]:
    cx, cy = cluster_size_distribution(320, p, trials=20, seed=5)
    axE.loglog(cx, cy, "o", color=c, ms=4, label=lab)
cx, cy = cluster_size_distribution(320, PC_2D, trials=20, seed=5)
mask = (cx > 2) & (cx < 4000)
slope = np.polyfit(np.log(cx[mask]), np.log(cy[mask]), 1)[0]
axE.loglog(cx[mask], np.exp(np.polyval([slope, np.polyfit(np.log(cx[mask]), np.log(cy[mask]), 1)[1]], np.log(cx[mask]))),
           "--", color="#d00000", lw=1, label=f"slope τ≈{-slope:.2f} (Fisher ~2.05)")
axE.set_xlabel("cluster size s"); axE.set_ylabel("density n(s)")
axE.set_title("Cluster sizes are scale-free exactly at p_c", fontsize=10.5)
axE.legend(fontsize=8.5); axE.grid(alpha=0.3, which="both")

fig.suptitle("R97 · Percolation — a spanning cluster is born at the critical density p_c ≈ 0.593",
             fontsize=13, y=1.0)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "percolation.png")
fig.savefig(path, dpi=110, bbox_inches="tight")
print("saved", path)
print(f"below span={spans(below)}  above span={spans(above)}  power-law tau={-slope:.2f}")
