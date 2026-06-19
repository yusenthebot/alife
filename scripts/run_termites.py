"""R133 figure — termite stigmergy: material self-organises into mounds with no blueprint."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio.v2 as imageio
from dataclasses import replace

from alife.termites import TermiteConfig, run, clustering, clustering_curve

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r133_termites")
os.makedirs(OUT, exist_ok=True)

cfg = TermiteConfig(L=140, n=3500, steps=5000, k=6.0, seed=1)
on = run(cfg, record_every=60)
off = run(replace(cfg, k=0.0))
ks, cc = clustering_curve(np.linspace(0, 9, 10), replace(cfg, L=110, n=2200, steps=2800, seed=2))
print(f"stigmergy clustering={clustering(on['M']):.2f}  random={clustering(off['M']):.2f}")

fig = plt.figure(figsize=(14.5, 8.4), facecolor="white")

ax1 = fig.add_subplot(2, 2, 1)
ax1.imshow(on["M"], cmap="magma"); ax1.axis("off")
ax1.scatter(on["pos"][:, 0], on["pos"][:, 1], s=1, c="#39d", alpha=0.25)
ax1.set_title(f"Stigmergy ON (k=6): material clumps into mounds\n(termites in blue; clustering {clustering(on['M']):.1f})",
              fontsize=10.5)

ax2 = fig.add_subplot(2, 2, 2)
ax2.imshow(off["M"], cmap="magma"); ax2.axis("off")
ax2.set_title(f"Stigmergy OFF (random deposition): flat floor\n(clustering {clustering(off['M']):.2f} ~ 1)", fontsize=10.5)

ax3 = fig.add_subplot(2, 2, 3)
ax3.plot(ks, cc, "o-", color="#9c4a00")
ax3.axhline(1.0, color="#999", ls=":", lw=1, label="flat (random)")
ax3.set_xlabel("stigmergy strength  k"); ax3.set_ylabel("material clustering (var/mean)")
ax3.set_title("Work begets work: clustering switches on\nas the feedback strength rises", fontsize=10.5)
ax3.legend(fontsize=8.5); ax3.grid(alpha=0.3)

ax4 = fig.add_subplot(2, 2, 4)
ax4.imshow(on["P"], cmap="viridis"); ax4.axis("off")
ax4.set_title("Cement pheromone field\n(diffuses from the mounds, recruits more building)", fontsize=10.5)

fig.suptitle("R133 · Termite construction (stigmergy) — random-walking builders deposit cement that "
             "recruits more cement, so the structure self-organises into mounds with NO blueprint (Grasse 1959)",
             fontsize=11, y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "termites.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)

# GIF: mounds emerging from the flat floor
frames = []
vmax = on["M"].max()
for M in on["snaps"]:
    f = plt.figure(figsize=(3.8, 3.8), facecolor="white")
    a = f.add_subplot(111); a.imshow(M, cmap="magma", vmin=0, vmax=vmax)
    a.set_xticks([]); a.set_yticks([]); a.set_title("termites building (stigmergy)", fontsize=9)
    f.tight_layout(); f.canvas.draw()
    frames.append(np.asarray(f.canvas.buffer_rgba())[:, :, :3].copy())
    plt.close(f)
gif = os.path.join(OUT, "termites.gif")
imageio.mimsave(gif, frames, duration=0.08, loop=0)
print("saved", gif, len(frames), "frames")
