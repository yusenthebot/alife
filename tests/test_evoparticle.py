import numpy as np

from alife.evoparticle import EvoConfig, motility, chaser_matrix, evolve

# small/fast config for tests
FAST = EvoConfig(n=250, world=240.0, steps=90)


def test_symmetric_matrix_conserves_momentum():
    # the key control: symmetric forces obey Newton's 3rd law -> zero net drift
    rng = np.random.default_rng(0)
    for s in range(5):
        M = rng.uniform(-1, 1, (4, 4))
        sym = (M + M.T) / 2
        assert motility(sym, FAST, seed=1) < 1e-6           # exactly zero (no self-propulsion)


def test_asymmetric_matrix_can_self_propel():
    # at least some random asymmetric matrices drift substantially (broken momentum conservation)
    rng = np.random.default_rng(1)
    drifts = [motility(rng.uniform(-1, 1, (4, 4)), FAST, seed=1) for _ in range(20)]
    assert max(drifts) > 5.0                                 # generic self-propulsion exists
    assert np.mean(drifts) > 0.0


def test_motility_nonnegative_and_finite():
    d = motility(chaser_matrix(), FAST, seed=0)
    assert np.isfinite(d) and d >= 0.0


def test_evolution_improves_motility():
    # a short GA should improve best motility over its first generation
    r = evolve(FAST, gens=5, pop=8, seed=0, eval_seeds=1)
    assert r["best_fitness"] >= r["best_hist"][0]            # monotone-best by construction
    assert r["best_fitness"] > 1.2 * r["best_hist"][0]       # and it actually climbs
    assert r["best_matrix"].shape == (4, 4)


def test_symmetrizing_evolved_matrix_kills_motility():
    # locomotion lives in the asymmetric part: symmetrizing the champion abolishes drift
    r = evolve(FAST, gens=5, pop=8, seed=2, eval_seeds=1)
    bm = r["best_matrix"]
    assert motility(bm, FAST, seed=1) > 5.0                  # champion moves
    assert motility((bm + bm.T) / 2, FAST, seed=1) < 1e-6    # symmetrized champion does not


def test_reproducible():
    a = motility(chaser_matrix(), FAST, seed=7)
    b = motility(chaser_matrix(), FAST, seed=7)
    assert a == b
