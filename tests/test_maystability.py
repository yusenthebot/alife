import numpy as np

from alife.maystability import (
    community_matrix, max_real_eigenvalue, is_stable, complexity,
    predicted_max_real, stability_fraction,
)


def test_diagonal_is_self_regulation():
    M = community_matrix(S=50, C=0.4, sigma=0.1, d=1.3, seed=0)
    assert np.allclose(np.diag(M), -1.3)


def test_offdiagonal_transpose_correlation_matches_rho():
    M = community_matrix(S=300, C=0.6, sigma=0.1, rho=-0.6, seed=1)
    iu = np.triu_indices(300, 1)
    a, b = M[iu], M[(iu[1], iu[0])]
    both = (a != 0) & (b != 0)                              # present (interacting) pairs
    assert abs(np.corrcoef(a[both], b[both])[0, 1] - (-0.6)) < 0.05


def test_girko_radius_predicts_spectral_reach():
    # random (rho=0): rightmost eigenvalue ~ -d + sigma*sqrt(S*C) (Girko circular law)
    S, C, sigma = 400, 0.3, 0.07
    M = community_matrix(S, C, sigma, rho=0.0, d=1.0, seed=2)
    assert abs(max_real_eigenvalue(M) - predicted_max_real(S, C, sigma, 0.0)) < 0.05


def test_may_complexity_destabilizes():
    # below the boundary sigma*sqrt(SC)<1 communities are stable; above it they are not
    lo = stability_fraction(S=200, C=0.3, sigma=0.7 / np.sqrt(60), reps=30, seed=3)   # kappa~0.7
    hi = stability_fraction(S=200, C=0.3, sigma=1.3 / np.sqrt(60), reps=30, seed=3)   # kappa~1.3
    assert lo > 0.9 and hi < 0.1


def test_transition_is_at_complexity_one():
    # stability fraction passes through ~0.5 right at kappa = d = 1
    near = stability_fraction(S=300, C=0.3, sigma=1.0 / np.sqrt(90), reps=60, seed=4)  # kappa~1.0
    assert 0.2 < near < 0.8


def test_predator_prey_structure_stabilizes():
    # at the random boundary (kappa~1), predator-prey (rho<0) stay stable, random are marginal,
    # mutualism (rho>0) has already collapsed -- interaction STRUCTURE, not just complexity, matters
    kw = dict(S=250, C=0.3, sigma=1.0 / np.sqrt(75), reps=40, seed=5)                # kappa~1.0
    pp = stability_fraction(rho=-0.6, **kw)
    rand = stability_fraction(rho=0.0, **kw)
    mut = stability_fraction(rho=0.6, **kw)
    assert pp > rand > mut                                                            # 1.0 > ~0.6 > 0.0
    assert pp > 0.8 and mut < 0.1


def test_predicted_reach_rises_with_rho_and_sigma():
    base = predicted_max_real(300, 0.3, 0.1, 0.0)
    assert predicted_max_real(300, 0.3, 0.1, 0.6) > base          # mutualism reaches further right
    assert predicted_max_real(300, 0.3, 0.1, -0.6) < base         # predator-prey pulled left
    assert predicted_max_real(300, 0.3, 0.15, 0.0) > base         # stronger interactions reach further


def test_higher_connectance_less_stable():
    lo = stability_fraction(S=200, C=0.15, sigma=0.12, reps=30, seed=6)
    hi = stability_fraction(S=200, C=0.6, sigma=0.12, reps=30, seed=6)
    assert lo > hi


def test_reproducible():
    a = community_matrix(S=80, C=0.3, sigma=0.1, rho=-0.4, seed=9)
    b = community_matrix(S=80, C=0.3, sigma=0.1, rho=-0.4, seed=9)
    assert np.array_equal(a, b)
