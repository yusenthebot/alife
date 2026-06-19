"""R101 — A real fluid: the D2Q9 lattice-Boltzmann method.

The evolving-rounds project leaves toy dynamics behind here and builds an actual fluid solver. The
lattice-Boltzmann method tracks, at every grid node, nine populations of fictitious particles moving
along nine directions; each step they relax toward local equilibrium (BGK collision) and then stream
to neighbouring nodes. In the continuum limit this recovers the incompressible Navier-Stokes
equations, so the same handful of lines reproduces real flows. We verify it against textbook physics
rather than asserting it works: a force-driven channel must settle into the exact PARABOLIC Poiseuille
profile, and flow past a cylinder at Reynolds ~100 must shed a KÁRMÁN VORTEX STREET — a regular train
of alternating vortices at the right Strouhal number. This solver is the substrate for evolving
swimmers in later rounds.

Vectorized numpy (streaming via np.roll); kinematic viscosity nu=(tau-0.5)/3.
"""

from __future__ import annotations

import numpy as np

# D2Q9 lattice: rest, 4 axial, 4 diagonal
EX = np.array([0, 1, 0, -1, 0, 1, -1, -1, 1])
EY = np.array([0, 0, 1, 0, -1, 1, 1, -1, -1])
W = np.array([4 / 9, 1 / 9, 1 / 9, 1 / 9, 1 / 9, 1 / 36, 1 / 36, 1 / 36, 1 / 36])
OPP = np.array([0, 3, 4, 1, 2, 7, 8, 5, 6])      # opposite direction (bounce-back)


def equilibrium(rho, ux, uy):
    """D2Q9 equilibrium distribution f_i^eq for given density and velocity fields."""
    usq = ux * ux + uy * uy
    feq = np.empty((9,) + rho.shape)
    for i in range(9):
        cu = EX[i] * ux + EY[i] * uy
        feq[i] = W[i] * rho * (1 + 3 * cu + 4.5 * cu * cu - 1.5 * usq)
    return feq


def macroscopic(f):
    rho = f.sum(axis=0)
    ux = (f * EX[:, None, None]).sum(axis=0) / rho
    uy = (f * EY[:, None, None]).sum(axis=0) / rho
    return rho, ux, uy


def _stream(f):
    out = np.empty_like(f)
    for i in range(9):
        out[i] = np.roll(np.roll(f[i], EX[i], axis=0), EY[i], axis=1)
    return out


def poiseuille(nx=40, ny=60, tau=0.8, force=1e-5, steps=8000):
    """Body-force-driven channel flow (periodic x, no-slip top/bottom). Returns the steady ux profile
    across the channel and the analytic parabola for comparison."""
    rho = np.ones((nx, ny))
    f = equilibrium(rho, np.zeros((nx, ny)), np.zeros((nx, ny)))
    wall = np.zeros((nx, ny), bool)
    wall[:, 0] = wall[:, -1] = True
    for _ in range(steps):
        rho, ux, uy = macroscopic(f)
        ux = ux + tau * force / rho                      # body force (velocity-shift forcing)
        feq = equilibrium(rho, ux, uy)
        f = f - (f - feq) / tau
        fb = f.copy()
        f = _stream(f)
        # half-way bounce-back at walls: populations that streamed into a wall reverse
        for i in range(9):
            f[i][wall] = fb[OPP[i]][wall]
    _, ux, _ = macroscopic(f)
    profile = ux[nx // 2, :]
    nu = (tau - 0.5) / 3
    y = np.arange(ny)
    H = ny - 1
    analytic = force / (2 * nu) * (y * (H - y)) / 1.0     # parabola, peak at centre
    return {"profile": profile, "analytic": analytic, "y": y, "nu": nu}


def karman(nx=320, ny=80, tau=0.56, u_in=0.1, radius=9, steps=20000, record_every=0):
    """Flow past a cylinder. Returns final vorticity, a downstream velocity probe time series, and Re."""
    rng = np.random.default_rng(0)
    rho = np.ones((nx, ny))
    cx, cy = nx // 5, ny // 2 + 2                         # slight offset breaks top/bottom symmetry
    X, Y = np.meshgrid(np.arange(nx), np.arange(ny), indexing="ij")
    cyl = (X - cx) ** 2 + (Y - cy) ** 2 < radius ** 2
    ux0 = np.full((nx, ny), u_in) * (1 + 0.02 * rng.standard_normal((nx, ny)))   # seed the instability
    ux0[cyl] = 0
    f = equilibrium(rho, ux0, np.zeros((nx, ny)))
    nu = (tau - 0.5) / 3
    Re = u_in * (2 * radius) / nu
    probe, snaps = [], {}
    for t in range(steps):
        # outlet: zero-gradient (copy 2nd-last column into last for outgoing populations)
        f[[3, 6, 7], -1, :] = f[[3, 6, 7], -2, :]
        rho, ux, uy = macroscopic(f)
        # inlet: impose uniform inflow (Zou/He-lite via equilibrium)
        ux[0, :] = u_in; uy[0, :] = 0; rho[0, :] = 1.0
        feq = equilibrium(rho, ux, uy)
        f[:, 0, :] = feq[:, 0, :]
        f = f - (f - feq) / tau
        fb = f.copy()
        f = _stream(f)
        for i in range(9):                               # bounce-back off the cylinder
            f[i][cyl] = fb[OPP[i]][cyl]
        if t > steps // 2:
            probe.append(uy[cx + 6 * radius if cx + 6 * radius < nx else -1, cy])
        if record_every and (t % record_every == 0 or t == steps - 1):
            snaps[t] = (ux.copy(), uy.copy())
    rho, ux, uy = macroscopic(f)
    vort = _vorticity(ux, uy)
    vort[cyl] = np.nan
    return {"vort": vort, "ux": ux, "uy": uy, "probe": np.asarray(probe), "Re": float(Re),
            "cyl": cyl, "radius": radius, "u_in": u_in, "snaps": snaps}


def _vorticity(ux, uy):
    duy_dx = np.gradient(uy, axis=0)
    dux_dy = np.gradient(ux, axis=1)
    return duy_dx - dux_dy


def strouhal(probe, radius, u_in):
    """Vortex-shedding Strouhal number St = f*D/U from the probe's dominant oscillation frequency."""
    a = probe - probe.mean()
    if a.std() < 1e-9:
        return 0.0
    spec = np.abs(np.fft.rfft(a))
    freqs = np.fft.rfftfreq(len(a))
    spec[0] = 0
    f_peak = freqs[np.argmax(spec)]
    return float(f_peak * (2 * radius) / u_in)
