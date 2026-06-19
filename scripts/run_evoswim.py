"""R103 figure — evolving a swimming stroke: a GA discovers a fast gait in a real fluid."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.evoswim import evolve, random_baseline, gait_speed, _stabilize
from alife.swimmer import simulate, SwimConfig

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r103_evoswim")
os.makedirs(OUT, exist_ok=True)
STEPS = 1500

cache = os.path.join(OUT, "ga.npz")
if os.path.exists(cache):
    z = np.load(cache)
    best, bh, mh, base = z["best"], z["bh"], z["mh"], z["base"]
else:
    res = evolve(gens=10, pop=10, steps=STEPS, seed=0)
    base = random_baseline(n=14, steps=STEPS, seed=7)
    best, bh, mh = res["best_genome"], res["best_hist"], res["mean_hist"]
    np.savez(cache, best=best, bh=bh, mh=mh, base=base)

# run the evolved champion with snapshots for the trajectory panel
amp, freq, wl = _stabilize(best)
champ_cfg = SwimConfig(nx=200, ny=100, length=56, thick=3.0, amp=float(amp), wavelength=float(wl),
                       freq=float(freq), mass=800.0, steps=4000)
champ = simulate(champ_cfg, record_every=1000)

fig = plt.figure(figsize=(15, 4.8), facecolor="white")

axA = fig.add_subplot(1, 3, 1)
g = np.arange(len(bh))
axA.plot(g, bh * 1000, "o-", color="#1f77b4", label="best")
axA.plot(g, mh * 1000, "s-", color="#aaa", label="population mean")
axA.set_xlabel("generation"); axA.set_ylabel("swim speed (×10⁻³ / step)")
axA.set_title(f"Evolution climbs to a fast stroke\n({bh[0]*1000:.1f} → {bh[-1]*1000:.1f} ×10⁻³)", fontsize=10.5)
axA.legend(fontsize=9); axA.grid(alpha=0.3)

axB = fig.add_subplot(1, 3, 2)
axB.hist(base * 1000, bins=10, color="#bbb", label=f"random gaits (max {base.max()*1000:.1f})")
axB.axvline(bh[-1] * 1000, color="crimson", lw=2, label=f"evolved ({bh[-1]*1000:.1f})")
axB.set_xlabel("swim speed (×10⁻³ / step)"); axB.set_ylabel("count")
axB.set_title(f"Evolved gait beats random by {bh[-1]/max(base.max(),1e-9):.1f}×", fontsize=10.5)
axB.legend(fontsize=8.5)

axC = fig.add_subplot(1, 3, 3)
axC.plot(champ["xc"] - champ["xc"][0], color="#2a9d8f")
axC.set_xlabel("time step"); axC.set_ylabel("centre-of-mass displacement")
axC.set_title(f"Evolved swimmer: A={amp:.1f}, f={freq:.4f}, λ={wl:.0f}\n(net {champ['net_disp']:.1f})", fontsize=10.5)
axC.grid(alpha=0.3)

fig.suptitle("R103 · Evolving a swimming stroke — selection discovers fast locomotion in a real fluid",
             fontsize=12.5, y=1.02)
fig.tight_layout(rect=[0, 0, 1, 0.92])
path = os.path.join(OUT, "evoswim.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
print(f"evolved genome amp={amp:.2f} freq={freq:.4f} wl={wl:.1f}  best={bh[-1]*1000:.2f}e-3  "
      f"random max={base.max()*1000:.2f}e-3  ratio={bh[-1]/max(base.max(),1e-9):.1f}x")
