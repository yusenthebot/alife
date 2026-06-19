"""R114 — Somitogenesis: the clock-and-wavefront turns a tempo into a body plan.

Vertebrae, ribs, the repeated blocks of muscle down a fish — the body is segmented, and the segments
(somites) are laid down one pair at a time, rhythmically, from head to tail during development. Cooke
& Zeeman (1976) proposed the mechanism, now confirmed molecularly (her1/her7 in zebrafish, Hes7 in
mouse): every cell in the presomitic mesoderm (PSM) runs a genetic OSCILLATOR — a clock — and a
determination WAVEFRONT sweeps slowly along the axis. While a cell is behind the front it keeps
oscillating; the instant the front passes, the cell's clock phase is FROZEN, committing it to a
position within a segment. Because the clock keeps ticking as the front recedes, successive bands of
cells freeze at successive phases, and a periodic pattern of somites crystallises out of a purely
TEMPORAL rhythm. The geometry is forced: one somite is laid down per clock period, so

    somite size  =  (wavefront speed) x (clock period)  =  2*pi * v / omega.

This is a different route to spatial pattern from Turing's reaction-diffusion (R45/gierermeinhardt) —
there is no diffusion-driven instability and no self-selected wavelength; the wavelength is SET by a
clock and a moving boundary. With a posterior-to-anterior frequency gradient the PSM also shows the
travelling "kinematic" phase waves seen in real embryos, sweeping forward and arresting at the front.
Pure numpy/CPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

TWO_PI = 2.0 * np.pi


@dataclass(frozen=True)
class SomiteConfig:
    N: int = 200             # cells along the anterior(0)->posterior(N) axis
    omega: float = 1.0       # base clock angular frequency (rad / time)
    v: float = 2.5           # wavefront speed (cells / time); front position = v*t
    grad: float = 0.0        # posterior frequency gradient: omega_i = omega*(1 + grad*i/N)
    coupling: float = 0.0    # optional local phase coupling (smooths kinematic waves)
    dt: float = 0.02
    seed: int = 0
    noise: float = 0.0       # phase noise on the oscillators


def frequencies(cfg: SomiteConfig):
    return cfg.omega * (1.0 + cfg.grad * np.arange(cfg.N) / cfg.N)


def predict_somite_size(cfg: SomiteConfig) -> float:
    """Clock-and-wavefront law (uniform clock): one somite per period -> size = 2*pi*v/omega cells."""
    return TWO_PI * cfg.v / cfg.omega


def run(cfg: SomiteConfig, record: bool = False):
    """Integrate the PSM clocks while the front recedes, freezing each cell's phase as it passes.

    Returns the per-cell frozen phase, and (if record) a phase-field kymograph over time."""
    rng = np.random.default_rng(cfg.seed)
    omega = frequencies(cfg)
    theta = cfg.noise * rng.standard_normal(cfg.N)        # PSM starts ~in phase (head end)
    idx = np.arange(cfg.N)
    frozen = np.zeros(cfg.N, bool)
    frozen_phase = np.full(cfg.N, np.nan)
    steps = int(np.ceil(cfg.N / cfg.v / cfg.dt)) + 1       # run until the front clears the axis
    kymo = []
    for t in range(steps):
        front = cfg.v * t * cfg.dt
        newly = (~frozen) & (idx < front)
        frozen_phase[newly] = theta[newly]
        frozen[newly] = True
        live = ~frozen
        dtheta = omega.copy()
        if cfg.coupling and live.any():
            lap = np.roll(theta, 1) + np.roll(theta, -1) - 2.0 * theta
            dtheta = dtheta + cfg.coupling * np.sin(lap)
        theta[live] += cfg.dt * dtheta[live]
        if record:
            disp = np.where(frozen, frozen_phase, theta)
            kymo.append(disp.copy())
    frozen_phase[~frozen] = theta[~frozen]                 # freeze any remainder
    return {"frozen_phase": frozen_phase, "omega": omega,
            "kymo": np.asarray(kymo) if record else None, "steps": steps}


def somite_ids(frozen_phase):
    """Integer somite label per cell = how many full clock cycles the frozen phase has advanced."""
    phi = np.asarray(frozen_phase, float)
    return np.floor((phi - np.nanmin(phi)) / TWO_PI).astype(int)


def somite_boundaries(frozen_phase):
    return np.where(np.diff(somite_ids(frozen_phase)) != 0)[0] + 1


def somite_sizes(frozen_phase):
    b = somite_boundaries(frozen_phase)
    edges = np.concatenate(([0], b, [len(frozen_phase)]))
    return np.diff(edges)


def mean_somite_size(frozen_phase) -> float:
    """Mean interior somite size (drops the partial first/last blocks at the axis ends)."""
    sizes = somite_sizes(frozen_phase)
    interior = sizes[1:-1] if sizes.size > 2 else sizes
    return float(np.mean(interior))


def n_somites(frozen_phase) -> int:
    return int(somite_boundaries(frozen_phase).size + 1)
