"""R45 — morphogenesis: patterns (and self-dividing spots) from two chemicals.

Turing's idea (1952): a uniform mix of two diffusing, reacting chemicals can
spontaneously break symmetry into stable patterns — the chemical basis of spots,
stripes and segmentation in living things. The Gray-Scott reaction-diffusion
system makes this vivid: depending on just two parameters (feed F, kill k) the
same equations grow stripes, mazes, coral, travelling waves — and, in one famous
regime, spots that grow and DIVIDE like cells (mitosis), an inorganic echo of
self-replication.

    dU/dt = Du ∇²U − U V² + F (1 − U)
    dV/dt = Dv ∇²V + U V² − (F + k) V

No genomes, no selection — just local chemistry and diffusion producing life-like
form. This is the self-organization half of artificial life.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# named Gray-Scott regimes (Pearson 1993 classification)
REGIMES = {
    "mitosis": (0.0367, 0.0649),    # spots that grow and divide
    "coral":   (0.0545, 0.0620),    # branching maze / coral
    "stripes": (0.0220, 0.0510),    # fingerprints / labyrinth
    "waves":   (0.0140, 0.0450),    # travelling waves
}


@dataclass(frozen=True)
class ReactionDiffConfig:
    size: int = 200
    du: float = 0.16
    dv: float = 0.08
    dt: float = 1.0
    steps: int = 9000
    seed_blocks: int = 25        # random square seeds of V to start (more -> fills faster)


def _laplacian(a: np.ndarray) -> np.ndarray:
    """9-point weighted Laplacian, periodic boundaries."""
    return (
        0.20 * (np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1))
        + 0.05 * (np.roll(np.roll(a, 1, 0), 1, 1) + np.roll(np.roll(a, 1, 0), -1, 1)
                  + np.roll(np.roll(a, -1, 0), 1, 1) + np.roll(np.roll(a, -1, 0), -1, 1))
        - a
    )


def run(F: float, k: float, cfg: ReactionDiffConfig, seed: int = 0, record_every: int = 0):
    rng = np.random.default_rng(seed)
    n = cfg.size
    U = np.ones((n, n)); V = np.zeros((n, n))
    # seed a few small blocks of V (the perturbation that breaks symmetry)
    for _ in range(cfg.seed_blocks):
        x, y = rng.integers(0, n - 6, 2)
        U[x:x + 6, y:y + 6] = 0.50
        V[x:x + 6, y:y + 6] = 0.25
    snaps = {}
    for t in range(cfg.steps):
        uvv = U * V * V
        U += (cfg.du * _laplacian(U) - uvv + F * (1.0 - U)) * cfg.dt
        V += (cfg.dv * _laplacian(V) + uvv - (F + k) * V) * cfg.dt
        np.clip(U, 0.0, 1.0, out=U); np.clip(V, 0.0, 1.0, out=V)
        if record_every and t % record_every == 0:
            snaps[t] = V.copy()
    return {"U": U, "V": V, "snaps": snaps}


def run_regime(name: str, cfg: ReactionDiffConfig, seed: int = 0, **kw):
    F, k = REGIMES[name]
    return run(F, k, cfg, seed=seed, **kw)


def pattern_strength(V: np.ndarray) -> float:
    """Spatial structure: std of the V field (0 = uniform, high = patterned)."""
    return float(V.std())
