import numpy as np

from alife.boltzmann import (
    bars_and_stripes, is_valid_bas, train, init_rbm, gibbs_sample, valid_fraction,
)


def test_bas_dataset():
    d = bars_and_stripes(4)
    assert d.shape == (30, 16)                         # 2*2^4 - 2 valid patterns
    assert all(is_valid_bas(p) for p in d)
    assert set(np.unique(d)).issubset({0.0, 1.0})


def test_is_valid_bas():
    n = 4
    rows = np.tile(np.array([1, 0, 1, 0])[:, None], (1, n)).ravel()   # horizontal bars
    cols = np.tile(np.array([1, 0, 1, 0])[None, :], (n, 1)).ravel()   # vertical stripes
    assert is_valid_bas(rows) and is_valid_bas(cols)
    bad = np.zeros(16); bad[0] = 1                                     # single pixel -> invalid
    assert not is_valid_bas(bad)


def test_training_reduces_reconstruction_error():
    data = bars_and_stripes(4)
    _, err = train(data, n_hid=16, epochs=2000, lr=0.1, seed=0)
    assert err[-1] < 0.3 * err[0]                       # CD learns to reconstruct the data


def test_trained_rbm_dreams_valid_patterns():
    data = bars_and_stripes(4)
    rbm, _ = train(data, n_hid=16, epochs=4000, lr=0.1, seed=0)
    vf = valid_fraction(gibbs_sample(rbm, 400, steps=300, seed=1))
    assert vf > 0.4                                     # most dreams are valid bars/stripes


def test_untrained_dreams_noise():
    untr = init_rbm(16, 16, np.random.default_rng(0))
    vf = valid_fraction(gibbs_sample(untr, 400, steps=300, seed=1))
    assert vf < 0.05                                    # untrained net dreams ~random noise


def test_dreams_are_diverse():
    data = bars_and_stripes(4)
    rbm, _ = train(data, n_hid=16, epochs=4000, lr=0.1, seed=0)
    gen = gibbs_sample(rbm, 600, steps=300, seed=3)
    distinct = len({tuple(s.tolist()) for s in gen if is_valid_bas(s)})
    assert distinct > 6                                 # samples many modes, not one (no collapse)


def test_reproducible():
    data = bars_and_stripes(3)
    a = train(data, n_hid=8, epochs=300, lr=0.1, seed=2)[0].W
    b = train(data, n_hid=8, epochs=300, lr=0.1, seed=2)[0].W
    assert np.allclose(a, b)
