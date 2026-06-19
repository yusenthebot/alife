"""R126 figure — animal coat geometry: domain width sculpts Turing spots (Murray; resolving R92)."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.coatpattern import (
    CoatConfig, run_strip, run_shape, body_tail_mask, n_spots, mean_blob_elongation,
)

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r126_coatpattern")
os.makedirs(OUT, exist_ok=True)

cfg = CoatConfig(steps=11000, seed=1)
widths = [120, 64, 36, 20]
strips = {W: run_strip(cfg, H=130, W=W) for W in widths}
mask = body_tail_mask(120, 320, 100, 26, body_frac=0.4)
creature = run_shape(cfg, mask)
# quantitative: elongation + spot count vs width
wsweep = [120, 96, 72, 52, 38, 28, 20, 14]
strips_q = {W: run_strip(cfg, H=130, W=W) for W in wsweep}
elong = [mean_blob_elongation(strips_q[W]) for W in wsweep]
nsp = [n_spots(strips_q[W]) for W in wsweep]
print("width:", wsweep)
print("elong:", [round(e, 2) for e in elong])
print("nspots:", nsp)

fig = plt.figure(figsize=(15, 8.4), facecolor="white")
gs = fig.add_gridspec(2, 4, height_ratios=[1.0, 1.05], hspace=0.3, wspace=0.25)

# top: the tapering creature (spotted body -> thinning toward the narrow tail)
axc = fig.add_subplot(gs[0, :])
axc.imshow(np.where(mask, creature, np.nan), cmap="copper", vmin=0, vmax=0.42)
axc.set_title("Same chemistry on a tapering body: a spot lattice on the wide body, thinning to few "
              "elongated rows down the narrow tail (Gray-Scott; resolves the R92 Gierer-Meinhardt frontier)",
              fontsize=10.5)
axc.axis("off")

# bottom-left three: width sweep
for j, W in enumerate([120, 36, 20]):
    ax = fig.add_subplot(gs[1, j])
    ax.imshow(strips[W], cmap="copper", vmin=0, vmax=0.42, aspect="auto")
    typ = "spots" if W == 120 else ("elongated" if W == 36 else "blank")
    ax.set_title(f"width {W}: {typ}", fontsize=10); ax.set_xticks([]); ax.set_yticks([])

# bottom-right: elongation + spot count vs width
axm = fig.add_subplot(gs[1, 3])
axm.plot(wsweep, elong, "o-", color="#9c4a00", label="spot elongation")
axm.axhline(1.0, color="#999", ls=":", lw=1)
axm.set_xlabel("domain width"); axm.set_ylabel("elongation (1=round spot)")
axm.invert_xaxis()
axt = axm.twinx(); axt.plot(wsweep, nsp, "s--", color="#2a9d8f", label="spot count")
axt.set_ylabel("spot count", color="#2a9d8f")
axm.set_title("Narrower -> fewer, more elongated spots\n(below one wavelength: blank)", fontsize=10)
axm.legend(fontsize=8, loc="upper left")

fig.suptitle("R126 · How the leopard gets its spots — domain GEOMETRY selects the Turing pattern (Murray): "
             "wide=spots, narrowing elongates them, sub-wavelength=blank (clean stripes a delicate sub-regime)",
             fontsize=11, y=0.97)
fig.tight_layout(rect=[0, 0, 1, 0.94])
path = os.path.join(OUT, "coatpattern.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
