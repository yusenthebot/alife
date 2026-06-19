"""R93 figure — Schelling segregation: mild preferences, extreme separation."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

from alife.schelling import init_grid, run, tipping_curve, segregation

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r93_schelling")
os.makedirs(OUT, exist_ok=True)
CMAP = ListedColormap(["#f3f3f3", "#2c6fbb", "#d1492b"])   # empty, type A, type B

start = init_grid(90, frac_empty=0.1, seed=1)
settled = run(size=90, frac_empty=0.1, tau=0.3, steps=80, seed=1)
taus, seg = tipping_curve(np.linspace(0.0, 0.8, 17), size=70, steps=80, seed=4)
runs = {t: run(size=80, frac_empty=0.1, tau=t, steps=80, seed=2) for t in (0.0, 0.3, 0.5)}

fig = plt.figure(figsize=(15, 8.6), facecolor="white")

axA = fig.add_subplot(2, 2, 1)
axA.imshow(start, cmap=CMAP, vmin=0, vmax=2, interpolation="nearest")
axA.set_title(f"Start: well mixed (segregation {segregation(start):.2f})", fontsize=10.5)
axA.axis("off")

axB = fig.add_subplot(2, 2, 2)
axB.imshow(settled["grid"], cmap=CMAP, vmin=0, vmax=2, interpolation="nearest")
axB.set_title(f"Mild preference τ=0.3 → segregated (seg {settled['final_seg']:.2f})\n"
              f"yet everyone is content (happy {settled['final_happy']:.0%})", fontsize=10.5)
axB.axis("off")

axC = fig.add_subplot(2, 2, 3)
axC.plot(taus, seg, "o-", color="#6a1b9a")
axC.axhline(0.5, color="#aaa", ls=":", lw=1, label="mixed (0.5)")
axC.axvline(0.5, color="#bbb", ls="--", lw=1)
axC.scatter([0.0], [seg[0]], color="#2a9d8f", zorder=5, s=40, label="τ=0 control (stays mixed)")
axC.annotate("a mild τ already\nsegregates", xy=(0.3, seg[np.argmin(np.abs(taus - 0.3))]),
             xytext=(0.33, 0.62), fontsize=9, color="#6a1b9a",
             arrowprops=dict(arrowstyle="->", color="#6a1b9a"))
axC.set_xlabel("tolerance threshold  τ  (min. same-type fraction wanted)")
axC.set_ylabel("final segregation index")
axC.set_title("Tipping point: segregation vs preference", fontsize=10.5)
axC.set_ylim(0.45, 1.02); axC.legend(fontsize=8); axC.grid(alpha=0.3)

axD = fig.add_subplot(2, 2, 4)
for t, c in zip((0.0, 0.3, 0.5), ("#2a9d8f", "#e76f51", "#6a1b9a")):
    axD.plot(runs[t]["seg"], color=c, label=f"τ={t} (→ {runs[t]['final_seg']:.2f})")
axD.axhline(0.5, color="#ccc", ls=":", lw=1)
axD.set_xlabel("relocation round"); axD.set_ylabel("segregation index")
axD.set_title("Segregation grows over time (τ=0 stays mixed)", fontsize=10.5)
axD.legend(fontsize=9); axD.grid(alpha=0.3)

fig.suptitle("R93 · Schelling segregation — mild individual preferences make extreme separation nobody chose",
             fontsize=12.5, y=1.0)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "schelling.png")
fig.savefig(path, dpi=110, bbox_inches="tight")
print("saved", path)
print(f"start seg={segregation(start):.2f}  tau=0.3 final={settled['final_seg']:.2f} happy={settled['final_happy']:.2f}")
print(f"tipping: tau={list(np.round(taus,2))[:9]}...  seg={[round(x,2) for x in seg][:9]}...")
