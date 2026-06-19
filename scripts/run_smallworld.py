"""R87 figure — Watts-Strogatz small worlds: shortcuts collapse path length, clustering survives."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.smallworld import watts_strogatz, clustering_coefficient, average_path_length, spread_time, ws_sweep

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r87_smallworld")
os.makedirs(OUT, exist_ok=True)

# --- classic curves + spreading payoff (larger graph) ---
N, K = 600, 6
ps, C, L = ws_sweep(n=N, k=K, seed=2, reps=5, path_sources=120)
S = []
rng = np.random.default_rng(5)
for p in ps:
    sp = [spread_time(watts_strogatz(N, K, float(p), int(rng.integers(1 << 30))), seeds=6,
                      seed=int(rng.integers(1 << 30))) for _ in range(3)]
    S.append(np.mean(sp))
S = np.asarray(S)
S0 = spread_time(watts_strogatz(N, K, 0.0, 2), seeds=10, seed=2)

# --- three regime drawings on a circular layout (small graph for legibility) ---
n_d, k_d = 60, 4
ang = 2 * np.pi * np.arange(n_d) / n_d
xy = np.c_[np.cos(ang), np.sin(ang)]


def draw(ax, p, title, color):
    g = watts_strogatz(n_d, k_d, p, seed=3)
    for i in range(n_d):
        for j in g[i]:
            if j > i:
                short = min((j - i) % n_d, (i - j) % n_d) <= k_d // 2
                ax.plot(*xy[[i, j]].T, color=("#cccccc" if short else color),
                        lw=(0.6 if short else 1.4), alpha=(0.6 if short else 0.95),
                        zorder=(1 if short else 2))
    ax.scatter(*xy.T, s=14, color="#222", zorder=3)
    ax.set_title(title, fontsize=10.5)
    ax.set_aspect("equal"); ax.axis("off")


fig = plt.figure(figsize=(15, 8.4), facecolor="white")

axA = fig.add_subplot(2, 3, (1, 2))
axA.semilogx(ps, C, "o-", color="#2a9d8f", label="C(p)/C(0)  — clustering")
axA.semilogx(ps, L, "s-", color="#e76f51", label="L(p)/L(0)  — path length")
axA.axvspan(0.004, 0.1, color="#ffe9b0", alpha=0.6, zorder=0)
axA.text(0.018, 0.5, "small-world\nregime", ha="center", fontsize=9, color="#a06800")
axA.set_xlabel("rewiring probability  p"); axA.set_ylabel("fraction of p=0 value")
axA.set_title(f"Watts–Strogatz: a few shortcuts collapse L while C survives  (n={N}, k={K})", fontsize=11)
axA.legend(loc="center left"); axA.grid(alpha=0.3, which="both")
axA.set_ylim(-0.02, 1.05)

axS = fig.add_subplot(2, 3, 3)
axS.semilogx(ps, S, "o-", color="#264653")
axS.axhline(S0, color="#aaa", ls=":", lw=1)
axS.text(ps[0], S0 * 0.93, f"ring: {S0:.0f} rounds", fontsize=8.5, color="#666")
axS.set_xlabel("rewiring probability  p")
axS.set_ylabel("rounds to inform everyone")
axS.set_title("Dynamical payoff:\nspreading speeds up", fontsize=10.5)
axS.grid(alpha=0.3, which="both")

draw(fig.add_subplot(2, 3, 4), 0.0, "Ring lattice  p=0\nclustered, long paths", "#e76f51")
draw(fig.add_subplot(2, 3, 5), 0.1, "Small world  p=0.1\nclustered + shortcuts (red)", "#c1121f")
draw(fig.add_subplot(2, 3, 6), 1.0, "Random  p=1\nshort paths, no clustering", "#5a189a")

fig.suptitle("R87 · Small-world networks — high clustering and short paths at once (Watts–Strogatz 1998)",
             fontsize=13, y=0.99)
fig.tight_layout(rect=[0, 0, 1, 0.97])
path = os.path.join(OUT, "smallworld.png")
fig.savefig(path, dpi=110, bbox_inches="tight")
print("saved", path)
# headline numbers
g01 = watts_strogatz(N, K, 0.01, 1)
print(f"p=0.01: L/L0={L[np.argmin(np.abs(ps-0.01))]:.2f}  C/C0={C[np.argmin(np.abs(ps-0.01))]:.2f}")
print(f"ring spread={S0:.0f}  p=0.1 spread={S[np.argmin(np.abs(ps-0.1))]:.0f}")
