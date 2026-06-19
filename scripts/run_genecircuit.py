"""R108 figure — synthetic gene circuits: the repressilator clock & the toggle switch."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.genecircuit import repressor_ring, oscillation_amplitude, toggle_final_state
from scipy.integrate import solve_ivp

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r108_genecircuit")
os.makedirs(OUT, exist_ok=True)

rep = repressor_ring(n_genes=3, hill=2.5, alpha=12, seed=1, t_max=160)
ns = [2, 3, 4, 5, 6, 7]
amps = [oscillation_amplitude(repressor_ring(n_genes=n, hill=2.5, alpha=12, seed=1)) for n in ns]
hills = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0]
hamps = [oscillation_amplitude(repressor_ring(n_genes=3, hill=h, alpha=12, seed=1)) for h in hills]

fig = plt.figure(figsize=(15, 4.8), facecolor="white")

axA = fig.add_subplot(1, 3, 1)
for i, c in enumerate(["#e63946", "#2a9d8f", "#457b9d"]):
    axA.plot(rep["t"], rep["proteins"][i], color=c, label=f"gene {i}")
axA.set_xlabel("time"); axA.set_ylabel("protein level")
axA.set_title("Repressilator (3-gene ring) → genetic clock\nthree proteins chase each other", fontsize=10.5)
axA.legend(fontsize=8.5)

axB = fig.add_subplot(1, 3, 2)
colors = ["#e63946" if n % 2 else "#999" for n in ns]
axB.bar([str(n) for n in ns], amps, color=colors)
axB.set_xlabel("repression-ring size n"); axB.set_ylabel("oscillation amplitude")
axB.set_title("Parity rule: ODD rings oscillate (red),\nEVEN rings are silent/bistable (grey)", fontsize=10.5)

axC = fig.add_subplot(1, 3, 3)
axC.plot(hills, hamps, "o-", color="#6a040f")
axC.axhline(0.2, color="#aaa", ls=":", lw=1)
axC.set_xlabel("Hill cooperativity n"); axC.set_ylabel("oscillation amplitude (3-gene)")
axC.set_title("Cooperativity needed: no oscillation until\nHill ≳ 2", fontsize=10.5)
axC.grid(alpha=0.3)

# inset-style toggle bistability note via second axis? keep 3 panels; add toggle as text annotation
a = toggle_final_state(hill=3, bias=+0.5); b = toggle_final_state(hill=3, bias=-0.5)
axA.text(0.02, 0.02, f"(toggle switch, 2-gene: bias→ (p0,p1)=({a[0]:.0f},{a[1]:.0f}) or ({b[0]:.0f},{b[1]:.0f}) = 1-bit memory)",
         transform=fig.transFigure, fontsize=8, color="#555")

fig.suptitle("R108 · Synthetic gene circuits — repressilator clock & toggle switch (loop parity decides)",
             fontsize=12.5, y=1.02)
fig.tight_layout(rect=[0, 0.04, 1, 0.92])
path = os.path.join(OUT, "genecircuit.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
print(f"amp by ring n={ns}: {[round(a,1) for a in amps]}  amp by hill={hills}: {[round(a,1) for a in hamps]}")
print(f"toggle: bias+ ->({a[0]:.2f},{a[1]:.2f})  bias- ->({b[0]:.2f},{b[1]:.2f})")
