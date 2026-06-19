"""R86 figure — Nagel-Schreckenberg traffic: phantom jams + the fundamental diagram."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.traffic import simulate, fundamental_diagram, jam_fraction

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r86_traffic")
os.makedirs(OUT, exist_ok=True)

ROAD, VMAX, P = 400, 5, 0.3
WIN = 160          # spacetime window (steps shown)

free = simulate(ROAD, int(0.07 * ROAD), VMAX, P, steps=WIN + 200, seed=7)
jam = simulate(ROAD, int(0.28 * ROAD), VMAX, P, steps=WIN + 200, seed=7)
d, J = fundamental_diagram(ROAD, VMAX, P, steps=300, seed=3, reps=6)
kc = int(np.argmax(J))

fig = plt.figure(figsize=(15, 5.2), facecolor="white")

# velocity colormap: red=stopped, green=free-flowing; empty road dark
cmap = plt.get_cmap("RdYlGn")
cmap.set_under("#101015")

def spacetime(ax, res, title):
    sp = res["space"][-WIN:, :].astype(float)
    sp[sp < 0] = -1                              # empties -> under-color
    ax.imshow(sp, aspect="auto", cmap=cmap, vmin=0, vmax=VMAX, origin="lower",
              interpolation="nearest")
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("position on ring  →")
    ax.set_ylabel("time  ↓ (later)")
    ax.invert_yaxis()

ax1 = fig.add_subplot(1, 3, 1)
spacetime(ax1, free, f"Free flow  ρ=0.07\n<v>={free['mean_flow']:.2f}  jam-frac={jam_fraction(free['space']):.2f}")
ax2 = fig.add_subplot(1, 3, 2)
spacetime(ax2, jam, f"Congested  ρ=0.28  — phantom jams\n<v>={jam['mean_flow']:.2f}  jam-frac={jam_fraction(jam['space']):.2f}")
ax2.text(0.5, 0.06, "dark stripes = jams,\npropagating BACKWARD ↖", transform=ax2.transAxes,
         ha="center", color="white", fontsize=8.5,
         bbox=dict(boxstyle="round", fc="#222", ec="none", alpha=0.7))

ax3 = fig.add_subplot(1, 3, 3)
ax3.plot(d, J, "o-", color="#1f77b4", ms=4)
ax3.axvline(d[kc], color="crimson", ls="--", lw=1)
ax3.annotate(f"ρ_c≈{d[kc]:.2f}\nmax throughput", xy=(d[kc], J[kc]),
             xytext=(d[kc] + 0.18, J[kc] * 0.92), fontsize=9, color="crimson",
             arrowprops=dict(arrowstyle="->", color="crimson"))
ax3.text(0.06, 0.04, "free flow", color="#2a7", fontsize=9)
ax3.text(0.6, 0.04, "congested", color="#c33", fontsize=9)
ax3.set_xlabel("density  ρ  (cars / cell)")
ax3.set_ylabel("throughput  J = ρ·<v>")
ax3.set_title("Fundamental diagram of traffic\n(emergent jamming transition)", fontsize=11)
ax3.grid(alpha=0.3)

fig.suptitle("R86 · Nagel–Schreckenberg traffic — jams emerge from local rules, no cause, no bottleneck",
             fontsize=12.5, y=1.0)
fig.tight_layout(rect=[0, 0, 1, 0.96])
path = os.path.join(OUT, "traffic.png")
fig.savefig(path, dpi=110, bbox_inches="tight")
print("saved", path)
print(f"free <v>={free['mean_flow']:.3f}  jam <v>={jam['mean_flow']:.3f}  rho_c={d[kc]:.2f}  Jmax={J[kc]:.3f}")
