"""R99 figure — motility-induced phase separation: active particles cluster with no attraction."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dataclasses import replace

from alife.mips import simulate, density_cv, MIPSConfig

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r99_mips")
os.makedirs(OUT, exist_ok=True)
base = MIPSConfig()

mips = simulate(base, seed=1)
const = simulate(replace(base, rho_star=1e9), seed=1)        # constant speed: active gas (control)
v0s = np.linspace(0, 6, 10)
cv_sweep = [np.mean([density_cv(simulate(replace(base, v0=float(v)), seed=s)) for s in range(3)]) for v in v0s]

fig = plt.figure(figsize=(15, 4.8), facecolor="white")

axA = fig.add_subplot(1, 4, 1)
axA.scatter(mips["pos"][:, 0], mips["pos"][:, 1], s=3, c="#d00000", alpha=0.35, edgecolors="none")
axA.set_title(f"MIPS: slow-in-crowds →\ndense clusters + dilute gas (CV={density_cv(mips):.1f})", fontsize=9.5)
axA.set_aspect("equal"); axA.set_xlim(0, base.box); axA.set_ylim(0, base.box); axA.set_xticks([]); axA.set_yticks([])

axB = fig.add_subplot(1, 4, 2)
axB.scatter(const["pos"][:, 0], const["pos"][:, 1], s=3, c="#457b9d", alpha=0.35, edgecolors="none")
axB.set_title(f"Control: constant speed →\nhomogeneous active gas (CV={density_cv(const):.1f})", fontsize=9.5)
axB.set_aspect("equal"); axB.set_xlim(0, base.box); axB.set_ylim(0, base.box); axB.set_xticks([]); axB.set_yticks([])

axC = fig.add_subplot(1, 4, 3)
axC.imshow(mips["counts"].T, origin="lower", cmap="inferno", interpolation="nearest")
axC.set_title("MIPS density field\n(dense domains in a void)", fontsize=9.5); axC.axis("off")

axD = fig.add_subplot(1, 4, 4)
axD.plot(v0s, cv_sweep, "o-", color="#6a040f")
axD.axhline(density_cv(const), color="#888", ls=":", lw=1, label="active gas baseline")
axD.set_xlabel("self-propulsion speed v0"); axD.set_ylabel("density CV (phase separation)")
axD.set_title("Onset with activity:\nno attraction needed", fontsize=9.5)
axD.legend(fontsize=8); axD.grid(alpha=0.3)

fig.suptitle("R99 · Motility-induced phase separation — activity alone makes clusters (no attractive force)",
             fontsize=12.5, y=1.03)
fig.tight_layout(rect=[0, 0, 1, 0.92])
path = os.path.join(OUT, "mips.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
print(f"MIPS CV={density_cv(mips):.2f}  const CV={density_cv(const):.2f}  v0-sweep CV={[round(c,1) for c in cv_sweep]}")
