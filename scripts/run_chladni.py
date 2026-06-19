"""R129 figure — Chladni figures: sand self-assembles onto the nodal lines of a vibrating plate."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio.v2 as imageio

from alife.chladni import ChladniConfig, mode_field, assemble_sand, eigenfrequency, node_amplitude, _phi_at

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r129_chladni")
os.makedirs(OUT, exist_ok=True)

modes = [(2, 1, 1.0), (3, 2, -1.0), (4, 3, 1.0), (5, 2, -1.0), (4, 1, 1.0), (5, 4, -1.0)]
modes.sort(key=lambda t: eigenfrequency(t[0], t[1]))

fig, axs = plt.subplots(2, 3, figsize=(13, 8.6), facecolor="white")
for ax, (m, n, c) in zip(axs.ravel(), modes):
    cfg = ChladniConfig(m=m, n=n, c=c, ngrain=6000, steps=550, seed=1)
    r = assemble_sand(cfg)
    ax.imshow(np.abs(r["phi"]), cmap="Greys", vmin=0, vmax=1.6, extent=[0, 1, 0, 1], origin="lower", alpha=0.2)
    ax.scatter(r["pos"][:, 0], r["pos"][:, 1], s=1.4, c="#161616")
    ax.set_title(f"mode ({m},{n}), freq~{eigenfrequency(m, n):.2f}", fontsize=10)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect("equal")

fig.suptitle("R129 · Chladni figures — sand on a vibrating plate drifts off the antinodes and settles on "
             "the NODAL lines, drawing each standing-wave mode (higher pitch -> finer figure)",
             fontsize=11.5, y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "chladni.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)

# verify sand settled on nodes (vs random)
cfg = ChladniConfig(m=3, n=2, c=-1.0, ngrain=6000, steps=550, seed=1)
r = assemble_sand(cfg, record_every=11)
rng = np.random.default_rng(0)
rand = rng.uniform(0.02, 0.98, (6000, 2))
print(f"sand |phi|={node_amplitude(r['phi'], r['pos']):.3f}  vs random |phi|={np.abs(_phi_at(r['phi'], rand)).mean():.3f}")

# GIF: sand assembling into the (3,2) figure
frames = []
for pos in r["snaps"]:
    f = plt.figure(figsize=(3.8, 3.8), facecolor="white")
    a = f.add_subplot(111)
    a.imshow(np.abs(r["phi"]), cmap="Greys", vmin=0, vmax=1.6, extent=[0, 1, 0, 1], origin="lower", alpha=0.2)
    a.scatter(pos[:, 0], pos[:, 1], s=1.4, c="#161616")
    a.set_xticks([]); a.set_yticks([]); a.set_aspect("equal"); a.set_title("sand finding the nodes", fontsize=9)
    f.tight_layout(); f.canvas.draw()
    frames.append(np.asarray(f.canvas.buffer_rgba())[:, :, :3].copy())
    plt.close(f)
gif = os.path.join(OUT, "chladni.gif")
imageio.mimsave(gif, frames, duration=0.08, loop=0)
print("saved", gif, len(frames), "frames")
