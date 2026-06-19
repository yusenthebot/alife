"""R132 figure — Wolf-Sheep-Grass: a 3-level food chain breathing in boom-bust cycles."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio.v2 as imageio

from alife.wolfsheep import WolfSheepConfig, run, predator_lag

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r132_wolfsheep")
os.makedirs(OUT, exist_ok=True)

cfg = WolfSheepConfig(L=45, steps=4500, seed=2)
r = run(cfg, record_every=15)
S, W, G, snaps = r["sheep"], r["wolves"], r["grass"], r["snaps"]
lag = predator_lag(S, W)
print(f"coexist len={len(S)} sheep[{S[500:].min()},{S[500:].max()}] wolves[{W[500:].min()},{W[500:].max()}] lag={lag}")


def draw_world(ax, grass, sheep, wolves, title):
    ax.imshow(grass.T, cmap="Greens", vmin=-0.3, vmax=1.3, origin="lower", extent=[0, cfg.L, 0, cfg.L])
    if len(sheep):
        ax.scatter(sheep[:, 0] + 0.5, sheep[:, 1] + 0.5, s=14, c="#f8f8f8", edgecolors="#444", linewidths=0.3)
    if len(wolves):
        ax.scatter(wolves[:, 0] + 0.5, wolves[:, 1] + 0.5, s=20, c="#d00000")
    ax.set_xlim(0, cfg.L); ax.set_ylim(0, cfg.L); ax.set_xticks([]); ax.set_yticks([]); ax.set_title(title, fontsize=10.5)

fig = plt.figure(figsize=(14.5, 8.4), facecolor="white")
draw_world(fig.add_subplot(2, 2, 1), *snaps[len(snaps) // 2], "The world: grass (green), sheep (white), wolves (red)")

axP = fig.add_subplot(2, 2, 2)
axP.plot(S, color="#2a9d8f", lw=1.2, label="sheep")
axP.plot(W, color="#d00000", lw=1.2, label="wolves")
axP.plot(G / G.max() * S.max(), color="#7cb342", lw=0.9, alpha=0.6, label="grass (scaled)")
axP.set_xlabel("time step"); axP.set_ylabel("population")
axP.set_title("Boom-bust cycles: wolves rise after sheep,\nsheep crash, grass recovers", fontsize=10.5)
axP.legend(fontsize=8.5); axP.grid(alpha=0.3)

axL = fig.add_subplot(2, 2, 3)
axL.plot(S[500:], W[500:], "-", color="#6a040f", lw=0.6, alpha=0.8)
axL.set_xlabel("sheep"); axL.set_ylabel("wolves")
axL.set_title("Predator-prey phase loop\n(orbits, not a fixed point)", fontsize=10.5)
axL.grid(alpha=0.3)

axC = fig.add_subplot(2, 2, 4)
s = S[500:] - S[500:].mean(); w = W[500:] - W[500:].mean()
xc = np.correlate(w, s, "full"); lags = np.arange(-s.size + 1, s.size)
near = np.abs(lags) <= 200
axC.plot(lags[near], xc[near] / np.abs(xc[near]).max(), color="#3a0ca3")
axC.axvline(lag, color="#d00000", ls="--", lw=1.3, label=f"peak lag = +{lag} (wolves follow sheep)")
axC.axvline(0, color="#999", lw=0.8)
axC.set_xlabel("lag (wolves relative to sheep)"); axC.set_ylabel("cross-correlation")
axC.set_title("Predator LAGS prey (positive lag)", fontsize=10.5)
axC.legend(fontsize=8.5); axC.grid(alpha=0.3)

fig.suptitle("R132 · Wolf-Sheep-Grass — a 3-level agent food chain: grass->sheep->wolves fall into "
             "predator-prey boom-bust cycles (the predator lags the prey); the simplest world that looks ALIVE",
             fontsize=11, y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "wolfsheep.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)

# GIF: the world living over time
frames = []
for grass, sheep, wolves in snaps[::2]:
    f = plt.figure(figsize=(4.0, 4.0), facecolor="white")
    a = f.add_subplot(111)
    draw_world(a, grass, sheep, wolves, "grass / sheep / wolves")
    f.tight_layout(); f.canvas.draw()
    frames.append(np.asarray(f.canvas.buffer_rgba())[:, :, :3].copy())
    plt.close(f)
gif = os.path.join(OUT, "wolfsheep.gif")
imageio.mimsave(gif, frames, duration=0.08, loop=0)
print("saved", gif, len(frames), "frames")
