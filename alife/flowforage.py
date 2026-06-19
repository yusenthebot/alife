"""R121 — A composed world: chemotactic foragers evolving inside a fluid flow.

The catalog so far is broad but its models stand alone. This round COMPOSES three of them into one
eco-evolutionary world and asks what emerges from the coupling: a fluid FLOW (the R101 lattice-
Boltzmann solver, or an analytic vortex array) advects a population of microswimmers that CHEMOTAX up
a diffusing NUTRIENT field they deplete, gaining energy to reproduce (with mutation) or starving. It
is a toy of ocean plankton: currents stir, cells chase patches of food, and natural selection tunes
their behaviour.

Two emergent results that none of the parts shows alone:
  1. SELECTION of behaviour — the heritable chemotactic sensitivity chi rises over generations when a
     nutrient gradient exists to exploit (depletion makes the field patchy, so chasing the gradient
     pays); with chemotaxis switched off chi is a neutral tag and merely drifts.
  2. PATCHINESS — chemotactic foragers concentrate into patches (index of dispersion >> 1, the random
     baseline), and the FLOW reshapes and stirs those patches (changing patchiness vs the no-flow
     world) — the fluid and the behaviour interact, as in real plankton thin-layers.

Pure numpy; the flow field is pluggable (analytic vortex array, or a cached fluid.py Kármán snapshot).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ForageConfig:
    L: int = 120
    n0: int = 400
    steps: int = 400
    eat: float = 0.5            # max nutrient eaten per step
    metab: float = 0.12         # energy cost per step
    repro: float = 2.0          # energy threshold to reproduce
    chi_gain: float = 8.0       # how strongly chi converts a gradient into motion
    chi_mut: float = 0.06       # mutation std on chi
    chi0_max: float = 3.0       # initial chi ~ U(0, chi0_max)
    noise: float = 0.3          # random swim component
    replenish: float = 0.02     # nutrient regrowth rate toward 1
    diffuse: float = 0.15       # nutrient diffusion
    cap: int = 2600             # population cap (carrying capacity guard)
    chemotaxis: bool = True     # False => chi is a neutral tag (control: no selection)
    seed: int = 0


def _lap(f):
    return np.roll(f, 1, 0) + np.roll(f, -1, 0) + np.roll(f, 1, 1) + np.roll(f, -1, 1) - 4.0 * f


def _grad(f):
    gx = 0.5 * (np.roll(f, -1, 1) - np.roll(f, 1, 1))
    gy = 0.5 * (np.roll(f, -1, 0) - np.roll(f, 1, 0))
    return gx, gy


def vortex_flow(L: int, amp: float = 0.6, k: int = 2):
    """Divergence-free k x k counter-rotating vortex array from a sine stream function."""
    j, i = np.indices((L, L))
    w = 2.0 * np.pi * k / L
    ux = amp * np.sin(w * i) * np.cos(w * j)
    uy = -amp * np.cos(w * i) * np.sin(w * j)
    return ux, uy


def lbm_flow(nx: int = 200, ny: int = 80, steps: int = 9000, u_in: float = 0.1, radius: int = 9):
    """A real fluid.py Kármán-vortex velocity snapshot (the composition showcase)."""
    from alife.fluid import karman
    res = karman(nx=nx, ny=ny, u_in=u_in, radius=radius, steps=steps)
    ux, uy = res["ux"], res["uy"]
    return ux / (np.abs(ux).max() + 1e-9), uy / (np.abs(ux).max() + 1e-9)   # normalise scale


def init(cfg: ForageConfig, rng):
    return {
        "x": rng.uniform(0, cfg.L, cfg.n0),
        "y": rng.uniform(0, cfg.L, cfg.n0),
        "chi": rng.uniform(0, cfg.chi0_max, cfg.n0),
        "E": np.full(cfg.n0, 1.0),
    }


def _sample(field, x, y, L):
    return field[(y.astype(int) % L), (x.astype(int) % L)]


def step(st, N, cfg: ForageConfig, rng, ux=None, uy=None):
    L = cfg.L
    x, y, chi, E = st["x"], st["y"], st["chi"], st["E"]
    gx, gy = _grad(N)
    sx, sy = _sample(gx, x, y, L), _sample(gy, x, y, L)
    drive = cfg.chi_gain * chi if cfg.chemotaxis else 0.0          # control: chi does nothing
    fx = 0.0 if ux is None else _sample(ux, x, y, L)
    fy = 0.0 if uy is None else _sample(uy, x, y, L)
    x = (x + drive * sx + fx + rng.normal(0, cfg.noise, x.size)) % L
    y = (y + drive * sy + fy + rng.normal(0, cfg.noise, y.size)) % L
    ix, iy = x.astype(int) % L, y.astype(int) % L
    eat = np.minimum(cfg.eat, N[iy, ix])
    np.add.at(N, (iy, ix), -eat)
    E = E + eat - cfg.metab
    # reproduce
    born = E > cfg.repro
    nb = int(born.sum())
    if nb:
        E[born] *= 0.5
        x = np.append(x, x[born]); y = np.append(y, y[born]); E = np.append(E, E[born])
        chi = np.append(chi, np.clip(chi[born] + rng.normal(0, cfg.chi_mut, nb), 0, 8))
    # die
    alive = E > 0
    x, y, E, chi = x[alive], y[alive], E[alive], chi[alive]
    if x.size > cfg.cap:
        keep = rng.choice(x.size, cfg.cap, replace=False)
        x, y, E, chi = x[keep], y[keep], E[keep], chi[keep]
    N += cfg.replenish * (1.0 - N) + cfg.diffuse * _lap(N)
    np.maximum(N, 0.0, out=N)                              # nutrient can't go negative
    return {"x": x, "y": y, "chi": chi, "E": E}


def patchiness(x, y, L, bins=24) -> float:
    """Index of dispersion (variance/mean of per-cell counts): ~1 random, >1 clustered into patches."""
    if x.size == 0:
        return 0.0
    h, _, _ = np.histogram2d(x % L, y % L, bins=bins, range=[[0, L], [0, L]])
    m = h.mean()
    return float(h.var() / m) if m > 0 else 0.0


def run(cfg: ForageConfig, flow=None, record_every: int = 0):
    """Run the world. flow = (ux, uy) arrays or None. Returns trait/population/patchiness histories."""
    rng = np.random.default_rng(cfg.seed)
    ux, uy = (flow if flow is not None else (None, None))
    st = init(cfg, rng)
    N = np.ones((cfg.L, cfg.L))
    chi_h, pop_h, patch_h, snaps = [], [], [], []
    for t in range(cfg.steps):
        st = step(st, N, cfg, rng, ux, uy)
        if st["x"].size == 0:
            break
        chi_h.append(float(st["chi"].mean()))
        pop_h.append(st["x"].size)
        patch_h.append(patchiness(st["x"], st["y"], cfg.L))
        if record_every and (t % record_every == 0 or t == cfg.steps - 1):
            snaps.append((st["x"].copy(), st["y"].copy(), st["chi"].copy()))
    return {"chi": np.asarray(chi_h), "pop": np.asarray(pop_h), "patch": np.asarray(patch_h),
            "state": st, "N": N, "snaps": snaps}
