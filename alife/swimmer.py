"""R102 — A swimmer in a real fluid: self-propulsion from an undulatory gait.

Step two of the swimming arc. We drop a flexible body into the R101 lattice-Boltzmann fluid and give
it a fish/sperm-like travelling-wave gait — the centreline bends as kappa(s,t)=A·(s/L)·sin(2π(s/λ −
f·t)), amplitude growing toward the tail. The body is imposed on the fluid as a moving velocity
source (its cells carry the local body velocity), so each flick of the tail throws fluid backward.
The swimmer is otherwise FREE: with the domain periodic and starting from rest, total momentum is
conserved, so the body's centre-of-mass velocity is exactly minus the fluid momentum over its mass —
the recoil that makes it swim. No part of the swim speed is prescribed; it emerges from the gait.
Turn the gait off (A=0) and the body just sits there. The substrate for evolving a stroke (R103).

Reuses alife.fluid (D2Q9). CPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from alife.fluid import EX, EY, equilibrium, macroscopic, _stream


@dataclass(frozen=True)
class SwimConfig:
    nx: int = 240
    ny: int = 120
    tau: float = 0.6
    length: int = 56          # body length (lattice units)
    thick: float = 3.0        # half-thickness of the body
    amp: float = 7.0          # gait amplitude A (0 = rigid control)
    wavelength: float = 40.0  # gait wavelength lambda
    freq: float = 0.012       # gait frequency f (cycles per step)
    mass: float = 1200.0      # swimmer mass (sets recoil scale)
    steps: int = 5000


def _body_mask_and_vel(cfg, xc, V, t):
    """Body cells (mask) and their target velocity field (ux,uy): swim velocity + lateral gait."""
    ny, nx = cfg.ny, cfg.nx
    yc = ny // 2
    s = np.arange(cfg.length)                                  # arc length along the body (head->tail)
    phase = 2 * np.pi * (s / cfg.wavelength - cfg.freq * t)
    ydisp = cfg.amp * (s / cfg.length) * np.sin(phase)         # lateral centreline displacement
    yvel = -cfg.amp * (s / cfg.length) * np.cos(phase) * 2 * np.pi * cfg.freq  # d/dt of ydisp
    xcells = (xc - s).astype(int)                              # head at xc, body trails in -x
    mask = np.zeros((nx, ny), bool)
    ux_b = np.zeros((nx, ny)); uy_b = np.zeros((nx, ny))
    th = int(np.ceil(cfg.thick))
    for k in range(cfg.length):
        xi = xcells[k] % nx
        yj = int(round(yc + ydisp[k]))
        for dy in range(-th, th + 1):
            yy = yj + dy
            if 0 <= yy < ny:
                mask[xi, yy] = True
                ux_b[xi, yy] = V                              # axial: moves with the swimmer
                uy_b[xi, yy] = yvel[k]                        # lateral: the gait
    return mask, ux_b, uy_b


def simulate(cfg=SwimConfig(), seed=0, record_every=0):
    """Free-swim the body; return centre-of-mass trajectory, net displacement, snapshots."""
    nx, ny = cfg.nx, cfg.ny
    rho = np.ones((nx, ny))
    f = equilibrium(rho, np.zeros((nx, ny)), np.zeros((nx, ny)))
    xc = float(nx * 0.7)                                       # start near the right, swim left
    V = 0.0
    xc_hist, snaps = [xc], {}
    for t in range(cfg.steps):
        mask, ux_b, uy_b = _body_mask_and_vel(cfg, xc, V, t)
        rho, ux, uy = macroscopic(f)
        feq = equilibrium(rho, ux, uy)
        f = f - (f - feq) / cfg.tau                           # BGK collide
        # impose body as a moving velocity source (no-slip-ish): body cells -> equilibrium at body vel
        bf = equilibrium(rho, ux_b, uy_b)
        f[:, mask] = bf[:, mask]
        f = _stream(f)
        # recoil from momentum conservation (periodic box, started from rest)
        rho, ux, uy = macroscopic(f)
        fluid = ~mask
        Px = float((rho * ux)[fluid].sum())
        V = -Px / cfg.mass
        xc = xc + V
        xc_hist.append(xc)
        if record_every and (t % record_every == 0 or t == cfg.steps - 1):
            snaps[t] = (mask.copy(), ux.copy(), uy.copy(), xc)
    xc_hist = np.asarray(xc_hist)
    return {"xc": xc_hist, "net_disp": float(xc_hist[-1] - xc_hist[0]), "snaps": snaps,
            "speed": float((xc_hist[-1] - xc_hist[0]) / cfg.steps)}
