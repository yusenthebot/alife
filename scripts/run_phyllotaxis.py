"""R118 figure — phyllotaxis: the golden angle uniquely packs, and emerges from a least-crowding rule."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.phyllotaxis import (
    GOLDEN_ANGLE, vogel, packing_uniformity, uniformity_curve, douady_couder, bifurcation,
)

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r118_phyllotaxis")
os.makedirs(OUT, exist_ok=True)

N = 900
alphas = np.arange(130.0, 145.0, 0.05)
au, mn = uniformity_curve(alphas, n=500)
traj = douady_couder(n=340, G=0.28, n_ang=2880)["divergence"]
Gs, bang = bifurcation(np.linspace(0.10, 0.42, 17), n=260, drop=120)
print(f"golden={GOLDEN_ANGLE:.3f}  peak-uniformity alpha={au[int(np.argmax(mn))]:.2f}  "
      f"emergent(G=0.28) tail={traj[150:].mean():.2f}")

fig = plt.figure(figsize=(15, 8.6), facecolor="white")

def spiral(ax, alpha, title):
    P = vogel(alpha, N)
    ax.scatter(P[:, 0], P[:, 1], s=7, c=np.arange(N), cmap="viridis")
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(title, fontsize=10.5)

spiral(fig.add_subplot(2, 3, 1), GOLDEN_ANGLE, f"Golden angle {GOLDEN_ANGLE:.2f}deg:\nuniform, gap-free packing (sunflower)")
spiral(fig.add_subplot(2, 3, 2), 137.0, "137.0deg (0.5deg off golden):\ngaps open into spiral arms")
spiral(fig.add_subplot(2, 3, 3), 144.0, "144deg = 2/5 turn (rational):\n5 radial spokes, big gaps")

axD = fig.add_subplot(2, 3, 4)
axD.plot(au, mn, color="#2a9d8f", lw=1.6)
axD.axvline(GOLDEN_ANGLE, color="#d00000", ls="--", lw=1.3, label=f"golden {GOLDEN_ANGLE:.2f}")
axD.set_xlabel("divergence angle (deg)"); axD.set_ylabel("min nearest-neighbour gap")
axD.set_title("Packing optimum: spread-out-ness peaks\nsharply AT the golden angle", fontsize=10.5)
axD.legend(fontsize=8.5); axD.grid(alpha=0.3)

axE = fig.add_subplot(2, 3, 5)
axE.plot(np.arange(traj.size), traj, color="#3a0ca3", lw=1.0)
axE.axhline(GOLDEN_ANGLE, color="#d00000", ls="--", lw=1.3, label=f"golden {GOLDEN_ANGLE:.2f}")
axE.set_xlabel("primordium number"); axE.set_ylabel("divergence angle (deg)")
axE.set_ylim(60, 180)
axE.set_title("Emergence (Douady-Couder): least-crowding\nrule locks onto the golden angle", fontsize=10.5)
axE.legend(fontsize=8.5); axE.grid(alpha=0.3)

axF = fig.add_subplot(2, 3, 6)
axF.scatter(Gs, bang, c="#e85d04", s=28)
axF.axhline(GOLDEN_ANGLE, color="#d00000", ls="--", lw=1.1, label=f"golden {GOLDEN_ANGLE:.1f}")
axF.axhline(99.5, color="#0077b6", ls=":", lw=1.1, label="Lucas ~99.5")
axF.set_xlabel("growth rate  G"); axF.set_ylabel("emergent divergence angle (deg)")
axF.set_title("Bifurcation: growth rate selects the branch\n(golden vs Lucas) -- both seen in real plants", fontsize=10.5)
axF.legend(fontsize=8.5); axF.grid(alpha=0.3)

fig.suptitle("R118 · Phyllotaxis — the golden angle uniquely packs organs gap-free (Vogel) AND emerges "
             "from a purely local least-crowding rule (Douady-Couder 1992); hence Fibonacci spirals",
             fontsize=11.5, y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "phyllotaxis.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
