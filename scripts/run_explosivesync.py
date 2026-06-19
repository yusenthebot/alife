"""R105 figure — explosive synchronization: a first-order, hysteretic sync transition."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.explosivesync import run

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r105_explosivesync")
os.makedirs(OUT, exist_ok=True)
Ks = np.linspace(0.0, 2.5, 22)

corr = run(n=600, m=3, Ks=Ks, seed=1, shuffle=False, equil=450, measure=130)
ctrl = run(n=600, m=3, Ks=Ks, seed=1, shuffle=True, equil=450, measure=130)

fig = plt.figure(figsize=(15, 4.8), facecolor="white")

axA = fig.add_subplot(1, 3, 1)
axA.plot(Ks, corr["rf"], "o-", color="#d00000", label="forward (K↑)")
axA.plot(Ks, corr["rb"], "s-", color="#1f77b4", label="backward (K↓)")
axA.fill_between(Ks, corr["rf"], corr["rb"], color="#ffd6a5", alpha=0.7)
axA.set_xlabel("coupling K"); axA.set_ylabel("coherence r")
axA.set_title(f"Frequency = degree → EXPLOSIVE\nabrupt jump + hysteresis (area {corr['area']:.2f})", fontsize=10.5)
axA.legend(fontsize=8.5); axA.grid(alpha=0.3); axA.set_ylim(-0.02, 1.03)

axB = fig.add_subplot(1, 3, 2)
axB.plot(Ks, ctrl["rf"], "o-", color="#d00000", label="forward (K↑)")
axB.plot(Ks, ctrl["rb"], "s-", color="#1f77b4", label="backward (K↓)")
axB.fill_between(Ks, ctrl["rf"], ctrl["rb"], color="#ffd6a5", alpha=0.7)
axB.set_xlabel("coupling K"); axB.set_ylabel("coherence r")
axB.set_title(f"Control: shuffled frequencies → SMOOTH\nreversible 2nd-order (area {ctrl['area']:.2f})", fontsize=10.5)
axB.legend(fontsize=8.5); axB.grid(alpha=0.3); axB.set_ylim(-0.02, 1.03)

axC = fig.add_subplot(1, 3, 3)
axC.plot(Ks, corr["rf"], "o-", color="#d00000", label=f"freq=degree (jump {np.max(np.diff(corr['rf'])):.2f})")
axC.plot(Ks, ctrl["rf"], "s-", color="#777", label=f"shuffled (jump {np.max(np.diff(ctrl['rf'])):.2f})")
axC.set_xlabel("coupling K"); axC.set_ylabel("coherence r (forward sweep)")
axC.set_title("The forward transition: a cliff vs a ramp", fontsize=10.5)
axC.legend(fontsize=8.5); axC.grid(alpha=0.3); axC.set_ylim(-0.02, 1.03)

fig.suptitle("R105 · Explosive synchronization — frequency-degree correlation turns sync into a first-order switch",
             fontsize=12.5, y=1.02)
fig.tight_layout(rect=[0, 0, 1, 0.92])
path = os.path.join(OUT, "explosivesync.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
print(f"correlated area={corr['area']:.3f} jump={np.max(np.diff(corr['rf'])):.2f}  "
      f"control area={ctrl['area']:.3f} jump={np.max(np.diff(ctrl['rf'])):.2f}")
