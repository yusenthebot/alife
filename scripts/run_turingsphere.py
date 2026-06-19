"""R138 figure — Turing patterns on a sphere: an animal coat on a curved, closed body.

Top row: Gray-Scott on the icosphere in three regimes (spots / labyrinth / coral), rendered as 3D balls.
Bottom: (B) spot count grows with sphere size (subdiv = effective R/λ) — the closed geometry quantises
the pattern; (C) the spotted ball unwrapped to a lon-lat map (full-globe coverage, no seams).
GIF: the spotted sphere rotating.
"""

from __future__ import annotations

import os

import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import replace
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from alife.turingsphere import TuringSphereConfig, run, count_spots

OUT = "runs/r138_turingsphere"
os.makedirs(OUT, exist_ok=True)


def render(ax, V, F, v, cmap, elev=18, azim=0):
    vf = v[F].mean(1)
    norm = (vf - vf.min()) / (np.ptp(vf) + 1e-9)
    polys = V[F]
    pc = Poly3DCollection(polys, facecolors=plt.get_cmap(cmap)(norm), edgecolors="none")
    ax.add_collection3d(pc)
    ax.set_xlim(-0.72, 0.72); ax.set_ylim(-0.72, 0.72); ax.set_zlim(-0.72, 0.72)
    ax.set_box_aspect((1, 1, 1)); ax.set_axis_off(); ax.view_init(elev, azim)


def main():
    regimes = [("spots", 0.0367, 0.0649, "copper"),
               ("labyrinth", 0.030, 0.062, "viridis"),
               ("coral", 0.025, 0.060, "BuGn")]
    print("running 3 coat regimes on the sphere (subdiv 5) ...")
    fields = []
    for name, F, k, cmap in regimes:
        r = run(TuringSphereConfig(subdiv=5, F=F, k=k, steps=14000, seed=3))
        fields.append((name, r, cmap))
        print(f"  {name}: spots~{count_spots(r['v'], r['A'])}  high-frac {(r['v']>0.2).mean():.3f}")

    print("spot-count vs sphere size ...")
    sizes = []
    for sd in [3, 4, 5]:
        r = run(TuringSphereConfig(subdiv=sd, F=0.0367, k=0.0649, steps=14000, seed=3))
        sizes.append((len(r["V"]), count_spots(r["v"], r["A"])))
        print(f"  subdiv {sd}: verts {sizes[-1][0]}  spots {sizes[-1][1]}")

    fig = plt.figure(figsize=(15, 9))
    for i, (name, r, cmap) in enumerate(fields):
        ax = fig.add_subplot(2, 3, i + 1, projection="3d")
        render(ax, r["V"], r["F"], r["v"], cmap, azim=25)
        ax.set_title(f"{name}  (F={regimes[i][1]}, k={regimes[i][2]})", fontsize=11)

    axB = fig.add_subplot(2, 3, 4)
    sz = np.array(sizes, float)
    axB.plot(sz[:, 0], sz[:, 1], "o-", color="#d62728", ms=9)
    axB.set_xlabel("mesh vertices (≈ sphere area / edge²)"); axB.set_ylabel("number of spots")
    axB.set_title("B. Closed geometry quantises the pattern\n(bigger sphere → more spots)")

    # unwrap the spotted ball to a lon-lat map
    name, r, cmap = fields[0]
    V, v = r["V"], r["v"]
    lon = np.arctan2(V[:, 1], V[:, 0]); lat = np.arcsin(np.clip(V[:, 2], -1, 1))
    axC = fig.add_subplot(2, 3, 5)
    axC.scatter(lon, lat, c=v, cmap=cmap, s=6)
    axC.set_xlabel("longitude"); axC.set_ylabel("latitude")
    axC.set_title("C. Spotted ball unwrapped (full-globe, no seam)")

    axD = fig.add_subplot(2, 3, 6, projection="3d")
    render(axD, fields[0][1]["V"], fields[0][1]["F"], fields[0][1]["v"], "copper", azim=160)
    axD.set_title("D. Same ball, far side", fontsize=11)

    fig.suptitle("R138 — Turing patterns on a sphere: an animal coat on a curved closed surface (Gray-Scott, icosphere)",
                 fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(f"{OUT}/turingsphere.png", dpi=110)
    print(f"wrote {OUT}/turingsphere.png")

    print("rendering rotating GIF ...")
    r = fields[0][1]
    frames = []
    gfig = plt.figure(figsize=(5, 5))
    for az in range(0, 360, 12):
        gfig.clf()
        gax = gfig.add_subplot(111, projection="3d")
        render(gax, r["V"], r["F"], r["v"], "copper", azim=az)
        gax.set_title("Turing coat on a sphere", fontsize=11)
        gfig.tight_layout(); gfig.canvas.draw()
        frames.append(np.asarray(gfig.canvas.buffer_rgba())[:, :, :3].copy())
    imageio.mimsave(f"{OUT}/turingsphere.gif", frames, fps=12, loop=0)
    print(f"wrote {OUT}/turingsphere.gif ({len(frames)} frames)")


if __name__ == "__main__":
    main()
