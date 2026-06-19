"""R115 — Chimera states: identical oscillators that split into order and chaos at once.

Take a ring of IDENTICAL phase oscillators, coupled symmetrically — each to its neighbours through a
smooth NONLOCAL kernel — with a small phase lag. Intuition says the only outcomes are global
synchrony or global incoherence. Kuramoto & Battogtokh (2002) found a third, impossible-looking one:
the ring spontaneously breaks into two coexisting domains — one where the oscillators are phase-locked
and coherent, and right next to it one where they drift incoherently — and this split PERSISTS. Abrams
& Strogatz named it a chimera, after the mythical part-lion-part-serpent beast, because coherence and
incoherence live in one homogeneous system at the same time. Nothing in the equations distinguishes
the two regions; the symmetry is broken by the dynamics alone. Chimeras have since been seen in
chemical, optical, mechanical and neural systems, and are a candidate picture of unihemispheric sleep
(half a brain asleep, half awake).

Model (ring, nonlocal kernel G, phase lag alpha):
    d(theta_i)/dt = omega - sum_j G(i-j) * sin(theta_i - theta_j + alpha)

Distinct from R-kuramoto (all-to-all -> only global sync) and explosive sync: the chimera needs (a) a
NONLOCAL kernel (not global, not nearest-neighbour) and (b) alpha just below pi/2. The coupling sum is
a circular convolution, evaluated by FFT (O(N log N)). Pure numpy/CPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ChimeraConfig:
    N: int = 256
    kappa: float = 4.0       # kernel decay rate (large=local, ~0=global all-to-all)
    alpha: float = 1.46      # phase lag (chimeras live just below pi/2 ~ 1.5708)
    omega: float = 0.0       # identical natural frequency (work in the rotating frame)
    dt: float = 0.05
    steps: int = 4000
    seed: int = 0
    global_coupling: bool = False   # control: flat kernel (all-to-all) -> no chimera


def kernel(cfg: ChimeraConfig):
    """Normalised circular coupling kernel G(m). Exponential (Kuramoto-Battogtokh) or flat (control)."""
    m = np.arange(cfg.N)
    d = np.minimum(m, cfg.N - m) / cfg.N            # circular distance in [0, 0.5]
    g = np.ones(cfg.N) if cfg.global_coupling else np.exp(-cfg.kappa * d)
    return g / g.sum()


def _circ_conv(f, ghat):
    return np.fft.ifft(np.fft.fft(f) * ghat).real


def init_phases(cfg: ChimeraConfig):
    """A localized random perturbation seeds the chimera basin (coherent elsewhere, scrambled in a bump)."""
    rng = np.random.default_rng(cfg.seed)
    x = np.arange(cfg.N)
    theta = 6.0 * np.exp(-0.5 * ((x - cfg.N / 2) / (cfg.N * 0.07)) ** 2) * rng.standard_normal(cfg.N)
    return theta % (2 * np.pi)


def step(theta, cfg: ChimeraConfig, ghat):
    c = _circ_conv(np.cos(theta), ghat)
    s = _circ_conv(np.sin(theta), ghat)
    coupling = np.sin(theta + cfg.alpha) * c - np.cos(theta + cfg.alpha) * s
    return theta + cfg.dt * (cfg.omega - coupling)


def run(cfg: ChimeraConfig, record_every: int = 0):
    """Integrate the ring. Returns final phases plus snapshots for the space-time view."""
    theta = init_phases(cfg)
    ghat = np.fft.fft(kernel(cfg))
    snaps = []
    for t in range(cfg.steps):
        theta = step(theta, cfg, ghat)
        if record_every and (t % record_every == 0 or t == cfg.steps - 1):
            snaps.append((theta % (2 * np.pi)).copy())
    return {"theta": theta % (2 * np.pi), "snaps": np.asarray(snaps) if snaps else None}


def local_order(theta, width_frac: float = 0.04):
    """Local Kuramoto order parameter R_i over a Gaussian window: ~1 where coherent, <1 where incoherent."""
    N = theta.size
    m = np.arange(N)
    d = np.minimum(m, N - m) / N
    w = np.exp(-0.5 * (d / width_frac) ** 2)
    w /= w.sum()
    what = np.fft.fft(w)
    z = _circ_conv(np.cos(theta), what) + 1j * _circ_conv(np.sin(theta), what)
    return np.abs(z)


def global_order(theta) -> float:
    return float(np.abs(np.mean(np.exp(1j * theta))))


def is_chimera(theta, hi: float = 0.9, lo: float = 0.7) -> bool:
    """True if the ring holds BOTH a coherent region (max R>hi) and an incoherent one (min R<lo)."""
    R = local_order(theta)
    return bool(R.max() > hi and R.min() < lo)


def coherent_fraction(theta, thresh: float = 0.85) -> float:
    return float((local_order(theta) > thresh).mean())
