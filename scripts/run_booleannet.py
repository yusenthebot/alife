"""R94 figure — Kauffman random Boolean networks: the order-chaos transition at K=2."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.booleannet import (make_network, derrida_curve, derrida_slope,
                              damage_spread, count_attractors)

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r94_booleannet")
os.makedirs(OUT, exist_ok=True)
COLORS = {1: "#2a9d8f", 2: "#e9c46a", 3: "#e76f51", 5: "#9d0208"}

fig = plt.figure(figsize=(15, 8.6), facecolor="white")

# A. Derrida curves: below diagonal=ordered, on=critical, above=chaotic
axA = fig.add_subplot(2, 2, 1)
axA.plot([0, 0.5], [0, 0.5], "k--", lw=1, label="diagonal (critical)")
for k in (1, 2, 3, 5):
    net = make_network(500, k, seed=1)
    xs, ys = derrida_curve(net, trials=60, seed=1)
    axA.plot(xs, ys, "o-", color=COLORS[k], ms=3, label=f"K={k}")
axA.set_xlabel("input difference  (Hamming, t)"); axA.set_ylabel("output difference  (t+1)")
axA.set_title("Derrida map: K=1 contracts (order), K=2 on the line, K≥3 expands (chaos)", fontsize=10)
axA.legend(fontsize=8.5); axA.grid(alpha=0.3)

# B. Derrida slope vs K -> the K/2 law, crossing 1 at K=2
axB = fig.add_subplot(2, 2, 2)
Ks = [1, 2, 3, 4, 5, 6]
slopes = [np.mean([derrida_slope(make_network(600, k, seed=s), trials=300, seed=s) for s in range(4)]) for k in Ks]
axB.plot(Ks, slopes, "o-", color="#264653", label="measured sensitivity")
axB.plot(Ks, [k / 2 for k in Ks], ":", color="#888", label="theory K/2")
axB.axhline(1.0, color="crimson", ls="--", lw=1)
axB.axvline(2.0, color="crimson", ls="--", lw=1)
axB.text(2.05, 0.4, "critical K=2", color="crimson", fontsize=9)
axB.set_xlabel("connectivity K"); axB.set_ylabel("Derrida slope (sensitivity)")
axB.set_title("Sensitivity = K/2 → ordered <1, chaotic >1", fontsize=10.5)
axB.legend(fontsize=8.5); axB.grid(alpha=0.3)

# C. damage spreading over time
axC = fig.add_subplot(2, 2, 3)
for k in (1, 2, 3, 5):
    d = np.mean([damage_spread(make_network(600, k, seed=s), steps=40, seed=s) for s in range(6)], axis=0)
    axC.plot(d, color=COLORS[k], label=f"K={k}")
axC.set_xlabel("time step"); axC.set_ylabel("damage (normalized Hamming)")
axC.set_title("One flipped gene: heals (K=1), marginal (K=2), avalanches (K≥3)", fontsize=10.5)
axC.legend(fontsize=8.5); axC.grid(alpha=0.3)

# D. attractor cycle length explodes past K=2 (cell types -> chaos)
axD = fig.add_subplot(2, 2, 4)
Kd = [1, 2, 3, 4, 5]
med = []
for k in Kd:
    ml = np.median([count_attractors(make_network(150, k, seed=s), n_init=30, max_steps=2000, seed=s)[1]
                    for s in range(4)])
    med.append(ml)
axD.semilogy(Kd, med, "o-", color="#6a040f")
axD.axhline(2000, color="#aaa", ls=":", lw=1)
axD.text(1.1, 2200, "search cap (chaotic: cycle never closes)", fontsize=8, color="#888")
axD.axvline(2.0, color="crimson", ls="--", lw=1)
axD.set_xlabel("connectivity K"); axD.set_ylabel("median attractor cycle length")
axD.set_title("Attractors short (cell types) for K≤2, explode for K≥3", fontsize=10.5)
axD.grid(alpha=0.3, which="both")

fig.suptitle("R94 · Kauffman random Boolean networks — order, chaos, and the critical edge at K=2",
             fontsize=13, y=1.0)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "booleannet.png")
fig.savefig(path, dpi=110, bbox_inches="tight")
print("saved", path)
print(f"Derrida slopes K=1..6: {[round(s,2) for s in slopes]}  (theory K/2, crosses 1 at K=2)")
print(f"median cycle len K=1..5: {med}")
