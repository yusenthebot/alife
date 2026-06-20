"""R140 milestone gallery — one headline frame per round R131-R139 in a single poster.

Renders a small/fast instance of each recent model and tiles their signature visuals. Eye-check that the
whole recent arc still produces recognizable, correct-looking results.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

OUT = "runs/r140_gallery"
os.makedirs(OUT, exist_ok=True)

fig = plt.figure(figsize=(15, 15))


def panel(i):
    return fig.add_subplot(3, 3, i)


# R131 barkley spiral
from alife.barkley import BarkleyConfig, run_spiral
u = run_spiral(BarkleyConfig(N=170, steps=2200))["u"]
ax = panel(1); ax.imshow(u, cmap="inferno"); ax.set_xticks([]); ax.set_yticks([])
ax.set_title("R131 Excitable media — BZ spiral wave", fontsize=11)

# R132 wolfsheep cycles
from alife.wolfsheep import WolfSheepConfig, run as wsrun
w = wsrun(WolfSheepConfig(steps=2500, seed=2))
ax = panel(2)
ax.plot(w["sheep"], color="#2ca02c", lw=0.8, label="sheep")
ax.plot(w["wolves"], color="#d62728", lw=0.8, label="wolves")
ax.set_title("R132 Wolf-Sheep — boom-bust cycles", fontsize=11); ax.legend(fontsize=7); ax.set_xticks([])

# R133 termites mounds
from alife.termites import TermiteConfig, run as trun
M = trun(TermiteConfig(steps=2500, k=6.0, seed=2))["M"]
ax = panel(3); ax.imshow(M, cmap="copper"); ax.set_xticks([]); ax.set_yticks([])
ax.set_title("R133 Termite stigmergy — mounds", fontsize=11)

# R134 murmuration
from alife.murmuration import MurmurConfig, run as mrun
r = mrun(MurmurConfig(N=140, steps=700, seed=2))
ax = panel(4)
vu = r["v"] / np.maximum(np.hypot(r["v"][:, 0], r["v"][:, 1])[:, None], 1e-9)
ax.quiver(r["p"][:, 0], r["p"][:, 1], vu[:, 0], vu[:, 1], color="#1f77b4", scale=40, width=0.005)
ax.plot(r["pp"][0], r["pp"][1], "o", ms=13, color="#d62728")
ax.set_xlim(0, MurmurConfig.L); ax.set_ylim(0, MurmurConfig.L); ax.set_aspect("equal")
ax.set_xticks([]); ax.set_yticks([]); ax.set_title("R134 Murmuration — flock flees hawk", fontsize=11)

# R135 faraday
from alife.faraday import FaradayConfig, run as frun
f = frun(FaradayConfig(N=96, steps=11000, seed=2))["field"]
ax = panel(5); v = np.abs(f).max(); ax.imshow(f, cmap="RdBu_r", vmin=-v, vmax=v)
ax.set_xticks([]); ax.set_yticks([]); ax.set_title("R135 Faraday waves — standing lattice", fontsize=11)

# R136 graingrowth
from alife.graingrowth import GrainConfig, run as grun
g = grun(GrainConfig(L=200, steps=160, seed=2))
lut = np.random.default_rng(7).random((GrainConfig.Q, 3)) * 0.85 + 0.1
ax = panel(6); ax.imshow(lut[g["s"]], interpolation="nearest"); ax.set_xticks([]); ax.set_yticks([])
ax.set_title("R136 Grain growth — coarsened mosaic", fontsize=11)

# R137 fisherfront 2D colony
from alife.fisherfront import FrontConfig, run2d
c = run2d(FrontConfig(), N=170, steps=320, seed_radius=10)["u"]
ax = panel(7); ax.imshow(c, cmap="YlGn", vmin=0, vmax=1); ax.set_xticks([]); ax.set_yticks([])
ax.set_title("R137 Fisher-KPP — invasion front", fontsize=11)

# R138 turingsphere
from alife.turingsphere import TuringSphereConfig, run as tsrun
ts = tsrun(TuringSphereConfig(subdiv=5, steps=13000, seed=3))
ax = fig.add_subplot(3, 3, 8, projection="3d")
vf = ts["v"][ts["F"]].mean(1); norm = (vf - vf.min()) / (np.ptp(vf) + 1e-9)
ax.add_collection3d(Poly3DCollection(ts["V"][ts["F"]], facecolors=plt.get_cmap("copper")(norm), edgecolors="none"))
ax.set_xlim(-0.7, 0.7); ax.set_ylim(-0.7, 0.7); ax.set_zlim(-0.7, 0.7)
ax.set_box_aspect((1, 1, 1)); ax.set_axis_off(); ax.view_init(18, 25)
ax.set_title("R138 Turing on a sphere — coat", fontsize=11)

# R139 dendrite
from alife.dendrite import DendriteConfig, run as drun
p = drun(DendriteConfig(N=300, j=6, steps=4000, seed=3))["p"]
ax = panel(9); ax.imshow(p, cmap="bone"); ax.set_xticks([]); ax.set_yticks([])
ax.set_title("R139 Dendrite — snowflake crystal", fontsize=11)

fig.suptitle("alife milestone gallery — R131-R139 (excitable media → dendritic solidification)", fontsize=15)
fig.tight_layout(rect=(0, 0, 1, 0.98))
fig.savefig(f"{OUT}/gallery_r140.png", dpi=100)
print(f"wrote {OUT}/gallery_r140.png")
