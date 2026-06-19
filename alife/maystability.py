"""R116 — May's complexity-stability theorem: why bigger ecosystems are HARDER to stabilise.

Ecologists long assumed that more diverse, more connected ecosystems are more stable — more pathways,
more redundancy. Robert May (1972) demolished that with one piece of random-matrix theory. Linearise a
community of S species about an equilibrium: the Jacobian (community matrix) has self-regulation -d on
the diagonal and random interactions off it — each pair interacts with probability C (connectance) and
strength drawn with standard deviation sigma. By Girko's circular law, for large S the eigenvalues of
such a matrix fill a DISK in the complex plane, centred at -d with radius sigma*sqrt(S*C). The
equilibrium is stable only if every eigenvalue has negative real part — i.e. the disk stays left of
the imaginary axis:

    stable  <=>  sigma * sqrt(S*C)  <  d.

So raising diversity S, connectance C, or interaction strength sigma pushes the disk RIGHT until it
crosses zero and the community goes unstable. Complexity destabilises. The result launched the
diversity-stability debate.

Allesina & Tang (2012) added the twist that rescued real food webs: the eigenvalue cloud is a disk
only when the pair interactions are uncorrelated. With correlation rho between a_ij and a_ji it becomes
an ELLIPSE with semi-axes sigma*sqrt(S*C)*(1 +/- rho). Predator-prey interactions are ANTIcorrelated
(one gains, the other loses, rho<0), which shrinks the horizontal axis and pushes the stability edge
out — predator-prey structure is STABILISING — whereas mutualism/competition (rho>0) is destabilising.
Pure numpy/scipy (eigenvalues of random matrices); no closed-form ecology needed.
"""

from __future__ import annotations

import numpy as np
from scipy import linalg


def community_matrix(S=250, C=0.3, sigma=0.1, rho=0.0, d=1.0, seed=0):
    """Random community (Jacobian): diagonal -d; each i<j pair interacts w.p. C with strength std sigma
    and transpose-correlation rho (rho<0 = predator-prey, rho>0 = mutualism/competition)."""
    rng = np.random.default_rng(seed)
    M = np.zeros((S, S))
    iu = np.triu_indices(S, 1)
    n = iu[0].size
    present = rng.random(n) < C
    a = rng.normal(0.0, sigma, n)
    b = rho * a + np.sqrt(max(1.0 - rho * rho, 0.0)) * rng.normal(0.0, sigma, n)
    M[iu] = np.where(present, a, 0.0)
    M[(iu[1], iu[0])] = np.where(present, b, 0.0)
    np.fill_diagonal(M, -d)
    return M


def max_real_eigenvalue(M) -> float:
    return float(linalg.eigvals(M).real.max())


def is_stable(M) -> bool:
    return max_real_eigenvalue(M) < 0.0


def complexity(S, C, sigma) -> float:
    """May's complexity parameter sigma*sqrt(S*C); stability boundary is at complexity = d."""
    return float(sigma * np.sqrt(S * C))


def predicted_max_real(S, C, sigma, rho=0.0, d=1.0) -> float:
    """Elliptic-law rightmost eigenvalue of the bulk: -d + sigma*sqrt(S*C)*(1+rho)."""
    return -d + complexity(S, C, sigma) * (1.0 + rho)


def stability_fraction(S, C, sigma, rho=0.0, d=1.0, reps=40, seed=0) -> float:
    """Fraction of random communities that are stable (drops sharply through the boundary)."""
    rng = np.random.default_rng(seed)
    return float(np.mean([is_stable(community_matrix(S, C, sigma, rho, d, seed=int(rng.integers(1 << 30))))
                          for _ in range(reps)]))


def stability_curve(sigmas, S=250, C=0.3, rho=0.0, d=1.0, reps=30, seed=0):
    """Stability fraction vs complexity sigma*sqrt(S*C) as interaction strength is swept."""
    rng = np.random.default_rng(seed)
    kappa = np.array([complexity(S, C, s) for s in sigmas])
    frac = np.array([stability_fraction(S, C, float(s), rho, d, reps, seed=int(rng.integers(1 << 30)))
                     for s in sigmas])
    return kappa, frac
