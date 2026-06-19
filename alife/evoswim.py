"""R103 — Evolving a swimming stroke: a GA finds an efficient gait in a real fluid.

The capstone of the swimming arc. R101 built a lattice-Boltzmann fluid; R102 showed a body with an
undulatory gait self-propels through it. Here evolution gets the wheel: a genetic algorithm searches
the space of gaits — amplitude, frequency, wavelength — and is selected purely on the swim speed that
emerges from the fluid simulation. There is no formula for "good swimming" handed to it; each genome
is judged by actually dropping the swimmer in the fluid and measuring how far it travels. Starting
from random (mostly feeble) gaits, selection climbs to a fast, coordinated stroke that trounces the
random baseline — locomotion discovered, not designed, in real physics.

Each fitness evaluation is a full LBM swim (seconds); keep the population and generations small.
"""

from __future__ import annotations

import numpy as np

from alife.swimmer import simulate, SwimConfig

# genome = [amp, freq, wavelength]; bounds for the GA search
LO = np.array([1.0, 0.0006, 15.0])
HI = np.array([10.0, 0.010, 60.0])
MACH_CAP = 0.08          # gait velocity amp*2pi*freq must stay below the LBM low-Mach limit


def _stabilize(g):
    """Clip a genome into bounds and enforce the low-Mach stability constraint amp*2pi*freq<cap."""
    g = np.clip(g, LO, HI)
    amp, freq, wl = g
    vmax = amp * 2 * np.pi * freq
    if vmax > MACH_CAP:
        freq = MACH_CAP / (amp * 2 * np.pi)
    return np.array([amp, freq, wl])


def gait_speed(genome, nx=150, ny=80, length=44, steps=1800, mass=600.0, seed=0):
    """Fitness = emergent swim speed |net displacement|/steps for a given gait genome."""
    amp, freq, wl = _stabilize(genome)
    cfg = SwimConfig(nx=nx, ny=ny, length=length, thick=3.0, amp=float(amp), wavelength=float(wl),
                     freq=float(freq), mass=mass, steps=steps)
    r = simulate(cfg, seed=seed)
    sp = abs(r["net_disp"]) / steps
    return sp if np.isfinite(sp) else 0.0


def evolve(gens=8, pop=8, elite=2, mut=0.2, seed=0, **kw):
    """GA over gait genomes maximising emergent swim speed. Returns best genome + fitness history."""
    rng = np.random.default_rng(seed)
    population = LO + rng.random((pop, 3)) * (HI - LO)
    best_hist, mean_hist = [], []
    best_g, best_f = None, -1.0
    for _ in range(gens):
        fits = np.array([gait_speed(g, seed=1, **kw) for g in population])
        order = np.argsort(fits)[::-1]
        if fits[order[0]] > best_f:
            best_f = float(fits[order[0]]); best_g = _stabilize(population[order[0]])
        best_hist.append(float(fits[order[0]])); mean_hist.append(float(fits.mean()))
        elites = population[order[:elite]]
        children = [elites[i % elite].copy() for i in range(pop - elite)]
        children = np.array(children) + rng.normal(0, 1, (pop - elite, 3)) * (HI - LO) * mut
        population = np.vstack([elites, np.clip(children, LO, HI)])
    return {"best_genome": best_g, "best_fitness": best_f,
            "best_hist": np.asarray(best_hist), "mean_hist": np.asarray(mean_hist)}


def random_baseline(n=12, seed=0, **kw):
    """Swim speeds of random gaits — the bar evolution must beat (control)."""
    rng = np.random.default_rng(seed)
    return np.array([gait_speed(LO + rng.random(3) * (HI - LO), seed=1, **kw) for _ in range(n)])
