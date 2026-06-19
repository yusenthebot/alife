"""R125 figure — Cahn-Hilliard spinodal decomposition: watch a mixture unmix and coarsen (L~t^1/3)."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio.v2 as imageio

from alife.cahnhilliard import CHConfig, run, coarsening_exponent

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r125_cahnhilliard")
os.makedirs(OUT, exist_ok=True)

cfg = CHConfig(N=256, eps=1.0, steps=8000, seed=1)
r = run(cfg, record_every=40)
t, L, snaps = r["t"], r["L"], r["snaps"]
n = coarsening_exponent(t, L, t_min=400)
print(f"coarsening exponent n={n:.3f} (LSW 1/3); mean c={r['c'].mean():.4f}; L {L[0]:.1f}->{L[-1]:.1f}")

# pick 4 snapshots spread in log-time for the coarsening sequence
pick = [np.argmin(np.abs(t - tt)) for tt in np.geomspace(t[2], t[-1], 4)]

fig = plt.figure(figsize=(15, 8.2), facecolor="white")
gs = fig.add_gridspec(2, 4, height_ratios=[1.25, 1.0], hspace=0.28, wspace=0.12)
for j, idx in enumerate(pick):
    ax = fig.add_subplot(gs[0, j])
    ax.imshow(snaps[idx], cmap="RdBu", vmin=-1, vmax=1, interpolation="nearest")
    ax.set_title(f"t = {t[idx]}   (domain size {L[idx]:.0f})", fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])

axL = fig.add_subplot(gs[1, 1:3])
axL.loglog(t, L, "o", color="#1d6fb8", ms=3, label="measured domain size L(t)")
tt = np.array([t[3], t[-1]])
axL.loglog(tt, L[3] * (tt / t[3]) ** (1 / 3), "k--", lw=1.4, label="t^(1/3) (Lifshitz-Slyozov)")
axL.set_xlabel("time"); axL.set_ylabel("domain size L")
axL.set_title(f"Domains coarsen as a power law:\nfitted exponent n = {n:.2f}  (theory 1/3)", fontsize=10.5)
axL.legend(fontsize=9); axL.grid(alpha=0.3, which="both")

fig.suptitle("R125 · Cahn-Hilliard spinodal decomposition — a quenched mixture spontaneously unmixes into "
             "two phases whose domains coarsen as L(t) ~ t^(1/3) (conserved order parameter; Model B)",
             fontsize=11.5, y=0.97)
fig.tight_layout(rect=[0, 0, 1, 0.94])
path = os.path.join(OUT, "cahnhilliard.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)

# GIF: the full unmix-and-coarsen animation
frames = []
for c in snaps[::3]:
    f = plt.figure(figsize=(3.6, 3.6), facecolor="white")
    a = f.add_subplot(111)
    a.imshow(c, cmap="RdBu", vmin=-1, vmax=1, interpolation="nearest")
    a.set_xticks([]); a.set_yticks([]); a.set_title("spinodal decomposition", fontsize=9)
    f.tight_layout(); f.canvas.draw()
    frames.append(np.asarray(f.canvas.buffer_rgba())[:, :, :3].copy())
    plt.close(f)
gif = os.path.join(OUT, "cahnhilliard.gif")
imageio.mimsave(gif, frames, duration=0.06, loop=0)
print("saved", gif, len(frames), "frames")
