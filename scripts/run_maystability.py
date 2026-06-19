"""R116 figure — May's complexity-stability + Allesina-Tang: random community spectra and the edge of stability."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from scipy import linalg

from alife.maystability import community_matrix, complexity, stability_curve

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r116_maystability")
os.makedirs(OUT, exist_ok=True)

S, C = 400, 0.3
def ev(sigma, rho, seed=0):
    return linalg.eigvals(community_matrix(S, C, sigma, rho, d=1.0, seed=seed))

sig_unstable = 1.25 / np.sqrt(S * C)          # kappa ~ 1.25 (random: unstable)
ev_rand = ev(sig_unstable, 0.0, 1)
sig_edge = 1.0 / np.sqrt(S * C)               # kappa ~ 1.0 — compare structures here
ev_pp, ev_rd, ev_mut = ev(sig_edge, -0.6, 2), ev(sig_edge, 0.0, 2), ev(sig_edge, 0.6, 2)

sigmas = np.linspace(0.2, 2.6, 18) / np.sqrt(250 * 0.3)
k_pp, f_pp = stability_curve(sigmas, S=250, C=0.3, rho=-0.6, reps=30, seed=10)
k_rd, f_rd = stability_curve(sigmas, S=250, C=0.3, rho=0.0, reps=30, seed=11)
k_mut, f_mut = stability_curve(sigmas, S=250, C=0.3, rho=0.6, reps=30, seed=12)
print(f"random transition near kappa=1: frac at k~1 = {f_rd[np.argmin(np.abs(k_rd-1))]:.2f}")

fig = plt.figure(figsize=(14.5, 8.4), facecolor="white")

# A: random spectrum crossing the stability line
axA = fig.add_subplot(2, 2, 1)
axA.scatter(ev_rand.real, ev_rand.imag, s=6, c="#d00000", alpha=0.6)
kap = complexity(S, C, sig_unstable)
axA.add_patch(plt.Circle((-1, 0), kap, fill=False, color="k", ls="--", lw=1.3))
axA.axvline(0, color="#0077b6", lw=1.4)
axA.set_xlabel("Re(lambda)"); axA.set_ylabel("Im(lambda)")
axA.set_title(f"Girko disk (random, kappa={kap:.2f}>1):\neigenvalues spill past Re=0 -> UNSTABLE", fontsize=10.5)
axA.set_aspect("equal"); axA.grid(alpha=0.3)

# B: May transition
axB = fig.add_subplot(2, 2, 2)
axB.plot(k_rd, f_rd, "o-", color="#6a040f")
axB.axvline(1.0, color="k", ls="--", lw=1.2, label="boundary  sigma*sqrt(SC)=1")
axB.set_xlabel("complexity  sigma*sqrt(S*C)"); axB.set_ylabel("fraction of stable communities")
axB.set_title("May 1972: complexity DEstabilises\n(stability collapses past the boundary)", fontsize=10.5)
axB.legend(fontsize=9); axB.grid(alpha=0.3)

# C: elliptic law — three interaction structures
axC = fig.add_subplot(2, 2, 3)
for evs, rho, col, lab in [(ev_pp, -0.6, "#2a9d8f", "predator-prey (rho<0)"),
                           (ev_rd, 0.0, "#888", "random (rho=0)"),
                           (ev_mut, 0.6, "#e85d04", "mutualism (rho>0)")]:
    axC.scatter(evs.real, evs.imag, s=5, color=col, alpha=0.5)
    kap = complexity(S, C, sig_edge)
    axC.add_patch(Ellipse((-1, 0), 2 * kap * (1 + rho), 2 * kap * (1 - rho),
                          fill=False, color=col, lw=1.3, label=lab))
axC.axvline(0, color="#0077b6", lw=1.4)
axC.set_xlabel("Re(lambda)"); axC.set_ylabel("Im(lambda)")
axC.set_title("Allesina-Tang elliptic law (kappa=1):\npredator-prey shrinks the cloud away from Re=0", fontsize=10.5)
axC.set_aspect("equal"); axC.legend(fontsize=8); axC.grid(alpha=0.3)

# D: stability curves shift with structure
axD = fig.add_subplot(2, 2, 4)
axD.plot(k_pp, f_pp, "o-", color="#2a9d8f", label="predator-prey (edge ~2.5)")
axD.plot(k_rd, f_rd, "o-", color="#888", label="random (edge 1.0)")
axD.plot(k_mut, f_mut, "o-", color="#e85d04", label="mutualism (edge ~0.6)")
axD.set_xlabel("complexity  sigma*sqrt(S*C)"); axD.set_ylabel("fraction stable")
axD.set_title("Structure beats complexity: predator-prey\nstays stable far past the random edge", fontsize=10.5)
axD.legend(fontsize=8.5); axD.grid(alpha=0.3)

fig.suptitle("R116 · May's complexity-stability theorem + Allesina-Tang — random-matrix spectra set the "
             "edge of ecological stability (sigma*sqrt(SC)=1); predator-prey structure pushes it out",
             fontsize=11.5, y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "maystability.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
