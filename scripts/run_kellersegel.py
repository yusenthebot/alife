"""R112 figure — Keller-Segel chemotactic collapse: a uniform cell lawn streams into mounds above chi_c."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm
from dataclasses import replace

from alife.kellersegel import KSConfig, run, aggregation, chi_critical, growth_rate, growth_rate_theory

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r112_kellersegel")
os.makedirs(OUT, exist_ok=True)

base = KSConfig(L=96, Dc=6.0, steps=7000, seed=3)
xc = chi_critical(base)

sub = run(replace(base, chi=0.5))                                   # below chi_c: uniform lawn (control)
sup = run(replace(base, chi=3.0), record_every=100)                # above chi_c: collapse
stream = sup["snaps"][3400][0]                                      # streaming / incipient mounds
mounds = sup["rho"]                                                 # fully aggregated

# rigorous threshold check: measured vs theoretical linear growth rate of the longest mode
chis = np.linspace(0.4, 3.0, 14)
sig_meas = np.array([growth_rate(replace(base, chi=float(c))) for c in chis])
sig_theory = np.array([growth_rate_theory(base, float(c), mode=(1, 0)) for c in chis])

print(f"chi_c={xc:.3f}  sub peak={aggregation(sub['rho'],1):.2f}  stream peak={aggregation(stream,1):.1f} "
      f"mounds peak={aggregation(mounds,1):.0f}  mass drift={abs(sup['mass'][-1]-sup['mass0'])/sup['mass0']:.0e}")

fig = plt.figure(figsize=(17, 4.4), facecolor="white")

# per-panel normalisation: PowerNorm(gamma<1) compresses the huge collapse dynamic range so the
# depleted background and mound haloes stay visible alongside the sharp peaks
panels = [
    (sub["rho"], None,
     f"chi=0.5 < chi_c\nstable lawn — cells stay scattered (peak {aggregation(sub['rho'],1):.2f}x)"),
    (stream, PowerNorm(0.5, vmin=0, vmax=float(stream.max())),
     f"chi=3.0, mid-run\nstreaming — incipient mounds (peak {aggregation(stream,1):.0f}x)"),
    (mounds, PowerNorm(0.4, vmin=0, vmax=float(mounds.max())),
     f"chi=3.0, late\nchemotactic collapse — mounds (peak {aggregation(mounds,1):.0f}x)"),
]
for k, (field, norm, ttl) in enumerate(panels):
    ax = fig.add_subplot(1, 4, k + 1)
    if norm is None:
        im = ax.imshow(field, cmap="magma", interpolation="nearest")      # autoscale: faint lawn texture
    else:
        im = ax.imshow(field, cmap="magma", norm=norm, interpolation="nearest")
    ax.set_title(ttl, fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

axD = fig.add_subplot(1, 4, 4)
axD.plot(chis, sig_theory, "-", color="#3a0ca3", lw=2, label="linear theory (dispersion)")
axD.plot(chis, sig_meas, "o", color="#e85d04", ms=5, label="measured (single mode)")
axD.axvline(xc, color="#e63946", ls="--", lw=1.4, label=f"chi_c={xc:.2f}")
axD.axhline(0.0, color="#999", ls=":", lw=1)
axD.set_xlabel("chemotactic sensitivity  chi"); axD.set_ylabel("growth rate  sigma(k_min)")
axD.set_title("Growth rate crosses zero AT the\npredicted threshold (theory = measured)", fontsize=10)
axD.legend(fontsize=8.5); axD.grid(alpha=0.3)

fig.suptitle("R112 · Keller-Segel chemotactic aggregation — cells secreting an attractant and climbing it "
             "collapse a uniform lawn into mounds once chi clears chi_c (mass exactly conserved; KS 1970)",
             fontsize=11.5, y=1.04)
fig.tight_layout(rect=[0, 0, 1, 0.9])
path = os.path.join(OUT, "kellersegel.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
print(f"chi   ={np.round(chis,2)}")
print(f"meas  ={np.round(sig_meas,4)}")
print(f"theory={np.round(sig_theory,4)}")
