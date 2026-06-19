"""R123 figure — self-propelled particles: spinning MILL vs marching FLOCK vs still CLUMP (+ mill GIF)."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio.v2 as imageio
from dataclasses import replace

from alife.selfpropelled import SPPConfig, run, PRESETS, polarization, milling

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r123_selfpropelled")
os.makedirs(OUT, exist_ok=True)

mill = run(replace(PRESETS["mill"], N=350, steps=2600, seed=1), record_every=8)
flock = run(replace(PRESETS["flock"], N=350, steps=2600, seed=1), record_every=8)
clump = run(replace(PRESETS["clump"], N=350, steps=2200, seed=1), record_every=8)
for nm, r in [("mill", mill), ("flock", flock), ("clump", clump)]:
    print(f"{nm}: P={r['P'][-20:].mean():.2f} M={r['M'][-20:].mean():.2f}")


def draw(ax, x, v, title, color):
    c = x.mean(0)
    xc = x - c
    ax.quiver(xc[:, 0], xc[:, 1], v[:, 0], v[:, 1], color=color, scale=34, width=0.005,
              headwidth=4, alpha=0.9)
    R = np.abs(xc).max() * 1.15
    ax.set_xlim(-R, R); ax.set_ylim(-R, R); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([]); ax.set_title(title, fontsize=11)


fig = plt.figure(figsize=(14.5, 4.8), facecolor="white")
ax1 = fig.add_subplot(1, 4, 1); draw(ax1, *mill["snaps"][-1], "MILL: a hollow spinning ring\n(P~0, M~1)", "#1d6fb8")
ax2 = fig.add_subplot(1, 4, 2); draw(ax2, *flock["snaps"][-1], "FLOCK: all march one way\n(P~1, M~0)", "#2a9d8f")
ax3 = fig.add_subplot(1, 4, 3); draw(ax3, *clump["snaps"][-1], "CLUMP: a still disordered blob\n(P~0, M~0)", "#9b5de5")

ax4 = fig.add_subplot(1, 4, 4)
labels = ["mill", "flock", "clump"]
Ps = [mill["P"][-20:].mean(), flock["P"][-20:].mean(), clump["P"][-20:].mean()]
Ms = [mill["M"][-20:].mean(), flock["M"][-20:].mean(), clump["M"][-20:].mean()]
xb = np.arange(3)
ax4.bar(xb - 0.18, Ps, 0.36, label="polarization P", color="#2a9d8f")
ax4.bar(xb + 0.18, Ms, 0.36, label="milling M", color="#1d6fb8")
ax4.set_xticks(xb); ax4.set_xticklabels(labels); ax4.set_ylim(0, 1.05)
ax4.set_title("(P, M) signature names each state", fontsize=11); ax4.legend(fontsize=8.5)
ax4.grid(alpha=0.3, axis="y")

fig.suptitle("R123 · Self-propelled particles (D'Orsogna 2006) — same rules, one knob: a spinning MILL, a "
             "marching FLOCK, or a still CLUMP; read the shape by eye, confirm with (P, M)", fontsize=11.5, y=1.02)
fig.tight_layout()
path = os.path.join(OUT, "selfpropelled.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)

# hero animated GIF: the mill spinning (last ~55 frames, recentered)
frames = []
snaps = mill["snaps"][-55:]
for x, v in snaps:
    f = plt.figure(figsize=(3.6, 3.6), facecolor="white")
    a = f.add_subplot(111)
    xc = x - x.mean(0)
    ang = np.arctan2(v[:, 1], v[:, 0])
    a.scatter(xc[:, 0], xc[:, 1], s=12, c=ang, cmap="hsv", vmin=-np.pi, vmax=np.pi)
    R = np.abs(xc).max() * 1.15
    a.set_xlim(-R, R); a.set_ylim(-R, R); a.set_aspect("equal"); a.set_xticks([]); a.set_yticks([])
    a.set_title("milling torus — circulating, hollow centre", fontsize=9)
    f.tight_layout()
    f.canvas.draw()
    frames.append(np.asarray(f.canvas.buffer_rgba())[:, :, :3].copy())
    plt.close(f)
gif = os.path.join(OUT, "mill.gif")
imageio.mimsave(gif, frames, duration=0.08, loop=0)
print("saved", gif, len(frames), "frames")
