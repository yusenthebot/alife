import numpy as np

from alife.rpsmobility import init, reaction_step, diffuse_sweep, run, n_survivors, _prey


def test_cyclic_dominance():
    assert _prey(1) == 2 and _prey(2) == 3 and _prey(3) == 1   # A->B->C->A


def test_predation_and_reproduction_conserve_lattice_shape():
    rng = np.random.default_rng(0)
    g = init(40, 0)
    g2 = reaction_step(g.copy(), rng)
    assert g2.shape == (40, 40) and set(np.unique(g2)).issubset({0, 1, 2, 3})


def test_diffusion_conserves_species_counts():
    rng = np.random.default_rng(0)
    g = init(40, 0)
    before = [np.sum(g == s) for s in range(4)]
    g2 = diffuse_sweep(g.copy(), rng)
    after = [np.sum(g2 == s) for s in range(4)]
    assert before == after                                     # exchange only moves cells


def test_low_mobility_preserves_biodiversity():
    r = run(L=100, mobility=2.0, steps=600, seed=1)
    assert n_survivors(r) == 3                                 # spirals coexist


def test_high_mobility_collapses_biodiversity():
    r = run(L=100, mobility=30.0, steps=600, seed=1)
    assert n_survivors(r) == 1                                 # strong mixing -> one survivor


def test_reproducible():
    a = run(L=60, mobility=3.0, steps=120, seed=7)["fracs"]
    b = run(L=60, mobility=3.0, steps=120, seed=7)["fracs"]
    assert np.array_equal(a, b)
