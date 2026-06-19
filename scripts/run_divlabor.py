"""R89 figure — the evolution of division of labor: convexity drives specialisation (Jensen)."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.divlabor import evolve, sweep_alpha, jensen_prediction

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r89_divlabor")
os.makedirs(OUT, exist_ok=True)

conv = evolve(alpha=3.0, gens=220, seed=1)
conc = evolve(alpha=0.5, gens=220, seed=1)
alphas, spec = sweep_alpha(np.linspace(0.4, 3.0, 14), gens=160, seed=10)

fig = plt.figure(figsize=(15, 4.6), facecolor="white")

# A. evolved effort distribution: bimodal castes vs unimodal generalists
axH = fig.add_subplot(1, 3, 1)
bins = np.linspace(0, 1, 26)
axH.hist(conv["final_thetas"], bins=bins, color="#1f77b4", alpha=0.8,
         label=f"convex α=3 (spec={conv['final_spec']:.2f})")
axH.hist(conc["final_thetas"], bins=bins, color="#e6862a", alpha=0.7,
         label=f"concave α=0.5 (spec={conc['final_spec']:.2f})")
axH.set_xlabel("evolved effort split  θ  (0 = task B only, 1 = task A only)")
axH.set_ylabel("members")
axH.set_title("Castes emerge under accelerating returns", fontsize=10.5)
axH.legend(fontsize=8)

# B. the transition: specialization vs convexity, threshold at alpha=1 (Jensen)
axS = fig.add_subplot(1, 3, 2)
axS.plot(alphas, spec, "o-", color="#2a9d8f")
axS.axvline(1.0, color="crimson", ls="--", lw=1)
axS.text(1.04, 0.05, "α=1\n(Jensen threshold)", color="crimson", fontsize=8.5)
axS.text(0.5, 0.85, "diminishing\nreturns →\ngeneralists", fontsize=8.5, color="#a0522d")
axS.text(2.2, 0.15, "accelerating\nreturns →\nspecialists", fontsize=8.5, color="#1f5f8b")
axS.set_xlabel("convexity  α  of task function g(x)=xᵅ")
axS.set_ylabel("evolved specialization index")
axS.set_title("Division of labor evolves iff returns accelerate", fontsize=10.5)
axS.grid(alpha=0.3)

# C. productivity + specialization over evolutionary time
axP = fig.add_subplot(1, 3, 3)
g = np.arange(len(conv["prod"]))
axP.plot(g, conv["prod"] / conv["prod"][0], color="#1f77b4", label="convex: productivity (×start)")
axP.plot(g, conc["prod"] / conc["prod"][0], color="#e6862a", label="concave: productivity (×start)")
axP.plot(g, conv["spec"], color="#1f77b4", ls=":", label="convex: specialization")
axP.plot(g, conc["spec"], color="#e6862a", ls=":", label="concave: specialization")
axP.set_xlabel("generation"); axP.set_ylabel("value")
axP.set_title("Convex: specialization rises, productivity ~3×", fontsize=10.5)
axP.legend(fontsize=7.5, loc="center right"); axP.grid(alpha=0.3)

fig.suptitle("R89 · A major transition — the evolution of division of labor (Jensen: specialise iff returns accelerate)",
             fontsize=12.5, y=1.0)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path = os.path.join(OUT, "divlabor.png")
fig.savefig(path, dpi=110, bbox_inches="tight")
print("saved", path)
# verify the sweep crosses where Jensen predicts
cross = alphas[np.argmax(spec > 0.5)]
print(f"spec index crosses 0.5 near alpha={cross:.2f} (Jensen threshold = 1.0)")
print(f"convex final spec={conv['final_spec']:.2f} prod x{conv['prod'][-1]/conv['prod'][0]:.2f}  "
      f"concave final spec={conc['final_spec']:.2f} prod x{conc['prod'][-1]/conc['prod'][0]:.2f}")
