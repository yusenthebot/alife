"""R113 figure — 3D Ising: dimensionality (coordination number z) lifts the critical temperature."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife import ising
from alife.ising3d import (
    TC2D, TC3D, mean_field_tc, run, sweep_temperature, locate_tc, binder_crossing,
)

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r113_ising3d")
os.makedirs(OUT, exist_ok=True)

temps3d = np.linspace(5.6, 3.6, 18)
s16 = sweep_temperature(L=16, temps=temps3d, equil=400, measure=500, seed=1)
s24 = sweep_temperature(L=24, temps=temps3d, equil=500, measure=600, seed=2)
t2d, m2d, chi2d, _ = ising.sweep_temperature(size=32, temps=np.linspace(1.4, 3.3, 16),
                                             equil=400, measure=500, seed=3)

tc_chi = locate_tc(s24["T"], s24["chi"])
tc_binder = binder_crossing(temps3d, s16["binder"], s24["binder"])
print(f"3D T_c: chi-peak(L=24)={tc_chi:.3f}  Binder-crossing={tc_binder:.3f}  known={TC3D}")
print(f"2D T_c (Onsager) = {TC2D:.3f}   |   mean-field: z=4->{mean_field_tc(4)}  z=6->{mean_field_tc(6)}")

# 3D mid-plane slices across the transition
slices = {T: run(L=40, T=T, sweeps=500, seed=5)["spins"][:, :, 20]
          for T in (3.8, TC3D, 5.2)}

fig = plt.figure(figsize=(15.5, 8.4), facecolor="white")

axA = fig.add_subplot(2, 3, 1)
axA.plot(t2d, m2d, "s-", color="#0077b6", ms=4, label="2D  (z=4)")
axA.plot(s24["T"], s24["M"], "o-", color="#d00000", ms=4, label="3D  (z=6, L=24)")
axA.axvline(TC2D, color="#0077b6", ls=":", lw=1.2); axA.axvline(TC3D, color="#d00000", ls=":", lw=1.2)
axA.set_xlabel("temperature T"); axA.set_ylabel("magnetisation |m|")
axA.set_title("Dimension lifts the transition:\n2D T_c=2.27  ->  3D T_c=4.51", fontsize=10.5)
axA.legend(fontsize=9); axA.grid(alpha=0.3)

axB = fig.add_subplot(2, 3, 2)
axB.plot(s16["T"], s16["chi"], "o-", color="#f48c06", ms=4, label="L=16")
axB.plot(s24["T"], s24["chi"], "o-", color="#d00000", ms=4, label="L=24")
axB.axvline(TC3D, color="#6a040f", ls="--", lw=1.3, label=f"known T_c={TC3D}")
axB.axvline(TC2D, color="#0077b6", ls=":", lw=1.2, label=f"2D T_c={TC2D:.2f}")
axB.set_xlabel("temperature T"); axB.set_ylabel("susceptibility  chi")
axB.set_title(f"Susceptibility peaks at 3D T_c\n(measured peak {tc_chi:.2f})", fontsize=10.5)
axB.legend(fontsize=8.5); axB.grid(alpha=0.3)

axC = fig.add_subplot(2, 3, 3)
axC.plot(s16["T"], s16["binder"], "o-", color="#f48c06", ms=4, label="L=16")
axC.plot(s24["T"], s24["binder"], "o-", color="#d00000", ms=4, label="L=24")
axC.axvline(tc_binder, color="#6a040f", ls="--", lw=1.3, label=f"crossing T_c={tc_binder:.2f}")
axC.set_xlabel("temperature T"); axC.set_ylabel("Binder cumulant  U")
axC.set_title("Binder crossing pins T_c\n(size-independent fixed point)", fontsize=10.5)
axC.legend(fontsize=8.5); axC.grid(alpha=0.3)

labels = [("T=3.8 < T_c : ordered", "#222"), (f"T={TC3D} ~ T_c : clusters at all scales", "#222"),
          ("T=5.2 > T_c : disordered", "#222")]
for k, (T, lab) in enumerate(zip(slices, labels)):
    ax = fig.add_subplot(2, 3, 4 + k)
    ax.imshow(slices[T], cmap="coolwarm", vmin=-1, vmax=1, interpolation="nearest")
    ax.set_title(lab[0], fontsize=10); ax.set_xticks([]); ax.set_yticks([])

fig.suptitle("R113 · 3D Ising model — more neighbours per spin (z: 4->6) push the order-disorder "
             "transition from T_c=2.27 (2D) up to 4.51 (3D); located 3 independent ways",
             fontsize=12, y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "ising3d.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
