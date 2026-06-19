"""R95 figure — bacterial chemotaxis: run-and-tumble climbs a gradient by temporal sensing."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.chemotaxis import simulate, chemotactic_index, gaussian_field, ChemoConfig

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r95_chemotaxis")
os.makedirs(OUT, exist_ok=True)
W = 100.0
conc, (cx, cy) = gaussian_field(W, 20.0)
gx, gy = np.meshgrid(np.linspace(0, W, 200), np.linspace(0, W, 200))
field = conc(np.c_[gx.ravel(), gy.ravel()]).reshape(gx.shape)

chemo = simulate(ChemoConfig(alpha=10.0), n=500, seed=1, record_every=5)
ctrl = simulate(ChemoConfig(alpha=0.0), n=500, seed=1, record_every=5)
alphas = [0, 1, 2, 4, 8, 16]
dose = [simulate(ChemoConfig(alpha=a), n=400, seed=3)["mean_c"][-1] for a in alphas]

fig = plt.figure(figsize=(15, 8.6), facecolor="white")

def field_scatter(ax, pos, title):
    ax.imshow(field, extent=[0, W, 0, W], origin="lower", cmap="bone", alpha=0.9)
    ax.scatter(pos[:, 0], pos[:, 1], s=5, c="#ffb703", alpha=0.7)
    ax.plot(cx, cy, "r*", ms=12)
    ax.set_title(title, fontsize=10.5); ax.set_xticks([]); ax.set_yticks([])

field_scatter(fig.add_subplot(2, 3, 1), chemo["pos"],
              f"Chemotaxis (α=10): cells accumulate at source\n{chemotactic_index(chemo):.0%} within one field-width")
field_scatter(fig.add_subplot(2, 3, 2), ctrl["pos"],
              f"Control (α=0): no temporal sensing → diffuse\n{chemotactic_index(ctrl):.0%} within one field-width")

axC = fig.add_subplot(2, 3, 3)
axC.plot(chemo["mean_c"], color="#fb8500", label="chemotaxis α=10")
axC.plot(ctrl["mean_c"], color="#8d99ae", label="control α=0")
axC.set_xlabel("time step"); axC.set_ylabel("mean concentration at cells")
axC.set_title("Cells climb the gradient over time", fontsize=10.5)
axC.legend(fontsize=9); axC.grid(alpha=0.3)

axD = fig.add_subplot(2, 3, 4)
axD.plot(alphas, dose, "o-", color="#d62828")
axD.set_xlabel("temporal modulation strength  α"); axD.set_ylabel("final mean concentration")
axD.set_title("Dose-response: more memory → better climbing", fontsize=10.5)
axD.grid(alpha=0.3)

# E. example run-and-tumble trajectories (track a few agents across snapshots)
axE = fig.add_subplot(2, 3, (5, 6))
axE.imshow(field, extent=[0, W, 0, W], origin="lower", cmap="bone", alpha=0.85)
ts = sorted(chemo["snaps"].keys())
paths = np.stack([chemo["snaps"][t] for t in ts])          # (T, n, 2)
rng = np.random.default_rng(0)
for i in rng.choice(500, 6, replace=False):
    axE.plot(paths[:, i, 0], paths[:, i, 1], lw=1.0, alpha=0.9)
    axE.plot(paths[0, i, 0], paths[0, i, 1], "o", ms=4, color="white")
axE.plot(cx, cy, "r*", ms=14)
axE.set_title("Run-and-tumble paths: straight runs + reorienting tumbles, biased uphill", fontsize=10.5)
axE.set_xticks([]); axE.set_yticks([])

fig.suptitle("R95 · Bacterial chemotaxis — climbing a gradient with no sense of direction (run-and-tumble)",
             fontsize=13, y=1.0)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "chemotaxis.png")
fig.savefig(path, dpi=110, bbox_inches="tight")
print("saved", path)
print(f"chemo near={chemotactic_index(chemo):.2f} conc_final={chemo['mean_c'][-1]:.3f}  "
      f"ctrl near={chemotactic_index(ctrl):.2f} conc_final={ctrl['mean_c'][-1]:.3f}  dose={[round(d,3) for d in dose]}")
