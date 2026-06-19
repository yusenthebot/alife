"""R102 figure — an undulatory swimmer self-propels through the lattice-Boltzmann fluid."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dataclasses import replace

from alife.swimmer import simulate, SwimConfig
from alife.fluid import _vorticity

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r102_swimmer")
os.makedirs(OUT, exist_ok=True)
cfg = SwimConfig(amp=6.0, freq=0.001, steps=6000, mass=800.0)

cache = os.path.join(OUT, "swim.npz")
swim = simulate(cfg, record_every=1000)
ctrl = simulate(replace(cfg, amp=0.0))

fig = plt.figure(figsize=(15, 7.6), facecolor="white")

# A. body shape snapshots (undulating + net translation)
axA = fig.add_subplot(2, 1, 1)
ts = sorted(swim["snaps"].keys())
cols = plt.get_cmap("viridis")(np.linspace(0.15, 0.9, len(ts)))
for c, t in zip(cols, ts):
    mask = swim["snaps"][t][0]
    ys, xs = np.where(mask.T)                                 # mask is (nx,ny); plot x horizontal
    axA.scatter(xs, ys, s=4, color=c, label=f"t={t}")
axA.set_title("Undulatory body over time (colour = time): the swimmer translates as it flexes", fontsize=11)
axA.set_xlabel("x"); axA.set_ylabel("y"); axA.legend(fontsize=7, ncol=7, loc="upper center")
axA.set_aspect("equal"); axA.set_xlim(0, cfg.nx); axA.set_ylim(0, cfg.ny)

# B. wake (vorticity) at the final snapshot
axB = fig.add_subplot(2, 2, 3)
_, ux, uy, xc = swim["snaps"][ts[-1]]
vort = _vorticity(ux, uy)
vlim = np.nanpercentile(np.abs(vort), 99.5)
axB.imshow(vort.T, origin="lower", cmap="RdBu_r", vmin=-vlim, vmax=vlim, aspect="equal")
axB.set_title("Wake: the tail throws fluid back (vorticity)", fontsize=10.5)
axB.set_xticks([]); axB.set_yticks([])

# C. centre-of-mass trajectory: swimmer vs rigid control
axC = fig.add_subplot(2, 2, 4)
axC.plot(swim["xc"] - swim["xc"][0], color="#1f77b4", label=f"undulating (net {swim['net_disp']:.1f})")
axC.plot(ctrl["xc"] - ctrl["xc"][0], color="#888", ls="--", label=f"rigid control A=0 (net {ctrl['net_disp']:.1f})")
axC.set_xlabel("time step"); axC.set_ylabel("centre-of-mass displacement")
axC.set_title("Self-propulsion: it swims only when it undulates", fontsize=10.5)
axC.legend(fontsize=9); axC.grid(alpha=0.3)

fig.suptitle("R102 · A swimmer in a real fluid — self-propulsion emerges from an undulatory gait (no prescribed speed)",
             fontsize=12.5, y=1.0)
fig.tight_layout(rect=[0, 0, 1, 0.96])
path = os.path.join(OUT, "swimmer.png")
fig.savefig(path, dpi=110, bbox_inches="tight")
print("saved", path)
print(f"undulating net_disp={swim['net_disp']:.2f}  control net_disp={ctrl['net_disp']:.2f}")
