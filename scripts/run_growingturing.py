"""R117 figure — Turing on a growing domain: stripes INSERT to hold their wavelength as the domain grows."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.growingturing import GrowTuringConfig, run_static, run_growing

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r117_growingturing")
os.makedirs(OUT, exist_ok=True)

cfg = GrowTuringConfig(gamma=4.0, seed=1)
g = run_growing(cfg, N0=70, Nmax=480, grow_factor=1.04, settle=45000, grow_steps=3000, disp_width=480)
L, n = g["lengths"], g["counts"]
wl = L / np.maximum(n, 1)
stat = run_static(cfg, N=240, steps=60000)
lam = stat["wavelength"]

# intrinsic wavelength is set by the chemistry (gamma), not the domain
gammas = [1.5, 2.5, 4.0, 6.0, 9.0]
lam_g = [run_static(GrowTuringConfig(gamma=gm, seed=2), N=240, steps=60000)["wavelength"] for gm in gammas]
print(f"growing: n {n[0]}->{n[-1]} as L {L[0]}->{L[-1]}  corr(L,n)={np.corrcoef(L,n)[0,1]:.3f}  "
      f"wavelength std/mean={wl.std()/wl.mean():.3f}  intrinsic lambda*={lam:.1f}")

fig = plt.figure(figsize=(14.5, 8.4), facecolor="white")

# A: kymograph (normalized coords) -> stripes split/insert as the domain grows
axA = fig.add_subplot(2, 2, 1)
axA.imshow(g["kymo"], aspect="auto", cmap="YlGnBu_r", origin="upper",
           extent=[0, 1, L[-1], L[0]], interpolation="nearest")
axA.set_xlabel("position (normalized to current length)"); axA.set_ylabel("domain length  L  (grows downward)")
axA.set_title("Growing domain: stripes INSERT/split to keep\ntheir spacing (developmental stripe addition)",
              fontsize=10.5)

# B: stripe count proportional to length
axB = fig.add_subplot(2, 2, 2)
axB.plot(L, n, "o-", color="#2a9d8f", ms=4)
fit = np.polyfit(L, n, 1)
axB.plot(L, np.polyval(fit, L), "k--", lw=1, label=f"linear fit (slope {fit[0]:.3f}/cell)")
axB.set_xlabel("domain length L"); axB.set_ylabel("number of stripes")
axB.set_title(f"Stripe count grows in PROPORTION to length\n(n ~ L/lambda*, corr={np.corrcoef(L,n)[0,1]:.3f})",
              fontsize=10.5)
axB.legend(fontsize=9); axB.grid(alpha=0.3)

# C: wavelength sawtooth around the intrinsic value
axC = fig.add_subplot(2, 2, 3)
axC.plot(L, wl, "o-", color="#6a040f", ms=4, label="wavelength L/n")
axC.axhline(lam, color="#0077b6", ls="--", lw=1.3, label=f"static intrinsic lambda*={lam:.1f}")
axC.set_xlabel("domain length L"); axC.set_ylabel("stripe spacing  L / n")
axC.set_title("Spacing is MAINTAINED, not stretched:\nstretch to ~1.5x lambda*, insert, reset (sawtooth)", fontsize=10.5)
axC.legend(fontsize=8.5); axC.grid(alpha=0.3)

# D: chemistry sets the intrinsic wavelength
axD = fig.add_subplot(2, 2, 4)
axD.plot(gammas, lam_g, "o-", color="#e85d04", ms=5, label="measured lambda*")
gg = np.linspace(min(gammas), max(gammas), 50)
axD.plot(gg, lam_g[2] * np.sqrt(4.0 / gg), "k--", lw=1, label="~ 1/sqrt(gamma)")
axD.set_xlabel("reaction rate  gamma"); axD.set_ylabel("intrinsic wavelength lambda*")
axD.set_title("Wavelength is set by the CHEMISTRY (gamma),\nnot the domain -- so growth must insert stripes",
              fontsize=10.5)
axD.legend(fontsize=8.5); axD.grid(alpha=0.3)

fig.suptitle("R117 · Turing patterns on a growing domain — the intrinsic wavelength is fixed by reaction-"
             "diffusion, so a growing embryo keeps spacing by INSERTING stripes (Crampin-Gaffney-Maini 1999)",
             fontsize=11, y=0.985)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "growingturing.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
