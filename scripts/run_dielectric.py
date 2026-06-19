"""R122 figure — dielectric-breakdown model: one exponent eta from compact blobs to lightning needles."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dataclasses import replace

from alife.dielectric import DBMConfig, grow, solve_field, fractal_dimension, dimension_curve

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r122_dielectric")
os.makedirs(OUT, exist_ok=True)

base = DBMConfig(M=151, target=1300, batch=5, seed=1)

def cluster_img(cl):
    c = cl.shape[0] // 2
    ci, cj = np.where(cl)
    img = np.full(cl.shape, np.nan)
    img[ci, cj] = np.hypot(ci - c, cj - c)
    return img

clusters = {}
for eta in (0.0, 1.0, 2.0, 4.0):
    r = grow(replace(base, eta=eta))
    clusters[eta] = (r["cluster"], fractal_dimension(r["cluster"]), r.get("phi"))
    print(f"eta={eta}: mass={r['mass']} D={clusters[eta][1]:.2f}")

etas, dims = dimension_curve(np.linspace(0.0, 5.0, 9), replace(base, M=111, target=750, batch=5))
print("D curve:", list(np.round(dims, 2)))

fig = plt.figure(figsize=(15, 8.6), facecolor="white")

titles = {0.0: "eta=0: ignore field -> COMPACT (D~2)",
          1.0: "eta=1: DLA regime -> FRACTAL",
          2.0: "eta=2: sparser branches",
          4.0: "eta=4: tip wins -> NEEDLES (D~1)"}
for k, eta in enumerate((0.0, 1.0, 2.0, 4.0)):
    ax = fig.add_subplot(2, 3, k + 1 if k < 2 else k + 2)   # slots 1,2,4,5 ; 3 & 6 for plots
    cl, D, _ = clusters[eta]
    ax.imshow(cluster_img(cl), cmap="turbo", interpolation="nearest")
    ax.set_title(f"{titles[eta]}\n(measured D={D:.2f})", fontsize=10)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_facecolor("#111")

# D vs eta curve
axC = fig.add_subplot(2, 3, 3)
axC.plot(etas, dims, "o-", color="#3a0ca3")
axC.axhline(2.0, color="#aaa", ls=":", lw=1, label="compact D=2")
axC.axhline(1.71, color="#2a9d8f", ls="--", lw=1.1, label="DLA D~1.71 (eta=1)")
axC.set_xlabel("growth exponent  eta"); axC.set_ylabel("fractal dimension  D")
axC.set_title("One knob spans the morphologies:\nD falls from 2 (compact) toward 1 (needle)", fontsize=10)
axC.legend(fontsize=8); axC.grid(alpha=0.3)

# harmonic field screening
axF = fig.add_subplot(2, 3, 6)
cl, _, phi = clusters[1.0]
if phi is None:
    phi = solve_field(cl)
disp = np.where(cl, np.nan, phi)
im = axF.imshow(disp, cmap="magma", interpolation="nearest")
axF.set_title("Why: the harmonic field is high at TIPS,\nscreened in fjords -> tips grow (eta sharpens it)", fontsize=10)
axF.set_xticks([]); axF.set_yticks([])
fig.colorbar(im, ax=axF, fraction=0.046, pad=0.04).set_label("potential phi", fontsize=9)

fig.suptitle("R122 · Dielectric-breakdown model (Niemeyer-Pietronero-Wiesmann 1984) — Laplacian growth "
             "with one exponent eta sweeps compact -> DLA-fractal -> lightning needles; generalises R78 DLA",
             fontsize=11.5, y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "dielectric.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
