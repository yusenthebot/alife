"""R128 figure — lane formation: counter-flowing crowds self-organise into lanes."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio.v2 as imageio
from dataclasses import replace

from alife.lanes import LaneConfig, run, lane_order

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r128_lanes")
os.makedirs(OUT, exist_ok=True)

cfg = LaneConfig(N=900, L=46.0, steps=5500, seed=1)
r = run(cfg, record_every=40)
snaps = r["snaps"]
ctrl = run(replace(cfg, v0=0.0))
print(f"lanes order={r['order'][-20:].mean():.2f}  no-drive order={ctrl['order'][-20:].mean():.2f}")

# noise melting transition
noises = np.linspace(0.1, 3.0, 9)
ord_noise = [run(replace(cfg, N=600, steps=3000, noise=float(n), seed=2))["order"][-20:].mean() for n in noises]

def draw(ax, pos, sp, title):
    ax.scatter(pos[sp > 0, 0], pos[sp > 0, 1], s=7, c="#d00000")
    ax.scatter(pos[sp < 0, 0], pos[sp < 0, 1], s=7, c="#1d6fb8")
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([]); ax.set_title(title, fontsize=10.5)

fig = plt.figure(figsize=(14.5, 8.4), facecolor="white")
draw(fig.add_subplot(2, 2, 1), *snaps[0], "t=0: a mixed salt-and-pepper crowd")
draw(fig.add_subplot(2, 2, 2), *snaps[-1], f"later: clean LANES (order {r['order'][-1]:.2f}) — red=+x, blue=-x")

axT = fig.add_subplot(2, 2, 3)
axT.plot(r["order"], color="#2a9d8f", lw=1.8, label="counter-flow -> lanes")
axT.plot(ctrl["order"], color="#999", lw=1.5, ls="--", label="no drive -> stays mixed")
axT.set_xlabel("time step"); axT.set_ylabel("lane order parameter")
axT.set_title("Lanes self-organise over time\n(drive on); mixed without drive", fontsize=10.5)
axT.set_ylim(0, 1); axT.legend(fontsize=8.5); axT.grid(alpha=0.3)

axN = fig.add_subplot(2, 2, 4)
axN.plot(noises, ord_noise, "o-", color="#6a040f")
axN.set_xlabel("noise (temperature)"); axN.set_ylabel("lane order parameter")
axN.set_title("Noise melts the lanes:\norder collapses above a critical noise", fontsize=10.5)
axN.set_ylim(0, 1); axN.grid(alpha=0.3)

fig.suptitle("R128 · Lane formation — two crowds driven through each other spontaneously segregate into "
             "lanes (non-equilibrium self-organisation; Helbing pedestrians / driven colloids)",
             fontsize=11.5, y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "lanes.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)

# GIF: lanes emerging
frames = []
for pos, sp in snaps[::2]:
    f = plt.figure(figsize=(4.0, 4.0), facecolor="white")
    a = f.add_subplot(111)
    a.scatter(pos[sp > 0, 0], pos[sp > 0, 1], s=6, c="#d00000")
    a.scatter(pos[sp < 0, 0], pos[sp < 0, 1], s=6, c="#1d6fb8")
    a.set_aspect("equal"); a.set_xticks([]); a.set_yticks([]); a.set_title("counter-flow lanes", fontsize=9)
    f.tight_layout(); f.canvas.draw()
    frames.append(np.asarray(f.canvas.buffer_rgba())[:, :, :3].copy())
    plt.close(f)
gif = os.path.join(OUT, "lanes.gif")
imageio.mimsave(gif, frames, duration=0.07, loop=0)
print("saved", gif, len(frames), "frames")
