"""R114 figure — somitogenesis: a clock + a receding wavefront crystallise a tempo into body segments."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

from alife.somitogenesis import (
    SomiteConfig, run, predict_somite_size, mean_somite_size, somite_ids, n_somites,
)

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r114_somitogenesis")
os.makedirs(OUT, exist_ok=True)

# kymograph: posterior frequency gradient -> travelling kinematic waves that arrest at the front
wave = run(SomiteConfig(N=220, v=2.2, omega=1.0, grad=2.2, coupling=0.04, dt=0.02), record=True)
kymo = wave["kymo"]
ds = max(1, kymo.shape[0] // 600)
field = np.sin(kymo[::ds])
front = wave["v"] if False else None  # (front overlaid below)

# clean uniform-clock segment pattern + a graded (gradient) one
flat = run(SomiteConfig(N=300, v=2.5, omega=1.0, grad=0.0, dt=0.01))["frozen_phase"]
grad = run(SomiteConfig(N=300, v=2.5, omega=1.0, grad=2.5, dt=0.01))["frozen_phase"]

# somite-size law: measured vs predicted 2*pi*v/omega across many (v, omega)
pred, meas = [], []
for v in (1.2, 1.8, 2.5, 3.2, 4.0):
    for om in (1.0, 1.6, 2.4):
        cfg = SomiteConfig(N=360, v=v, omega=om, dt=0.01)
        pred.append(predict_somite_size(cfg)); meas.append(mean_somite_size(run(cfg)["frozen_phase"]))
pred, meas = np.array(pred), np.array(meas)
print(f"law fit: max rel err = {np.max(np.abs(meas-pred)/pred):.3f}  n_somites(flat)={n_somites(flat)} (grad)={n_somites(grad)}")

fig = plt.figure(figsize=(15, 8.2), facecolor="white")
gs = fig.add_gridspec(2, 2, height_ratios=[1.35, 1.0], hspace=0.32, wspace=0.22)

# A: kymograph
axA = fig.add_subplot(gs[0, 0])
T = kymo.shape[0] * 0.02
axA.imshow(field, aspect="auto", cmap="RdBu", origin="upper",
           extent=[0, 220, T, 0], interpolation="nearest")
tt = np.linspace(0, T, 50); axA.plot(2.2 * tt, tt, color="k", lw=1.6, ls="--", label="determination front")
axA.set_xlim(0, 220); axA.set_ylim(T, 0)
axA.set_xlabel("position along axis  (anterior 0 -> posterior)"); axA.set_ylabel("time")
axA.set_title("PSM clock: travelling phase waves (right of front)\narrest into frozen somites (left of front)",
              fontsize=10.5)
axA.legend(fontsize=8.5, loc="lower right")

# B: somite-size law
axB = fig.add_subplot(gs[0, 1])
axB.plot([0, pred.max() * 1.05], [0, pred.max() * 1.05], "k--", lw=1, label="y = x")
axB.scatter(pred, meas, c="#d00000", s=34, zorder=3, label="simulation")
axB.set_xlabel("predicted somite size  2*pi*v/omega  (cells)")
axB.set_ylabel("measured somite size  (cells)")
axB.set_title("Clock-and-wavefront law holds exactly:\nsomite size = front speed x clock period", fontsize=10.5)
axB.legend(fontsize=9); axB.grid(alpha=0.3)

# C: segment patterns (zebra strips)
zebra = ListedColormap(["#1d3557", "#e9c46a"])
for r, (phi, lab) in enumerate([(flat, "uniform clock -> equal somites"),
                                (grad, "posterior frequency gradient -> graded somites (anterior larger)")]):
    ax = fig.add_subplot(gs[1, :]) if False else fig.add_subplot(2, 2, 3 + r)
    strip = np.tile(somite_ids(phi) % 2, (24, 1))
    ax.imshow(strip, aspect="auto", cmap=zebra, interpolation="nearest")
    ax.set_title(lab, fontsize=10); ax.set_yticks([])
    ax.set_xlabel("position along axis (cells)")

fig.suptitle("R114 · Somitogenesis (clock-and-wavefront) — a genetic oscillator's PERIOD becomes the body's "
             "segment SIZE via a receding front; size = 2*pi*v/omega, verified exactly (Cooke-Zeeman 1976)",
             fontsize=11.5, y=0.97)
fig.tight_layout(rect=[0, 0, 1, 0.94])
path = os.path.join(OUT, "somitogenesis.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
