"""R120 milestone gallery — one representative panel per round R111-R119 (runs/ is gitignored)."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, PowerNorm
from dataclasses import replace

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r120_review")
os.makedirs(OUT, exist_ok=True)

fig, axs = plt.subplots(3, 3, figsize=(13.5, 13), facecolor="white")
A = axs.ravel()
def clean(ax, t):
    ax.set_title(t, fontsize=10); ax.set_xticks([]); ax.set_yticks([])

# R111 spatial RPS — coexistence spirals
from alife.rpsmobility import run as rps_run
g = rps_run(L=130, mobility=3.0, steps=450, seed=1)
A[0].imshow(g["grid"], cmap=ListedColormap(["#fff", "#e63946", "#2a9d8f", "#457b9d"]), vmin=0, vmax=3)
clean(A[0], "R111 spatial RPS — 3-species spirals coexist")

# R112 Keller-Segel — chemotactic collapse
from alife.kellersegel import KSConfig, run as ks_run
ks = ks_run(KSConfig(L=96, Dc=6.0, chi=3.0, steps=2600, seed=3))
A[1].imshow(ks["rho"], cmap="magma", norm=PowerNorm(0.4, vmin=0, vmax=float(ks["rho"].max())))
clean(A[1], "R112 Keller-Segel — cells aggregate into mounds")

# R113 3D Ising — mid-slice near T_c
from alife.ising3d import run as is3_run
sl = is3_run(L=36, T=4.3, sweeps=300, seed=2)["spins"][:, :, 18]
A[2].imshow(sl, cmap="coolwarm", vmin=-1, vmax=1)
clean(A[2], "R113 3D Ising — clusters at all scales (T~Tc)")

# R114 somitogenesis — zebra segments
from alife.somitogenesis import SomiteConfig, run as som_run, somite_ids
phi = som_run(SomiteConfig(N=300, v=2.5, omega=1.0, dt=0.01))["frozen_phase"]
A[3].imshow(np.tile(somite_ids(phi) % 2, (40, 1)), cmap=ListedColormap(["#1d3557", "#e9c46a"]), aspect="auto")
clean(A[3], "R114 somitogenesis — segments (size=2pi v/w)")

# R115 chimera — phase snapshot coloured by local order
from alife.chimera import ChimeraConfig, run as ch_run, local_order
ch = ch_run(ChimeraConfig(N=256, kappa=4.0, alpha=1.46, steps=3500, seed=1))
A[4].scatter(np.arange(256), ch["theta"], s=6, c=local_order(ch["theta"]), cmap="viridis")
A[4].set_title("R115 chimera — coherent arc + incoherent arc", fontsize=10); A[4].set_xticks([]); A[4].set_yticks([])

# R116 May stability — Girko eigenvalue disk
from alife.maystability import community_matrix
from scipy import linalg
ev = linalg.eigvals(community_matrix(400, 0.3, 1.25 / np.sqrt(120), 0.0, seed=1))
A[5].scatter(ev.real, ev.imag, s=5, c="#d00000", alpha=0.6); A[5].axvline(0, color="#0077b6")
A[5].set_title("R116 May — eigenvalue disk crosses stability", fontsize=10)
A[5].set_aspect("equal"); A[5].set_xticks([]); A[5].set_yticks([])

# R117 growing-domain Turing — stripe insertion kymograph
from alife.growingturing import GrowTuringConfig, run_growing
gt = run_growing(GrowTuringConfig(gamma=4.0, seed=1), N0=70, Nmax=380, grow_factor=1.05, settle=40000, grow_steps=2800)
A[6].imshow(gt["kymo"], aspect="auto", cmap="YlGnBu_r", origin="upper")
clean(A[6], "R117 growing Turing — stripes insert (n~L)")

# R118 phyllotaxis — golden sunflower
from alife.phyllotaxis import GOLDEN_ANGLE, vogel
P = vogel(GOLDEN_ANGLE, 800)
A[7].scatter(P[:, 0], P[:, 1], s=6, c=np.arange(800), cmap="viridis"); A[7].set_aspect("equal")
clean(A[7], "R118 phyllotaxis — golden-angle packing")

# R119 snowflake — Reiter dendrite
from alife.snowflake import SnowflakeConfig, grow as sf_grow, frozen_mask, to_cartesian
cfg = SnowflakeConfig(L=221, beta=0.5, gamma=0.001, steps=430)
s = sf_grow(cfg); m = frozen_mask(s); X, Y = to_cartesian(cfg.L)
A[8].scatter(X[m], Y[m], s=1.5, c=s[m], cmap="Blues_r"); A[8].set_aspect("equal"); A[8].set_facecolor("#0b1726")
clean(A[8], "R119 snowflake — six-fold dendrite (Reiter)")

fig.suptitle("ALife — milestone gallery R111-R119 (every headline re-verified with fresh seeds at the R120 review)",
             fontsize=13, y=0.995)
fig.tight_layout(rect=[0, 0, 1, 0.97])
path = os.path.join(OUT, "gallery.png")
fig.savefig(path, dpi=110, bbox_inches="tight")
print("saved", path)
