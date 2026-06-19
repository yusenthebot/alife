"""R85 — The Ising model: a phase transition and spontaneous symmetry breaking (Metropolis MC).

The most-studied model in statistical physics, and a gap this project hadn't filled: an
EQUILIBRIUM phase transition (R74's sandpile was self-organized criticality; this is the classic
order-disorder transition). Spins ±1 on a lattice prefer to align with their neighbours
(energy -J s_i s_j), fighting thermal noise at temperature T. Sweep T and a sharp transition
appears at the critical temperature T_c = 2/ln(1+√2) ≈ 2.269 (Onsager, 2D): below T_c the system
spontaneously MAGNETISES — a global direction emerges from a symmetric rule (spontaneous symmetry
breaking) — while above T_c thermal noise wins and order dissolves. At T_c fluctuations span all
scales (critical opalescence) and the susceptibility diverges. Order from local alignment, melted
by temperature.

Vectorized checkerboard Metropolis (the two sublattices don't interact, so each updates in
parallel). Pure numpy/CPU.
"""

from __future__ import annotations

import numpy as np

TC = 2.0 / np.log(1.0 + np.sqrt(2.0))     # Onsager critical temperature ~ 2.269


def _checker(size):
    i, j = np.indices((size, size))
    return (i + j) % 2 == 0


def mc_sweep(s, T, rng, J=1.0):
    """One Metropolis sweep via two checkerboard half-steps (parallel within a sublattice)."""
    even = _checker(s.shape[0])
    for color in (even, ~even):
        nb = (np.roll(s, 1, 0) + np.roll(s, -1, 0) + np.roll(s, 1, 1) + np.roll(s, -1, 1))
        dE = 2.0 * J * s * nb
        accept = color & ((dE <= 0) | (rng.random(s.shape) < np.exp(-dE / T)))
        s[accept] *= -1
    return s


def energy(s, J=1.0):
    """Energy per spin: -J * average bond (sum over right & down neighbours)."""
    bonds = s * (np.roll(s, -1, 0) + np.roll(s, -1, 1))
    return float(-J * bonds.mean())


def run(size=64, T=2.0, sweeps=300, seed=0, start=None, record_every=0):
    rng = np.random.default_rng(seed)
    s = start.copy() if start is not None else np.where(rng.random((size, size)) < 0.5, 1, -1).astype(np.int8)
    mag, snaps = [], {}
    for t in range(sweeps):
        s = mc_sweep(s, T, rng)
        mag.append(float(s.mean()))
        if record_every and (t % record_every == 0 or t == sweeps - 1):
            snaps[t] = s.copy()
    return {"spin": s, "mag": np.array(mag), "snaps": snaps}


def sweep_temperature(size=48, temps=None, equil=300, measure=300, seed=0):
    """For each T: |magnetization|, susceptibility chi = N(<m^2>-<m>^2)/T, and energy/spin.
    Warm-starts from the previous (lower) T's configuration for efficiency."""
    rng = np.random.default_rng(seed)
    temps = np.asarray(temps) if temps is not None else np.linspace(1.2, 3.4, 23)
    n = size * size
    s = np.ones((size, size), dtype=np.int8)         # start ordered (low-T phase)
    absM, chi, en = [], [], []
    for T in temps:
        for _ in range(equil):
            s = mc_sweep(s, T, rng)
        ms, es = [], []
        for _ in range(measure):
            s = mc_sweep(s, T, rng)
            ms.append(s.mean()); es.append(energy(s))
        ms = np.array(ms)
        absM.append(float(np.mean(np.abs(ms))))
        chi.append(float(n * (np.mean(ms ** 2) - np.mean(np.abs(ms)) ** 2) / T))
        en.append(float(np.mean(es)))
    return temps, np.array(absM), np.array(chi), np.array(en)
