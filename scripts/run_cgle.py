"""R124 figure — complex Ginzburg-Landau: spiral pinwheels, defect cores, and the road to turbulence."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio.v2 as imageio

from alife.cgle import CGLEConfig, run, defect_count, net_charge, benjamin_feir, winding, defect_curve

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r124_cgle")
os.makedirs(OUT, exist_ok=True)

spiral = run(CGLEConfig(N=240, b=1.0, c=-0.7, steps=6000, seed=1), record_every=60)   # frozen spirals
turb = run(CGLEConfig(N=240, b=2.0, c=-1.4, steps=6000, seed=1))                        # defect turbulence
As, At = spiral["A"], turb["A"]
print(f"spiral: defects={defect_count(As)} net={net_charge(As)} 1+bc={benjamin_feir(1.0,-0.7):+.2f}")
print(f"turbulent: defects={defect_count(At)} net={net_charge(At)} 1+bc={benjamin_feir(2.0,-1.4):+.2f}")

bf, nd = defect_curve(np.linspace(-0.2, -1.6, 9), CGLEConfig(N=160, b=1.6, steps=4000, seed=2))

fig = plt.figure(figsize=(14.5, 8.6), facecolor="white")

axA = fig.add_subplot(2, 2, 1)
axA.imshow(np.angle(As), cmap="hsv", vmin=-np.pi, vmax=np.pi)
axA.set_title(f"Frozen SPIRALS (1+bc=+0.30): phase = colour wheel,\nevery pinwheel is a +/-1 defect "
              f"({defect_count(As)} defects, net charge {net_charge(As)})", fontsize=10)
axA.set_xticks([]); axA.set_yticks([])

axB = fig.add_subplot(2, 2, 2)
im = axB.imshow(np.abs(As), cmap="inferno", vmin=0, vmax=1.25)
axB.set_title("Amplitude |A| of the same field:\neach defect core is a dark dot (|A|->0)", fontsize=10)
axB.set_xticks([]); axB.set_yticks([])
fig.colorbar(im, ax=axB, fraction=0.046, pad=0.04).set_label("|A|", fontsize=9)

axC = fig.add_subplot(2, 2, 3)
axC.imshow(np.angle(At), cmap="hsv", vmin=-np.pi, vmax=np.pi)
axC.set_title(f"Defect TURBULENCE (1+bc=-1.80): spirals broke up\ninto roiling chaos ({defect_count(At)} defects)",
              fontsize=10)
axC.set_xticks([]); axC.set_yticks([])

axD = fig.add_subplot(2, 2, 4)
axD.plot(bf, nd, "o-", color="#3a0ca3")
axD.axvline(0.0, color="#d00000", ls="--", lw=1.3, label="Benjamin-Feir line 1+bc=0")
axD.set_xlabel("1 + b c   (Benjamin-Feir parameter)"); axD.set_ylabel("number of defects")
axD.set_title("Cross the Benjamin-Feir line into 1+bc<0\nand the defect count explodes", fontsize=10)
axD.legend(fontsize=8.5); axD.grid(alpha=0.3); axD.invert_xaxis()

fig.suptitle("R124 · Complex Ginzburg-Landau — one universal equation: rainbow spiral pinwheels (each a "
             "topological defect) that break into defect turbulence across the Benjamin-Feir line",
             fontsize=11.5, y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "cgle.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)

# GIF: the spiral field evolving (defects drift, spirals rotate)
frames = []
for A in spiral["snaps"][-60:]:
    f = plt.figure(figsize=(3.8, 3.8), facecolor="white")
    a = f.add_subplot(111)
    a.imshow(np.angle(A), cmap="hsv", vmin=-np.pi, vmax=np.pi)
    a.set_xticks([]); a.set_yticks([]); a.set_title("CGLE spirals (phase)", fontsize=9)
    f.tight_layout(); f.canvas.draw()
    frames.append(np.asarray(f.canvas.buffer_rgba())[:, :, :3].copy())
    plt.close(f)
gif = os.path.join(OUT, "cgle.gif")
imageio.mimsave(gif, frames, duration=0.08, loop=0)
print("saved", gif, len(frames), "frames")
