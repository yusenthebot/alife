"""R124 — Complex Ginzburg-Landau: spiral pinwheels and the road to defect turbulence.

One complex field, one universal equation — the amplitude equation every oscillatory medium reduces to
near its onset (chemical BZ reactions, cardiac tissue, fluid convection, lasers, Rayleigh-Benard):

    dA/dt = A + (1 + i b) lap(A) - (1 + i c) |A|^2 A

The phase of A is a colour wheel; wherever the phase winds by a full turn around a point, the amplitude
must vanish (you cannot define a phase at zero) and a TOPOLOGICAL DEFECT sits there — a spiral core.
You can SEE them at a glance: in the phase image every defect is a pinwheel where all hues meet at a
point, and in the amplitude image it is a dark dot. Their charge is exactly +/-1 (the integer winding
number), and on a periodic torus the total charge is always zero (defects are born and die in pairs).

The Benjamin-Feir-Newell line, 1 + b c = 0, splits the behaviour: for 1+bc>0 the medium freezes into a
glassy lattice of slowly-rotating SPIRALS; cross to 1+bc<0 and the spirals destabilise into roiling
DEFECT TURBULENCE, the defect count exploding. Distinct from R88 excitable.py (a discrete Greenberg-
Hastings CA that makes a single spiral) — this is the continuum complex PDE with many interacting
defects. Integrated by a Fourier integrating-factor split-step (diffusion exact, reaction explicit);
pure numpy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CGLEConfig:
    N: int = 220
    b: float = 1.0            # linear dispersion
    c: float = -0.7           # nonlinear dispersion (1 + b c sets the Benjamin-Feir line)
    dt: float = 0.05
    steps: int = 5000
    seed: int = 0


def benjamin_feir(b, c) -> float:
    """1 + b c: > 0 -> frozen spirals (stable), < 0 -> defect turbulence."""
    return 1.0 + b * c


def _expL(cfg: CGLEConfig):
    k = 2.0 * np.pi * np.fft.fftfreq(cfg.N)
    kx, ky = np.meshgrid(k, k)
    return np.exp(-(1.0 + 1j * cfg.b) * (kx ** 2 + ky ** 2) * cfg.dt)


def step(A, expL, cfg: CGLEConfig):
    A = A + cfg.dt * (A - (1.0 + 1j * cfg.c) * np.abs(A) ** 2 * A)   # reaction (explicit)
    return np.fft.ifft2(np.fft.fft2(A) * expL)                       # diffusion (exact in Fourier)


def run(cfg: CGLEConfig, record_every: int = 0):
    rng = np.random.default_rng(cfg.seed)
    A = 0.1 * (rng.standard_normal((cfg.N, cfg.N)) + 1j * rng.standard_normal((cfg.N, cfg.N)))
    expL = _expL(cfg)
    ndef, snaps = [], []
    for t in range(cfg.steps):
        A = step(A, expL, cfg)
        if record_every and (t % record_every == 0 or t == cfg.steps - 1):
            ndef.append(defect_count(A))
            snaps.append(A.copy())
    return {"A": A, "defects": np.asarray(ndef), "snaps": snaps}


def _wrap(d):
    return (d + np.pi) % (2.0 * np.pi) - np.pi


def winding(theta):
    """Topological charge per plaquette = discrete curl of the phase / 2pi (integer at defects)."""
    dr = _wrap(np.roll(theta, -1, 1) - theta)
    du = _wrap(np.roll(theta, -1, 0) - theta)
    return (dr + np.roll(du, -1, 1) - np.roll(dr, -1, 0) - du) / (2.0 * np.pi)


def defect_count(A, periodic: bool = True) -> int:
    w = winding(np.angle(A))
    if not periodic:
        w = w[:-1, :-1]
    return int((np.abs(w) > 0.5).sum())


def net_charge(A, periodic: bool = True) -> int:
    w = winding(np.angle(A))
    if not periodic:
        w = w[:-1, :-1]
    return int(round(w[np.abs(w) > 0.5].sum()))


def defect_curve(cs, cfg: CGLEConfig):
    """Final defect count vs the Benjamin-Feir parameter 1+bc (sweep c at fixed b)."""
    from dataclasses import replace
    bf, nd = [], []
    for c in cs:
        r = run(replace(cfg, c=float(c)))
        bf.append(benjamin_feir(cfg.b, c)); nd.append(defect_count(r["A"]))
    return np.asarray(bf), np.asarray(nd)
