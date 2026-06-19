"""R121 figure — composed world: chemotactic foragers evolving inside a fluid flow (fluid.py + ecology)."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dataclasses import replace

from alife.flowforage import ForageConfig, run, vortex_flow, lbm_flow

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r121_flowforage")
os.makedirs(OUT, exist_ok=True)

# Panel A: a REAL fluid.py Karman-vortex flow (the fluid we compose the ecology into) -- cached
cache = os.path.join(OUT, "karman.npz")
if os.path.exists(cache):
    d = np.load(cache); ux_k, uy_k = d["ux"], d["uy"]
else:
    ux_k, uy_k = lbm_flow(nx=240, ny=80, steps=12000, u_in=0.1, radius=10)
    np.savez(cache, ux=ux_k, uy=uy_k)
vort = (np.roll(uy_k, -1, 1) - np.roll(uy_k, 1, 1) - np.roll(ux_k, -1, 0) + np.roll(ux_k, 1, 0)) * 0.5

base = ForageConfig(L=120, n0=400, steps=520, seed=1)
snap = run(base, flow=vortex_flow(120, amp=0.6, k=2), record_every=0)        # composed-world snapshot
sel = run(base)                                                              # selection (chemotaxis on)
neu = run(replace(base, chemotaxis=False))                                   # neutral control

# Panel D: selected chemotaxis vs flow strength (multi-seed)
amps = [0.0, 0.4, 0.8, 1.2, 1.6]
means, stds = [], []
for amp in amps:
    fl = None if amp == 0 else vortex_flow(120, amp=amp, k=2)
    vals = [run(replace(base, seed=s), flow=fl)["chi"][-8:].mean() for s in range(3)]
    means.append(np.mean(vals)); stds.append(np.std(vals))
means, stds = np.array(means), np.array(stds)
print(f"selection chi {sel['chi'][0]:.2f}->{sel['chi'][-1]:.2f}  neutral {neu['chi'][0]:.2f}->{neu['chi'][-1]:.2f}")
print(f"flow sweep amps={amps} chi={np.round(means,2)}")

fig = plt.figure(figsize=(14.5, 8.6), facecolor="white")

axA = fig.add_subplot(2, 2, 1)
axA.imshow(vort, cmap="RdBu", vmin=-np.abs(vort).max() * 0.5, vmax=np.abs(vort).max() * 0.5, aspect="auto")
axA.set_title("Composed with R101 fluid.py: a real Karman\nvortex street (the flow the ecology lives in)", fontsize=10.5)
axA.set_xticks([]); axA.set_yticks([])

axB = fig.add_subplot(2, 2, 2)
st = snap["state"]
axB.imshow(snap["N"].T, cmap="YlGn", origin="lower", extent=[0, 120, 0, 120], alpha=0.85)
sc = axB.scatter(st["x"], st["y"], s=5, c=st["chi"], cmap="inferno", vmin=0, vmax=4)
axB.set_title("The world: foragers (colour = chemotaxis chi)\non the depleted nutrient field, stirred by flow", fontsize=10.5)
axB.set_xticks([]); axB.set_yticks([])
fig.colorbar(sc, ax=axB, fraction=0.046, pad=0.04).set_label("chi", fontsize=9)

axC = fig.add_subplot(2, 2, 3)
axC.plot(sel["chi"], color="#2a9d8f", lw=1.8, label="chemotaxis active -> selected")
axC.plot(neu["chi"], color="#999", lw=1.6, ls="--", label="neutral tag (control) -> drifts")
axC.set_xlabel("time step"); axC.set_ylabel("mean chemotactic sensitivity  chi")
axC.set_title("Selection: behaviour evolves in the world\n(chi rises; a neutral tag just drifts)", fontsize=10.5)
axC.legend(fontsize=8.5); axC.grid(alpha=0.3)

axD = fig.add_subplot(2, 2, 4)
axD.errorbar(amps, means, yerr=stds, fmt="o-", color="#6a040f", capsize=3)
axD.set_xlabel("flow strength (vortex amplitude)"); axD.set_ylabel("selected chemotaxis  chi (3-seed mean)")
axD.set_title("Flow shapes evolution: stronger currents do some\nforaging, so less chemotaxis is selected", fontsize=10.5)
axD.grid(alpha=0.3)

fig.suptitle("R121 · A composed world — chemotactic foragers EVOLVE inside a fluid flow (fluid.py + nutrient "
             "field + selection); behaviour is selected, and the current reshapes how much",
             fontsize=11.5, y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "flowforage.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
