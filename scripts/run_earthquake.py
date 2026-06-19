"""R107 figure — OFC earthquake model: Gutenberg-Richter power law & the conservation control."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.earthquake import simulate, size_distribution, gr_exponent, big_quake_fraction

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r107_earthquake")
os.makedirs(OUT, exist_ok=True)
L = 44

main = simulate(L=L, alpha=0.22, n_quakes=6000, seed=1, warmup=1000)
tau = gr_exponent(main)
alphas = [0.12, 0.17, 0.21, 0.25]
runs = {a: simulate(L=L, alpha=a, n_quakes=5000, seed=1, warmup=1000) for a in alphas}
bigfrac = [big_quake_fraction(runs[a], L) for a in alphas]

fig = plt.figure(figsize=(15, 4.8), facecolor="white")

axA = fig.add_subplot(1, 3, 1)
cx, cy = size_distribution(main)
axA.loglog(cx, cy, "o", color="#6a040f", ms=5)
m = (cx >= 2) & (cx <= 0.3 * cx.max())
fit = np.polyfit(np.log(cx[m]), np.log(cy[m]), 1)
axA.loglog(cx[m], np.exp(np.polyval(fit, np.log(cx[m]))), "--", color="#d00000",
           label=f"power law τ≈{tau:.2f}")
axA.set_xlabel("earthquake size s (sites slipped)"); axA.set_ylabel("P(s)")
axA.set_title(f"Gutenberg-Richter law (α=0.22, cons={4*0.22:.2f})", fontsize=10.5)
axA.legend(fontsize=9)

axB = fig.add_subplot(1, 3, 2)
cols = plt.get_cmap("viridis")(np.linspace(0.1, 0.85, len(alphas)))
for a, c in zip(alphas, cols):
    cx, cy = size_distribution(runs[a])
    axB.loglog(cx, cy, "o-", color=c, ms=3, label=f"α={a}")
axB.set_xlabel("earthquake size s"); axB.set_ylabel("P(s)")
axB.set_title("Conservation α tunes the catalogue\n(dissipative→small, conservative→spanning)", fontsize=10)
axB.legend(fontsize=8)

axC = fig.add_subplot(1, 3, 3)
axC.plot(alphas, bigfrac, "o-", color="#1f77b4")
axC.axvline(0.25, color="#aaa", ls=":", lw=1)
axC.text(0.243, 0.5, "conservative", rotation=90, fontsize=8, color="#888", va="center")
axC.set_xlabel("conservation parameter α"); axC.set_ylabel(f"fraction of slip in big quakes (≥L={L})")
axC.set_title("More conservation → bigger ruptures", fontsize=10.5)
axC.grid(alpha=0.3)

fig.suptitle("R107 · Olami-Feder-Christensen earthquakes — non-conservative self-organized criticality",
             fontsize=12.5, y=1.02)
fig.tight_layout(rect=[0, 0, 1, 0.92])
path = os.path.join(OUT, "earthquake.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
print(f"alpha=0.22 GR tau={tau:.2f}  max quake={main.max()}  big-frac by alpha={[round(b,2) for b in bigfrac]}")
