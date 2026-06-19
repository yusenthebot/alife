"""R113 — The Ising model in 3D: dimensionality lifts the critical temperature.

R85 built the 2D Ising model and found Onsager's exact transition at T_c = 2/ln(1+sqrt2) ~ 2.269.
But that number is not universal — it depends on the DIMENSION of the lattice, through one quantity:
the coordination number z (how many neighbours each spin has). In 2D a spin has z=4 neighbours; in
3D it has z=6. More aligning bonds per spin means order resists thermal noise to a HIGHER temperature,
so the 3D Ising model orders all the way up to T_c ~ 4.5115 (no closed form exists in 3D — this is a
numerical value) versus 2.269 in 2D. Mean-field theory makes the mechanism explicit: it predicts
T_c = z (in units of J/k_B), i.e. 4 and 6 — overestimating both (it ignores fluctuations, worst in
low dimension) but capturing the dimension trend exactly. The critical EXPONENTS change too (3D Ising
beta ~ 0.326 vs the 2D exact 1/8), because fluctuations matter less as dimension rises.

This module is the 3D analogue of R85: a vectorised checkerboard Metropolis on an L^3 cubic lattice
(the parity (i+j+k) mod 2 splits the lattice into two interpenetrating sublattices whose 6 neighbours
are all the opposite colour, so each sublattice updates in parallel). It locates T_c three ways —
the magnetisation collapse, the susceptibility peak, and the size-independent Binder-cumulant crossing
— and contrasts every number with the 2D model. Pure numpy/CPU.
"""

from __future__ import annotations

import numpy as np

TC2D = 2.0 / np.log(1.0 + np.sqrt(2.0))     # Onsager 2D, z=4  (~2.269)
TC3D = 4.5115                                # numerical 3D,  z=6  (no closed form)


def mean_field_tc(z: int) -> float:
    """Mean-field prediction T_c = z*J/k_B — overestimates (ignores fluctuations) but gets the trend."""
    return float(z)


def _checker3d(L):
    i, j, k = np.indices((L, L, L))
    return (i + j + k) % 2 == 0


def _neighbour_sum(s):
    return (np.roll(s, 1, 0) + np.roll(s, -1, 0) + np.roll(s, 1, 1)
            + np.roll(s, -1, 1) + np.roll(s, 1, 2) + np.roll(s, -1, 2))


def mc_sweep(s, T, rng, J=1.0):
    """One Metropolis sweep via two checkerboard half-steps (each sublattice updates in parallel)."""
    chk = _checker3d(s.shape[0])
    for color in (True, False):
        dE = 2.0 * J * s * _neighbour_sum(s)
        accept = rng.random(s.shape) < np.exp(-dE / T)      # dE<0 => exp>1 => always accept
        flip = (chk == color) & accept
        s[flip] *= -1
    return s


def magnetization(s) -> float:
    return float(abs(s.mean()))


def energy(s, J=1.0) -> float:
    """Energy per spin (each bond counted once: 3 forward neighbours per site in 3D)."""
    bonds = s * (np.roll(s, -1, 0) + np.roll(s, -1, 1) + np.roll(s, -1, 2))
    return float(-J * bonds.mean())


def run(L=16, T=4.0, sweeps=400, seed=0, start=None, record_every=0):
    """Equilibrate an L^3 lattice at temperature T. Returns final spins and the |m| trace."""
    rng = np.random.default_rng(seed)
    s = start.copy() if start is not None else rng.choice([-1, 1], (L, L, L)).astype(np.int8)
    mag, snaps = [], {}
    for t in range(sweeps):
        mc_sweep(s, T, rng)
        mag.append(magnetization(s))
        if record_every and (t % record_every == 0 or t == sweeps - 1):
            snaps[t] = s.copy()
    return {"spins": s, "mag": np.asarray(mag), "snaps": snaps}


def sweep_temperature(L=16, temps=None, equil=400, measure=400, seed=0):
    """Sweep T (warm-started downward through the transition). Returns |m|, susceptibility, Binder U."""
    if temps is None:
        temps = np.linspace(5.5, 3.5, 16)
    temps = np.asarray(temps, float)
    rng = np.random.default_rng(seed)
    N = L ** 3
    s = rng.choice([-1, 1], (L, L, L)).astype(np.int8)
    M, CHI, U = [], [], []
    for T in temps:
        for _ in range(equil):
            mc_sweep(s, T, rng)
        m1 = m2 = m4 = 0.0
        for _ in range(measure):
            mc_sweep(s, T, rng)
            m = abs(s.mean())
            m1 += m; m2 += m * m; m4 += m ** 4
        m1 /= measure; m2 /= measure; m4 /= measure
        M.append(m1)
        CHI.append(N * (m2 - m1 * m1) / T)
        U.append(1.0 - m4 / (3.0 * m2 * m2))
    return {"T": temps, "M": np.asarray(M), "chi": np.asarray(CHI), "binder": np.asarray(U)}


def locate_tc(temps, chi) -> float:
    """Finite-size T_c estimate = temperature of the susceptibility peak."""
    return float(np.asarray(temps)[int(np.argmax(chi))])


def binder_crossing(temps, U_small, U_large) -> float:
    """T_c from the size-independent Binder-cumulant crossing of two lattice sizes (interpolated)."""
    t = np.asarray(temps, float)
    d = np.asarray(U_small, float) - np.asarray(U_large, float)
    order = np.argsort(t)
    t, d = t[order], d[order]
    sign = np.sign(d)
    idx = np.where(np.diff(sign) != 0)[0]
    if idx.size == 0:
        return float(t[np.argmin(np.abs(d))])
    i = idx[0]
    # linear interpolation of the zero crossing of (U_small - U_large)
    return float(t[i] - d[i] * (t[i + 1] - t[i]) / (d[i + 1] - d[i]))
