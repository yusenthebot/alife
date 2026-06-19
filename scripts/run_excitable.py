"""R88 figure — excitable media: a rotating spiral, wave annihilation, and re-entry vs a dying wave."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.excitable import (run, planar_wave_ic, two_wave_ic, spiral_ic,
                             gh_step, dominant_period)

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r88_excitable")
os.makedirs(OUT, exist_ok=True)

K = 10
H = W = 220

# --- spiral: capture snapshots at chosen times ---
s = spiral_ic(H, W, K)
snaps_t = [40, 110, 180, 250]
snaps = {}
spiral_act = [int((s == 1).sum())]
for t in range(1, max(snaps_t) + 1):
    s = gh_step(s, K)
    spiral_act.append(int((s == 1).sum()))
    if t in snaps_t:
        snaps[t] = s.copy()

# --- two-wave collision: before / after ---
tw = two_wave_ic(H, W, K, gap=45)
before, after = None, None
for t in range(1, 90):
    tw = gh_step(tw, K)
    if t == 38:
        before = tw.copy()
    if t == 70:
        after = tw.copy()

# --- activity: spiral (sustained) vs uncut planar wave (dies) ---
_, act_spiral = run(spiral_ic(H, W, K), K, steps=500, record_every=500)
_, act_planar = run(planar_wave_ic(H, W, K, col=8), K, steps=500, record_every=500)
period = dominant_period(act_spiral, burn=120)


def show(ax, state, title):
    disp = np.ma.masked_where(state == 0, state.astype(float))
    cmap = plt.get_cmap("twilight").copy()
    cmap.set_bad("#0a0a14")
    ax.imshow(disp, cmap=cmap, vmin=1, vmax=K - 1, interpolation="nearest")
    ax.set_title(title, fontsize=10); ax.axis("off")


fig = plt.figure(figsize=(15, 8), facecolor="white")

for i, t in enumerate(snaps_t):
    show(fig.add_subplot(2, 4, i + 1), snaps[t], f"spiral  t={t}")

show(fig.add_subplot(2, 4, 5), before, "two waves\nbefore collision")
show(fig.add_subplot(2, 4, 6), after, "after collision\nANNIHILATED (empty)")

axA = fig.add_subplot(2, 4, (7, 8))
axA.plot(act_spiral, color="#c1121f", lw=1.3, label=f"broken wave → spiral (sustained, period≈{period:.0f})")
axA.plot(act_planar, color="#457b9d", lw=1.3, label="uncut planar wave → dies out")
axA.set_xlabel("time step"); axA.set_ylabel("excited cells (activity)")
axA.set_title("Re-entry: only the broken wavefront sustains itself", fontsize=10.5)
axA.legend(fontsize=8.5, loc="center right"); axA.grid(alpha=0.3)

fig.suptitle("R88 · Excitable media — self-sustaining spiral waves & re-entry (Greenberg–Hastings)",
             fontsize=13, y=0.99)
fig.tight_layout(rect=[0, 0, 1, 0.96])
path = os.path.join(OUT, "excitable.png")
fig.savefig(path, dpi=110, bbox_inches="tight")
print("saved", path)
print(f"spiral sustained late-min={act_spiral[200:].min()}  planar end={act_planar[-1]}  period={period:.0f}")
