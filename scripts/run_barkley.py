"""R131 figure — excitable media (Barkley): BZ-type spiral waves & pacemaker target rings."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio.v2 as imageio
from dataclasses import replace

from alife.barkley import BarkleyConfig, step, run_spiral, run_target, wave_speed, excited_fraction

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r131_barkley")
os.makedirs(OUT, exist_ok=True)

base = BarkleyConfig(N=240, steps=7000, seed=1)
sp = run_spiral(replace(base, steps=6000))
tg = run_target(replace(base, steps=6500), pace_period=360, record_every=60)
print(f"spiral activity={sp['activity']:.2f}  wave_speed={wave_speed(base):.2f}")

# excitability threshold curve: does a seed of amplitude A launch a wave?
amps = np.linspace(0.0, 0.12, 13)
def launches(amp):
    N = 110; u = np.zeros((N, N)); v = np.zeros((N, N))
    u[N // 2 - 3:N // 2 + 3, N // 2 - 3:N // 2 + 3] = amp
    cfg = replace(base, N=N)
    for _ in range(900):
        u, v = step(u, v, cfg)
    return excited_fraction(u)
exc = [launches(a) for a in amps]

# wave-speed front-position vs time (1D)
cfg = base
L = 400; u1 = np.zeros(L); v1 = np.zeros(L); u1[:4] = 1.0
from alife.barkley import _lap1d
pos, ts = [], []
for t in range(1400):
    u1 = u1 + cfg.dt * (cfg.Du * _lap1d(u1) + (1 / cfg.eps) * u1 * (1 - u1) * (u1 - (v1 + cfg.b) / cfg.a))
    v1 = v1 + cfg.dt * (u1 - v1); np.clip(u1, 0, 1, out=u1)
    fr = np.where(u1 > 0.5)[0]
    if fr.size: pos.append(fr.max()); ts.append(t * cfg.dt)
pos, ts = np.array(pos), np.array(ts)

fig = plt.figure(figsize=(14.5, 8.4), facecolor="white")
ax1 = fig.add_subplot(2, 2, 1); ax1.imshow(sp["u"], cmap="inferno", vmin=0, vmax=1); ax1.axis("off")
ax1.set_title("SPIRAL waves (broken front -> re-entrant rotation)", fontsize=10.5)
ax2 = fig.add_subplot(2, 2, 2); ax2.imshow(tg["u"], cmap="inferno", vmin=0, vmax=1); ax2.axis("off")
ax2.set_title("TARGET waves (concentric rings from a pacemaker)", fontsize=10.5)

ax3 = fig.add_subplot(2, 2, 3)
ax3.plot(amps, exc, "o-", color="#d00000")
ax3.axvline(0.02 / 0.75, color="#3a0ca3", ls="--", lw=1.3, label="threshold (v+b)/a = b/a")
ax3.set_xlabel("initial kick amplitude"); ax3.set_ylabel("excited fraction after relaxation")
ax3.set_title("Excitability: a kick below threshold dies,\nabove it ignites a wave", fontsize=10.5)
ax3.legend(fontsize=8.5); ax3.grid(alpha=0.3)

ax4 = fig.add_subplot(2, 2, 4)
ax4.plot(ts, pos, ".", color="#1d6fb8", ms=3)
m = (pos > 10) & (pos < L - 10)
fit = np.polyfit(ts[m], pos[m], 1)
ax4.plot(ts[m], np.polyval(fit, ts[m]), "k--", lw=1.2, label=f"speed = {fit[0]:.2f} cells/time")
ax4.set_xlabel("time"); ax4.set_ylabel("wavefront position")
ax4.set_title("Constant wave speed\n(front advances linearly in a 1D cable)", fontsize=10.5)
ax4.legend(fontsize=8.5); ax4.grid(alpha=0.3)

fig.suptitle("R131 · Excitable media (Barkley model) — BZ-type chemical waves: rotating SPIRALS and "
             "concentric TARGET rings, with a firing threshold and a constant wave speed",
             fontsize=11.5, y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "barkley.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)

# GIF: target rings expanding
frames = []
for u in tg["snaps"]:
    f = plt.figure(figsize=(3.8, 3.8), facecolor="white")
    a = f.add_subplot(111); a.imshow(u, cmap="inferno", vmin=0, vmax=1)
    a.set_xticks([]); a.set_yticks([]); a.set_title("BZ target waves", fontsize=9)
    f.tight_layout(); f.canvas.draw()
    frames.append(np.asarray(f.canvas.buffer_rgba())[:, :, :3].copy())
    plt.close(f)
gif = os.path.join(OUT, "barkley.gif")
imageio.mimsave(gif, frames, duration=0.08, loop=0)
print("saved", gif, len(frames), "frames")
