import numpy as np

from alife.hopfield import (
    store_hebbian, energy, recall, overlap, corrupt, occlude,
    capacity_curve, demo_patterns,
)


def test_weights_symmetric_zero_diagonal():
    pats = np.random.default_rng(0).choice([-1, 1], (4, 30))
    W = store_hebbian(pats)
    assert np.allclose(W, W.T)
    assert np.allclose(np.diag(W), 0)


def test_stored_patterns_are_fixed_points():
    pats, shape = demo_patterns(12)
    W = store_hebbian(pats)
    for mu in range(len(pats)):
        s, et, _ = recall(W, pats[mu].copy(), steps=10, seed=0)
        assert overlap(s, pats[mu]) > 0.99            # a stored memory is a stable attractor


def test_recall_from_noise():
    pats, shape = demo_patterns(14)
    W = store_hebbian(pats)
    rng = np.random.default_rng(1)
    for mu in range(len(pats)):
        cue = corrupt(pats[mu], 0.25, rng)
        s, _, _ = recall(W, cue, steps=30, seed=2)
        assert overlap(s, pats[mu]) > 0.95            # error-corrected back to the memory


def test_energy_never_increases():
    pats, shape = demo_patterns(12)
    W = store_hebbian(pats)
    cue = corrupt(pats[0], 0.4, np.random.default_rng(3))
    _, etrace, _ = recall(W, cue, steps=30, seed=0)
    assert np.all(np.diff(etrace) <= 1e-9)            # Lyapunov: async updates never raise energy


def test_pattern_completion_from_occlusion():
    pats, shape = demo_patterns(14)
    W = store_hebbian(pats)
    s, _, _ = recall(W, occlude(pats[1], 0.4), steps=30, seed=0)
    assert overlap(s, pats[1]) > 0.8                  # fills in a blanked-out half


def test_capacity_transition():
    al, acc = capacity_curve(N=160, alphas=[0.05, 0.10, 0.25], trials=5, seed=0)
    assert acc[0] > 0.95 and acc[1] > 0.9             # below capacity: near-perfect recall
    assert acc[2] < acc[1] - 0.15                     # above ~0.138: recall has collapsed


def test_inverse_is_also_attractor():
    pats, shape = demo_patterns(12)
    W = store_hebbian(pats)
    s, _, _ = recall(W, (-pats[0]).copy(), steps=10, seed=0)
    assert overlap(s, pats[0]) < -0.99               # the negative of a memory is also stable
