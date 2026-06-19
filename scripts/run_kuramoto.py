"""R96 figure — Kuramoto oscillators: the synchronization transition at a critical coupling."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.kuramoto import run, sweep_coupling, order_parameter, gaussian_kc

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r96_kuramoto")
os.makedirs(OUT, exist_ok=True)
SIGMA = 1.0
KC = gaussian_kc(SIGMA)

incoh = run(n=800, K=0.5 * KC, sigma=SIGMA, seed=1)
synced = run(n=800, K=2.5 * KC, sigma=SIGMA, seed=1)
partial = run(n=800, K=1.1 * KC, sigma=SIGMA, seed=1, track_freq=True)   # locked + drifting both present
Ks, rs = sweep_coupling(np.linspace(0.2, 4.5, 22), n=800, sigma=SIGMA, seed=3)

fig = plt.figure(figsize=(15, 8.6), facecolor="white")

def circle(ax, theta, title):
    ax.add_artist(plt.Circle((0, 0), 1, fill=False, color="#ccc"))
    ax.scatter(np.cos(theta), np.sin(theta), s=8, c="#3a86ff", alpha=0.5)
    r, psi = order_parameter(theta)
    ax.arrow(0, 0, r * np.cos(psi), r * np.sin(psi), color="#d00000", width=0.02,
             length_includes_head=True, zorder=5)
    ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.2, 1.2); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(f"{title}\nr = {r:.2f}", fontsize=10.5)

circle(fig.add_subplot(2, 3, 1), incoh["theta"], f"Weak coupling K=0.5 Kc\nincoherent (phases scattered)")
circle(fig.add_subplot(2, 3, 2), synced["theta"], f"Strong coupling K=2.5 Kc\nsynchronized (phases locked)")

axR = fig.add_subplot(2, 3, 3)
axR.plot(incoh["r"], color="#8d99ae", label="K=0.5 Kc (incoherent)")
axR.plot(synced["r"], color="#d00000", label="K=2.5 Kc (synchronizes)")
axR.set_xlabel("time step"); axR.set_ylabel("coherence r")
axR.set_title("Order emerges over time", fontsize=10.5)
axR.legend(fontsize=8.5); axR.grid(alpha=0.3); axR.set_ylim(0, 1)

axT = fig.add_subplot(2, 3, 4)
axT.plot(Ks, rs, "o-", color="#264653")
axT.axvline(KC, color="crimson", ls="--", lw=1)
axT.text(KC + 0.1, 0.1, f"Kc={KC:.2f}\n(theory 2/πg(0))", color="crimson", fontsize=8.5)
axT.set_xlabel("coupling strength K"); axT.set_ylabel("steady-state coherence r")
axT.set_title("Synchronization transition at critical Kc", fontsize=10.5)
axT.grid(alpha=0.3); axT.set_ylim(0, 1)

# partial synchronization: locked plateau vs drifting wings (coupling just above Kc)
axF = fig.add_subplot(2, 3, (5, 6))
o = partial["omega"]; ef = partial["eff_freq"]
order = np.argsort(o)
locked = np.abs(ef) < 0.1
axF.scatter(o[order], ef[order], s=9, c=np.where(locked, "#2a9d8f", "#e76f51")[order], alpha=0.7)
axF.plot(o[order], o[order], color="#bbb", ls="--", lw=1, label="ω (uncoupled)")
axF.set_xlabel("natural frequency ω"); axF.set_ylabel("effective frequency")
axF.set_title(f"Partial sync (K=1.1 Kc): a locked plateau (green, {locked.mean():.0%}, eff freq≈mean) "
              f"flanked by drifting oscillators (orange)", fontsize=10)
axF.legend(fontsize=8.5); axF.grid(alpha=0.3)

fig.suptitle("R96 · Kuramoto oscillators — spontaneous synchronization above a critical coupling",
             fontsize=13, y=1.0)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "kuramoto.png")
fig.savefig(path, dpi=110, bbox_inches="tight")
print("saved", path)
print(f"Kc theory={KC:.2f}  incoherent r={incoh['final_r']:.3f}  synced r={synced['final_r']:.3f}")
print(f"locked fraction (|eff_freq|<0.1): {np.mean(np.abs(ef)<0.1):.2f}")
