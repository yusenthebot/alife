"""R119 figure — Reiter snow-crystal CA: six-fold snowflakes and the humidity->morphology (Nakaya) sweep."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dataclasses import replace

from alife.snowflake import SnowflakeConfig, grow, frozen_mask, compactness, crystal_mass, to_cartesian

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r119_snowflake")
os.makedirs(OUT, exist_ok=True)

base = SnowflakeConfig(L=241, alpha=1.0)

def show(ax, cfg, title):
    s = grow(cfg)
    m = frozen_mask(s)
    X, Y = to_cartesian(cfg.L)
    ax.scatter(X[m], Y[m], s=2.0, c=s[m], cmap="Blues_r", vmin=1.0, vmax=s[m].max())
    R = max(np.abs(X[m]).max(), np.abs(Y[m]).max()) * 1.05
    ax.set_xlim(-R, R); ax.set_ylim(-R, R); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([]); ax.set_facecolor("#0b1726")
    ax.set_title(title, fontsize=10)
    return s

fig = plt.figure(figsize=(15, 9), facecolor="white")

gallery = [
    (replace(base, beta=0.40, gamma=0.001, steps=520), "low humidity (beta=0.40):\ncompact star"),
    (replace(base, beta=0.50, gamma=0.001, steps=430), "beta=0.50: classic dendrite"),
    (replace(base, beta=0.60, gamma=0.0005, steps=430), "high humidity (beta=0.60):\nbroad branches"),
    (replace(base, beta=0.45, gamma=0.01, steps=430), "more deposition (gamma=0.01):\nfeathery side-branches"),
    (replace(base, beta=0.55, gamma=0.002, steps=430), "beta=0.55: sectored plate"),
]
for k, (cfg, title) in enumerate(gallery):
    ax = fig.add_subplot(2, 3, k + 1 if k < 3 else k + 2)   # leave slot 4 (index 3) for the curve
    show(ax, cfg, title)

# morphology curve: compactness vs humidity beta (the Nakaya knob)
axC = fig.add_subplot(2, 3, 4)
betas = np.array([0.34, 0.40, 0.46, 0.52, 0.58])       # boundary-safe range (crystal stays inside L)
comp = np.array([compactness(grow(replace(base, beta=float(b), gamma=0.001, steps=360))) for b in betas])
axC.plot(betas, comp, "o-", color="#0077b6")
axC.set_xlabel("background humidity  beta"); axC.set_ylabel("compactness (fill of enclosing disc)")
axC.set_title("Nakaya knob: raising humidity drives\ncompact star -> open dendrite", fontsize=10)
axC.grid(alpha=0.3)
print("betas", list(betas), "compactness", list(np.round(comp, 3)))

fig.suptitle("R119 · Snowflake growth (Reiter's hexagonal CA) — diffusing vapour + tip instability grow "
             "exact six-fold crystals; one humidity knob sweeps plate -> dendrite (Nakaya 1954 / Reiter 2005)",
             fontsize=11.5, y=0.99)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "snowflake.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
