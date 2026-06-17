"""Red Queen dynamics — host-parasite coevolution that never settles.

A matching-allele model: a parasite of type i infects a host of type i. So common
host types are hunted down (their matching parasite thrives), giving RARE host
types an advantage — negative frequency-dependent selection. Hosts flee toward
whatever allele is rare; parasites chase. Neither wins: allele frequencies
oscillate forever, with the parasites lagging the hosts. "It takes all the running
you can do, to keep in the same place."
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class RedQueenConfig:
    k: int = 4               # number of allele types
    generations: int = 600
    s_host: float = 0.9      # how much a matching parasite hurts a host
    s_para: float = 0.9      # how much a matching host helps a parasite
    mut: float = 0.01        # drift toward uniform (prevents fixation/loss)


def evolve(cfg: RedQueenConfig, seed: int = 0):
    rng = np.random.default_rng(seed)
    host = rng.dirichlet(np.ones(cfg.k))
    para = rng.dirichlet(np.ones(cfg.k))
    H, P = [host.copy()], [para.copy()]
    for _ in range(cfg.generations):
        w_host = 1.0 - cfg.s_host * para          # common matching parasite hurts host type
        w_para = 0.1 + cfg.s_para * host          # matching host helps parasite type
        host = host * w_host
        host = host / host.sum()
        para = para * w_para
        para = para / para.sum()
        u = np.ones(cfg.k) / cfg.k
        host = (1 - cfg.mut) * host + cfg.mut * u  # mutation/drift
        para = (1 - cfg.mut) * para + cfg.mut * u
        H.append(host.copy()); P.append(para.copy())
    return np.array(H), np.array(P)


def oscillation_strength(freqs: np.ndarray, burn: int = 100) -> float:
    """Std of an allele frequency after burn-in — >0 means sustained oscillation
    (a converged equilibrium would have ~0)."""
    return float(freqs[burn:, 0].std())


def host_parasite_lag(H: np.ndarray, P: np.ndarray, allele: int = 0, max_lag: int = 60, burn: int = 100) -> int:
    """Lag (generations) at which parasite freq best matches past host freq —
    positive => parasites track/chase hosts (the Red Queen signature)."""
    h = H[burn:, allele] - H[burn:, allele].mean()
    p = P[burn:, allele] - P[burn:, allele].mean()
    best_lag, best = 0, -np.inf
    for lag in range(0, max_lag):
        if lag >= h.size:
            break
        c = np.corrcoef(h[: h.size - lag], p[lag:])[0, 1]
        if c > best:
            best, best_lag = c, lag
    return best_lag
