"""R135 — Faraday waves: a vibrated fluid surface erupts into a standing-wave lattice.

Shake a dish of liquid up and down and, above a critical amplitude, the flat surface spontaneously
breaks into a regular lattice of standing waves (Faraday 1831). Two fingerprints make it unmistakable:
(1) PARAMETRIC onset — nothing happens until the drive passes a threshold, then a pattern grows from
noise; (2) the SUBHARMONIC response — the surface oscillates at HALF the drive frequency (the waves
flip sign once per drive period, completing a cycle every two), the signature of parametric resonance.
The wavelength is not arbitrary: the drive at frequency Ω excites the mode whose natural frequency is
Ω/2, so the selected wavenumber k* solves the gravity-capillary dispersion ω0(k*) = Ω/2 — shake faster
and the pattern gets FINER.

Model: the free surface height h(x,y,t) as a spectral field. Each Fourier mode is a parametrically
forced, damped oscillator (a damped Mathieu equation) — vertical vibration modulates effective gravity
g -> g - a cos(Ωt), so the linear stiffness is (g - a cos Ωt)|k| + σ|k|^3 (gravity-capillary
dispersion, deep-water). A real-space cubic term -β h^3 saturates the growth into a finite-amplitude
pattern. Second-order-in-time symplectic-Euler integration. numpy FFT only.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FaradayConfig:
    N: int = 96
    Lx: float = 37.699111843  # 2*pi*6 -> dk = 2*pi/Lx
    g: float = 1.0            # gravity
    sigma: float = 1.0        # surface tension / density
    gamma: float = 0.05       # viscous damping
    a: float = 2.0            # vertical forcing acceleration amplitude
    Omega: float = 6.32455532  # drive angular frequency (= 2*w0(k=2) by default -> k* = 2)
    beta: float = 4.0         # cubic saturation
    dt: float = 0.004
    steps: int = 12000
    noise: float = 1e-3
    seed: int = 0


def w0(k, cfg: FaradayConfig):
    """Gravity-capillary dispersion: natural angular frequency of a free surface mode |k|."""
    return np.sqrt(cfg.g * k + cfg.sigma * k ** 3)


def resonant_k(cfg: FaradayConfig) -> float:
    """The wavenumber the drive selects: w0(k*) = Omega/2  ->  sigma k^3 + g k - (Omega/2)^2 = 0."""
    target = (cfg.Omega / 2.0) ** 2
    roots = np.roots([cfg.sigma, 0.0, cfg.g, -target])
    real = [r.real for r in roots if abs(r.imag) < 1e-9 and r.real > 0]
    return float(real[0])


def _grids(cfg: FaradayConfig):
    kx = np.fft.fftfreq(cfg.N, d=cfg.Lx / cfg.N) * 2 * np.pi
    KX, KY = np.meshgrid(kx, kx, indexing="ij")
    return kx, np.hypot(KX, KY)


def run(cfg: FaradayConfig, sample_every: int = 0, record_every: int = 0):
    """Integrate the parametric surface. Returns final field, rms-vs-time, optional point series + snaps."""
    rng = np.random.default_rng(cfg.seed)
    _, K = _grids(cfg)
    hh = np.fft.fft2(rng.normal(0, cfg.noise, (cfg.N, cfg.N)))
    hth = np.zeros((cfg.N, cfg.N), dtype=complex)
    cap = cfg.g * K + cfg.sigma * K ** 3          # the unforced stiffness w0(k)^2
    t = 0.0
    rms, series, ts, snaps = [], [], [], []
    for s in range(cfg.steps):
        lop = cap - cfg.a * np.cos(cfg.Omega * t) * K   # (g - a cos Ωt)|k| + σ|k|^3
        h = np.real(np.fft.ifft2(hh))
        acc = -2 * cfg.gamma * hth - lop * hh - np.fft.fft2(cfg.beta * h ** 3)
        hth = hth + cfg.dt * acc
        hh = hh + cfg.dt * hth
        t += cfg.dt
        if s % 20 == 0:
            rms.append(float(np.sqrt((np.real(np.fft.ifft2(hh)) ** 2).mean())))
        if sample_every and s % sample_every == 0:
            series.append(float(np.real(np.fft.ifft2(hh))[cfg.N // 4, cfg.N // 4])); ts.append(t)
        if record_every and s % record_every == 0:
            snaps.append(np.real(np.fft.ifft2(hh)).copy())
    field = np.real(np.fft.ifft2(hh))
    return {"field": field, "rms": np.asarray(rms), "series": np.asarray(series),
            "ts": np.asarray(ts), "snaps": snaps, "K": K}


def dominant_k(field, cfg: FaradayConfig) -> float:
    """Wavenumber |k| with the most spectral power (excluding the DC component)."""
    _, K = _grids(cfg)
    P = np.abs(np.fft.fft2(field)); P.flat[0] = 0.0
    return float(K.flat[int(np.argmax(P))])


def subharmonic_peak(series, ts) -> float:
    """Dominant angular frequency of a point time-series (use the post-saturation tail)."""
    half = len(series) // 2
    s = series[half:] - series[half:].mean()
    dt = float(ts[1] - ts[0])
    F = np.abs(np.fft.rfft(s * np.hanning(len(s))))
    fr = np.fft.rfftfreq(len(s), d=dt) * 2 * np.pi
    return float(fr[1 + int(np.argmax(F[1:]))])
