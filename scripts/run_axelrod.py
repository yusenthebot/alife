"""R98 figure — Axelrod culture: monoculture vs frozen multiculture, and the transition in q."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.axelrod import run, sweep_traits, domains

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r98_axelrod")
os.makedirs(OUT, exist_ok=True)


def culture_image(culture):
    """Map each unique culture vector to a color (hash -> hue) for the domain map."""
    L, _, F = culture.shape
    flat = culture.reshape(L * L, F)
    _, inv = np.unique(flat, axis=0, return_inverse=True)
    rng = np.random.default_rng(0)
    palette = rng.random((inv.max() + 1, 3)) * 0.8 + 0.1
    return palette[inv].reshape(L, L, 3)


L = 26
mono = run(L=L, F=10, q=5, seed=2, max_sweeps=12000)        # below q_c -> monoculture
frag = run(L=L, F=10, q=120, seed=2, max_sweeps=12000)      # above q_c -> fragmented

qs = np.array([2, 5, 10, 20, 40, 60, 90, 130, 200])
qv, largest = sweep_traits(qs, L=18, F=10, seed=5, max_sweeps=9000)

fig = plt.figure(figsize=(15, 5.0), facecolor="white")

axA = fig.add_subplot(1, 3, 1)
axA.imshow(culture_image(mono["culture"]), interpolation="nearest")
axA.set_title(f"Low diversity q=5 → MONOCULTURE\nlargest domain {mono['largest']:.0%}, {mono['n_regions']} region(s)", fontsize=10.5)
axA.axis("off")

axB = fig.add_subplot(1, 3, 2)
axB.imshow(culture_image(frag["culture"]), interpolation="nearest")
axB.set_title(f"High diversity q=120 → frozen MULTICULTURE\nlargest domain {frag['largest']:.0%}, {frag['n_regions']} regions", fontsize=10.5)
axB.axis("off")

axC = fig.add_subplot(1, 3, 3)
axC.plot(qv, largest, "o-", color="#6a4c93")
axC.axhline(0.5, color="#ccc", ls=":", lw=1)
axC.set_xlabel("number of traits per feature  q"); axC.set_ylabel("largest cultural domain (fraction)")
axC.set_title("Diversity transition: contact unifies only\nwhen cultures start similar enough", fontsize=10.5)
axC.set_ylim(-0.02, 1.05); axC.grid(alpha=0.3)
axC.annotate("monoculture", xy=(10, 0.97), fontsize=9, color="#1f6f3f")
axC.annotate("fragmented", xy=(150, 0.1), fontsize=9, color="#a13")

fig.suptitle("R98 · Axelrod culture dissemination — why contact doesn't always erase differences",
             fontsize=13, y=1.02)
fig.tight_layout(rect=[0, 0, 1, 0.93])
path = os.path.join(OUT, "axelrod.png")
fig.savefig(path, dpi=120, bbox_inches="tight")
print("saved", path)
print(f"mono q=5 largest={mono['largest']:.2f}  frag q=120 largest={frag['largest']:.2f}")
print(f"sweep q={list(qs)}  largest={[round(x,2) for x in largest]}")
