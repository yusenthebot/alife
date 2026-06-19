"""R130 milestone gallery — one representative panel per round R121-R129 (runs/ gitignored)."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm
from dataclasses import replace

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r130_review")
os.makedirs(OUT, exist_ok=True)
fig, axs = plt.subplots(3, 3, figsize=(13.5, 13), facecolor="white")
A = axs.ravel()
def clean(ax, t):
    ax.set_title(t, fontsize=10); ax.set_xticks([]); ax.set_yticks([])

# R121 flowforage
from alife.flowforage import ForageConfig, run as frun, vortex_flow
r = frun(ForageConfig(L=120, n0=400, steps=420, seed=1), flow=vortex_flow(120, 0.6, 2))
st = r["state"]
A[0].imshow(r["N"].T, cmap="YlGn", origin="lower", extent=[0, 120, 0, 120], alpha=0.85)
A[0].scatter(st["x"], st["y"], s=4, c=st["chi"], cmap="inferno", vmin=0, vmax=4)
clean(A[0], "R121 flow-coupled foragers (evolve chemotaxis)")

# R122 dielectric
from alife.dielectric import DBMConfig, grow
cl = grow(DBMConfig(M=121, eta=1.0, target=900, batch=5, seed=1))["cluster"]
c = cl.shape[0] // 2; ci, cj = np.where(cl)
img = np.full(cl.shape, np.nan); img[ci, cj] = np.hypot(ci - c, cj - c)
A[1].imshow(img, cmap="turbo"); clean(A[1], "R122 dielectric breakdown (DLA-fractal eta=1)")

# R123 selfpropelled mill
from alife.selfpropelled import SPPConfig, run as srun, PRESETS
m = srun(replace(PRESETS["mill"], N=350, steps=2400, seed=1))
xm = m["x"] - m["x"].mean(0); ang = np.arctan2(m["v"][:, 1], m["v"][:, 0])
A[2].scatter(xm[:, 0], xm[:, 1], s=8, c=ang, cmap="hsv"); A[2].set_aspect("equal"); clean(A[2], "R123 self-propelled mill (rotating ring)")

# R124 cgle spirals
from alife.cgle import CGLEConfig, run as crun
A[3].imshow(np.angle(crun(CGLEConfig(N=200, b=1.0, c=-0.7, steps=5000, seed=1))["A"]), cmap="hsv")
clean(A[3], "R124 complex Ginzburg-Landau spirals")

# R125 cahnhilliard
from alife.cahnhilliard import CHConfig, run as chrun
A[4].imshow(chrun(CHConfig(N=200, steps=6000, seed=1))["c"], cmap="RdBu", vmin=-1, vmax=1)
clean(A[4], "R125 Cahn-Hilliard coarsening")

# R126 coatpattern (tapered creature)
from alife.coatpattern import CoatConfig, run_shape, body_tail_mask
mask = body_tail_mask(110, 300, 92, 24)
A[5].imshow(np.where(mask, run_shape(CoatConfig(steps=11000, seed=1), mask), np.nan), cmap="copper", vmin=0, vmax=0.42)
clean(A[5], "R126 animal coat (spotted body / tail)")

# R127 swifthohenberg hexagons
from alife.swifthohenberg import SHConfig, run as shrun
A[6].imshow(shrun(SHConfig(N=200, r=0.1, g=1.2, steps=5000, seed=1))["u"], cmap="RdBu"); clean(A[6], "R127 Swift-Hohenberg hexagons (Benard)")

# R128 lanes
from alife.lanes import LaneConfig, run as lrun
lr = lrun(LaneConfig(N=900, L=46, steps=5000, seed=1)); p, sp = lr["pos"], lr["species"]
A[7].scatter(p[sp > 0, 0], p[sp > 0, 1], s=5, c="#d00000"); A[7].scatter(p[sp < 0, 0], p[sp < 0, 1], s=5, c="#1d6fb8")
A[7].set_aspect("equal"); clean(A[7], "R128 lane formation (counter-flow)")

# R129 chladni
from alife.chladni import ChladniConfig, assemble_sand
ch = assemble_sand(ChladniConfig(m=5, n=2, c=-1.0, ngrain=6000, steps=550, seed=1))
A[8].imshow(np.abs(ch["phi"]), cmap="Greys", vmin=0, vmax=1.6, extent=[0, 1, 0, 1], origin="lower", alpha=0.2)
A[8].scatter(ch["pos"][:, 0], ch["pos"][:, 1], s=1.4, c="#161616"); A[8].set_aspect("equal"); clean(A[8], "R129 Chladni figure (sand on nodes)")

fig.suptitle("ALife — milestone gallery R121-R129 (visual-checkable streak; every headline re-verified at the R130 review)",
             fontsize=13, y=0.995)
fig.tight_layout(rect=[0, 0, 1, 0.97])
path = os.path.join(OUT, "gallery.png")
fig.savefig(path, dpi=110, bbox_inches="tight")
print("saved", path)
