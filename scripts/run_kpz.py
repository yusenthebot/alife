"""R106 figure — KPZ surface growth: ballistic deposition vs random deposition."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.kpz import (ballistic_deposition, random_deposition, mean_growth_exponent,
                       roughness_exponent)

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r106_kpz")
os.makedirs(OUT, exist_ok=True)

# seed-averaged w(t) for clean log-log curves
L, LAY, SEEDS = 1000, 1200, 5
bd = [ballistic_deposition(L, LAY, seed=s) for s in range(SEEDS)]
rd = [random_deposition(L, LAY, seed=s) for s in range(SEEDS)]
t = bd[0]["t"]
wb = np.mean([b["w"] for b in bd], axis=0)
wr = np.mean([r["w"] for r in rd], axis=0)
beta_b, sb = mean_growth_exponent("ballistic", L=L, layers=LAY, seeds=SEEDS)
beta_r, sr = mean_growth_exponent("random", L=L, layers=LAY, seeds=SEEDS)

# interface snapshots (small L, partway)
hb = ballistic_deposition(120, 120, seed=0)["h"]
hr = random_deposition(120, 120, seed=0)["h"]

# roughness exponent alpha (w_sat vs L)
Ls, wsat, alpha = roughness_exponent((32, 64, 128, 256), seed=0)

fig = plt.figure(figsize=(15, 4.8), facecolor="white")

axA = fig.add_subplot(1, 3, 1)
axA.loglog(t, wb, color="#d00000", label=f"ballistic  β≈{beta_b:.2f}±{sb:.2f}")
axA.loglog(t, wr, color="#1f77b4", label=f"random  β≈{beta_r:.2f}")
# reference slopes
axA.loglog(t, wb[5] * (t / t[5]) ** (1 / 3), "--", color="#d00000", lw=0.8, alpha=0.6)
axA.loglog(t, wr[5] * (t / t[5]) ** 0.5, "--", color="#1f77b4", lw=0.8, alpha=0.6)
axA.set_xlabel("time t (layers)"); axA.set_ylabel("interface width w")
axA.set_title("Width growth: KPZ β≈1/3 vs random 1/2\n(dashed = 1/3 and 1/2 reference slopes)", fontsize=10)
axA.legend(fontsize=8.5)

axB = fig.add_subplot(1, 3, 2)
axB.plot(hb - hb.mean(), color="#d00000", lw=0.9, label="ballistic (correlated)")
axB.plot(hr - hr.mean(), color="#1f77b4", lw=0.9, alpha=0.7, label="random (spiky/uncorrelated)")
axB.set_xlabel("column"); axB.set_ylabel("height − mean")
axB.set_title("Interface morphology", fontsize=10.5)
axB.legend(fontsize=8.5)

axC = fig.add_subplot(1, 3, 3)
axC.loglog(Ls, wsat, "o-", color="#6a040f")
axC.loglog(Ls, wsat[0] * (Ls / Ls[0]) ** 0.5, "--", color="#aaa", lw=1, label="slope 1/2 (KPZ α)")
axC.set_xlabel("system size L"); axC.set_ylabel("saturated width w_sat")
axC.set_title(f"Roughness exponent α≈{alpha:.2f} (KPZ 1/2)", fontsize=10.5)
axC.legend(fontsize=8.5)

fig.suptitle("R106 · KPZ surface growth (ballistic deposition) — lateral sticking bends the exponent to 1/3",
             fontsize=12.5, y=1.02)
fig.tight_layout(rect=[0, 0, 1, 0.92])
path = os.path.join(OUT, "kpz.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
print(f"ballistic beta={beta_b:.3f}+-{sb:.3f} random beta={beta_r:.3f}  alpha={alpha:.3f}  "
      f"w_final ballistic={wb[-1]:.1f} random={wr[-1]:.1f}")
