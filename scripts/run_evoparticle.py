"""R91 figure — Evolved Particle Life: evolution discovers self-propelled swarms.

Asymmetric interactions break momentum conservation -> generic self-propulsion; a GA sculpts it into
fast directed swimmers; symmetrizing the matrix abolishes all motion (the asymmetry is the engine).
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.evoparticle import EvoConfig, evolve, motility, random_baseline

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r91_evoparticle")
os.makedirs(OUT, exist_ok=True)
cfg = EvoConfig()

# --- evolve once (the expensive step), cache the result for instant re-renders ---
cache = os.path.join(OUT, "ga_result.npz")
if os.path.exists(cache):
    z = np.load(cache)
    res = {"best_matrix": z["best_matrix"], "best_fitness": float(z["best_fitness"]),
           "best_hist": z["best_hist"], "mean_hist": z["mean_hist"]}
else:
    res = evolve(cfg, gens=16, pop=16, seed=0, eval_seeds=2)
    np.savez(cache, best_matrix=res["best_matrix"], best_fitness=res["best_fitness"],
             best_hist=res["best_hist"], mean_hist=res["mean_hist"])
best = res["best_matrix"]
np.save(os.path.join(OUT, "best_matrix.npy"), best)

# --- distributions: random asymmetric vs symmetric control ---
rng = np.random.default_rng(11)
asym = random_baseline(cfg, n=60, seed=11)
sym = np.array([motility((lambda M: (M + M.T) / 2)(rng.uniform(-1, 1, (4, 4))), cfg, seed=1)
                for _ in range(60)])
best_drift, best_traj, (bpos, btyp) = motility(best, cfg, seed=1, return_traj=True)
sym_best = motility((best + best.T) / 2, cfg, seed=1)

# trajectories for comparison
_, traj_rand, _ = motility(rng.uniform(-1, 1, (4, 4)), cfg, seed=1, return_traj=True)
_, traj_sym, _ = motility((best + best.T) / 2, cfg, seed=1, return_traj=True)

fig = plt.figure(figsize=(15, 9), facecolor="white")

# A. motility distributions + controls
axA = fig.add_subplot(2, 2, 1)
axA.hist(asym, bins=20, color="#4c72b0", alpha=0.8, label=f"random asymmetric (max {asym.max():.0f})")
axA.hist(sym, bins=20, color="#999999", alpha=0.9, label="symmetric control (≈0)")
axA.axvline(best_drift, color="crimson", lw=2, label=f"evolved champion ({best_drift:.0f})")
axA.set_xlabel("net centre-of-mass drift (self-propulsion)")
axA.set_ylabel("matrices")
axA.set_title("Asymmetry → self-propulsion; symmetry → none; evolution → far more", fontsize=10.5)
axA.legend(fontsize=8.5)

# B. GA fitness curve
axB = fig.add_subplot(2, 2, 2)
g = np.arange(len(res["best_hist"]))
axB.plot(g, res["best_hist"], "o-", color="crimson", label="best")
axB.plot(g, res["mean_hist"], "s-", color="#888", label="population mean")
axB.set_xlabel("generation"); axB.set_ylabel("motility (CoM drift)")
axB.set_title(f"Evolution amplifies locomotion ({res['best_hist'][0]:.0f} → {res['best_fitness']:.0f})", fontsize=10.5)
axB.legend(fontsize=9); axB.grid(alpha=0.3)

# C. CoM trajectories
axC = fig.add_subplot(2, 2, 3)
axC.plot(best_traj[:, 0], best_traj[:, 1], color="crimson", lw=2, label=f"evolved (drift {best_drift:.0f})")
axC.plot(traj_rand[:, 0], traj_rand[:, 1], color="#4c72b0", lw=1.5, label="random asymmetric")
axC.plot(traj_sym[:, 0], traj_sym[:, 1], color="#999", lw=1.5, label=f"symmetrized evolved ({sym_best:.0f})")
axC.scatter([0], [0], color="k", s=20, zorder=5)
axC.set_xlabel("CoM x (world units)"); axC.set_ylabel("CoM y")
axC.set_title("Centre-of-mass path: evolved swarm travels a long directed path", fontsize=10.5)
axC.legend(fontsize=8.5); axC.set_aspect("equal", adjustable="datalim"); axC.grid(alpha=0.3)

# D. evolved swarm snapshot (colored by type)
axD = fig.add_subplot(2, 2, 4)
colors = np.array(["#e6194B", "#3cb44b", "#4363d8", "#f58231"])
axD.scatter(bpos[:, 0], bpos[:, 1], c=colors[btyp], s=6, alpha=0.85)
axD.set_title("Evolved swarm (colored by type) — a self-propelled active cluster", fontsize=10.5)
axD.set_aspect("equal"); axD.set_xlim(0, cfg.world); axD.set_ylim(0, cfg.world); axD.axis("off")

fig.suptitle("R91 · Evolved Particle Life — selection discovers self-propelled matter (the asymmetry is the engine)",
             fontsize=13, y=1.0)
fig.tight_layout(rect=[0, 0, 1, 0.96])
path = os.path.join(OUT, "evoparticle.png")
fig.savefig(path, dpi=110, bbox_inches="tight")
print("saved", path)
print(f"evolved={best_drift:.0f}  symmetrized={sym_best:.0f}  random max={asym.max():.0f}  sym mean={sym.mean():.2f}")
