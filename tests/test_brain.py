"""Brain network invariants: shapes, weight bounds, heritable variation."""

from __future__ import annotations

import numpy as np

from alife import brain
from alife.brain import BrainSpec


def test_weight_count():
    spec = BrainSpec(n_in=13, n_hidden=8, n_out=2)
    assert spec.n_weights == (13 + 1) * 8 + (8 + 1) * 2  # 130


def test_forward_shape_and_finite():
    spec = BrainSpec(n_in=13, n_hidden=8, n_out=2)
    rng = np.random.default_rng(0)
    w = brain.random_brains(40, spec, rng)
    x = rng.normal(size=(40, 13))
    out = brain.forward(w, spec, x)
    assert out.shape == (40, 2)
    assert np.all(np.isfinite(out))


def test_mutate_bounds_and_variation():
    spec = BrainSpec(n_in=13)
    rng = np.random.default_rng(1)
    w = brain.random_brains(200, spec, rng)
    m = brain.mutate_brains(w, rng, rate=1.0, sigma=5.0)
    assert m.shape == w.shape
    assert (np.abs(m) <= brain.W_CLIP + 1e-9).all()
    assert not np.allclose(m, w)


def test_forward_is_deterministic():
    spec = BrainSpec(n_in=13)
    rng = np.random.default_rng(2)
    w = brain.random_brains(5, spec, rng)
    x = rng.normal(size=(5, 13))
    assert np.array_equal(brain.forward(w, spec, x), brain.forward(w, spec, x))
