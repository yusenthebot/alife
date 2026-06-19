"""R101 figure — lattice-Boltzmann fluid verified: Poiseuille profile + Karman vortex street."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.fluid import poiseuille, karman, strouhal

OUT = os.path.join(os.path.dirname(__file__), "..", "runs", "r101_fluid")
os.makedirs(OUT, exist_ok=True)

# --- Poiseuille (fast) ---
po = poiseuille(nx=20, ny=60, tau=0.8, force=1e-5, steps=6000)
p, a, y = po["profile"], po["analytic"], po["y"]
shape_rmse = float(np.sqrt(np.mean((p / p.max() - a / a.max()) ** 2)))

# --- Karman (cache; ~35s) ---
cache = os.path.join(OUT, "karman.npz")
if os.path.exists(cache):
    z = np.load(cache)
    vort, probe, Re, St = z["vort"], z["probe"], float(z["Re"]), float(z["St"])
else:
    k = karman(nx=320, ny=80, tau=0.55, u_in=0.1, radius=9, steps=16000)
    vort, probe, Re = k["vort"], k["probe"], k["Re"]
    St = strouhal(probe, k["radius"], k["u_in"])
    np.savez(cache, vort=vort, probe=probe, Re=Re, St=St)

fig = plt.figure(figsize=(15, 7.6), facecolor="white")

# A. Poiseuille parabola
axA = fig.add_subplot(2, 2, 1)
axA.plot(p, y, "o", color="#1f77b4", ms=4, label="LBM")
axA.plot(a / a.max() * p.max(), y, "-", color="#e76f51", lw=1.5, label="analytic parabola")
axA.set_xlabel("velocity uₓ"); axA.set_ylabel("channel position y")
axA.set_title(f"Poiseuille flow → parabolic profile\n(shape RMSE {shape_rmse:.3f})", fontsize=10.5)
axA.legend(fontsize=9); axA.grid(alpha=0.3)

# B. Karman vorticity field (the showpiece)
axB = fig.add_subplot(2, 1, 2) if False else fig.add_subplot(2, 2, (3, 4))
vlim = np.nanpercentile(np.abs(vort), 99)
im = axB.imshow(vort.T, origin="lower", cmap="RdBu_r", vmin=-vlim, vmax=vlim, aspect="equal")
axB.set_title(f"Kármán vortex street behind a cylinder — Re={Re:.0f}, Strouhal St={St:.2f} "
              f"(alternating vortices shed in a regular train)", fontsize=10.5)
axB.set_xticks([]); axB.set_yticks([])

# C. probe time series (shedding oscillation)
axC = fig.add_subplot(2, 2, 2)
axC.plot(probe, color="#264653", lw=0.9)
axC.set_xlabel("time step (steady-state window)"); axC.set_ylabel("transverse velocity u_y at wake probe")
axC.set_title(f"Periodic vortex shedding (St={St:.2f})", fontsize=10.5)
axC.grid(alpha=0.3)

fig.suptitle("R101 · A real fluid (lattice-Boltzmann D2Q9) — verified against textbook flows",
             fontsize=13, y=1.0)
fig.tight_layout(rect=[0, 0, 1, 0.96])
path = os.path.join(OUT, "fluid.png")
fig.savefig(path, dpi=110, bbox_inches="tight")
print("saved", path)
print(f"Poiseuille shape RMSE={shape_rmse:.4f} peak ratio={p.max()/a.max():.2f}  Karman Re={Re:.0f} St={St:.3f}")
