"""R127 figure — Swift-Hohenberg convection: rolls vs honeycomb hexagons + the FFT 6-fold signature."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dataclasses import replace

from alife.swifthohenberg import SHConfig, run, dominant_wavenumber, cell_count, mean_elongation

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r127_swifthohenberg")
os.makedirs(OUT, exist_ok=True)

N = 200
rolls = run(SHConfig(N=N, r=0.4, g=0.0, steps=5000, seed=1))["u"]
hexf = run(SHConfig(N=N, r=0.1, g=1.2, steps=5000, seed=1))["u"]
print(f"rolls: dom_k={dominant_wavenumber(rolls):.2f} elong={mean_elongation(rolls):.2f}")
print(f"hex:   dom_k={dominant_wavenumber(hexf):.2f} elong={mean_elongation(hexf):.2f} cells={cell_count(hexf)}")

def fft_crop(u, half=34):
    F = np.log(np.abs(np.fft.fftshift(np.fft.fft2(u - u.mean()))) + 1)
    c = u.shape[0] // 2
    return F[c - half:c + half, c - half:c + half]

# g-sweep transition (fixed r)
gs = np.linspace(0.0, 1.6, 7)
elong = [mean_elongation(run(SHConfig(N=140, r=0.12, g=float(g), steps=4000, seed=2))["u"]) for g in gs]

fig = plt.figure(figsize=(15, 8.4), facecolor="white")

ax1 = fig.add_subplot(2, 3, 1); ax1.imshow(rolls, cmap="RdBu"); ax1.axis("off")
ax1.set_title("ROLLS (g=0): parallel stripes\n(convection rolls)", fontsize=10.5)
ax2 = fig.add_subplot(2, 3, 2); ax2.imshow(hexf, cmap="RdBu"); ax2.axis("off")
ax2.set_title("HEXAGONS (g=1.2, near onset):\nhoneycomb Benard cells", fontsize=10.5)

ax3 = fig.add_subplot(2, 3, 4); ax3.imshow(fft_crop(rolls), cmap="magma"); ax3.axis("off")
ax3.set_title("FFT of rolls: a diffuse ring\n(labyrinth = many roll orientations)", fontsize=10.5)
ax4 = fig.add_subplot(2, 3, 5); ax4.imshow(fft_crop(hexf), cmap="magma"); ax4.axis("off")
ax4.set_title("FFT of hexagons: 6 spots at 60deg\n(three orientations)", fontsize=10.5)

ax5 = fig.add_subplot(2, 3, 3)
ax5.plot(gs, elong, "o-", color="#9c4a00")
ax5.axhline(1.8, color="#999", ls=":", lw=1, label="rolls / hexagons cut")
ax5.set_xlabel("up/down asymmetry  g"); ax5.set_ylabel("cell elongation")
ax5.set_title("Raising g switches rolls -> hexagons\n(elongated stripes -> round cells)", fontsize=10.5)
ax5.legend(fontsize=8.5); ax5.grid(alpha=0.3)

ax6 = fig.add_subplot(2, 3, 6)
k = np.linspace(0, 2, 200)
ax6.plot(k, 0.3 - (1 - k ** 2) ** 2, color="#3a0ca3")
ax6.axhline(0, color="#999", lw=0.8); ax6.axvline(1, color="#d00000", ls="--", lw=1.2, label="selected k=1")
ax6.set_xlabel("wavenumber k"); ax6.set_ylabel("growth rate  r-(1-k^2)^2")
ax6.set_title("Built-in wavelength: growth peaks at k=1\n(measured dom_k~1.0)", fontsize=10.5)
ax6.legend(fontsize=8.5); ax6.grid(alpha=0.3)

fig.suptitle("R127 · Swift-Hohenberg / Rayleigh-Benard convection — a built-in wavelength (k=1) and one "
             "asymmetry knob g: parallel ROLLS vs honeycomb HEXAGONS (the Benard cells)", fontsize=11.5, y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "swifthohenberg.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
