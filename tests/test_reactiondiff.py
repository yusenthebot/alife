import numpy as np

from dataclasses import replace

from alife.reactiondiff import (
    REGIMES,
    ReactionDiffConfig,
    pattern_strength,
    run,
    run_regime,
)

FAST = ReactionDiffConfig(size=100, steps=2500, seed_blocks=12)


def test_field_stays_bounded():
    r = run_regime("stripes", FAST, seed=0)
    assert np.all(r["V"] >= 0) and np.all(r["V"] <= 1)
    assert np.all(r["U"] >= 0) and np.all(r["U"] <= 1)
    assert np.all(np.isfinite(r["V"]))


def test_patterns_form():
    """Symmetry breaks: the V field develops spatial structure (non-uniform)."""
    for name in ("stripes", "waves", "coral"):
        r = run_regime(name, FAST, seed=0)
        assert pattern_strength(r["V"]) > 0.02


def test_no_seed_stays_uniform():
    """With no perturbation the homogeneous state persists (no spontaneous pattern)."""
    cfg = replace(FAST, seed_blocks=0)
    r = run_regime("stripes", cfg, seed=0)
    assert pattern_strength(r["V"]) < 1e-3


def test_regimes_differ():
    a = run_regime("stripes", FAST, seed=0)["V"]
    b = run_regime("waves", FAST, seed=0)["V"]
    assert not np.allclose(a, b)


def test_snapshots_recorded():
    r = run_regime("coral", replace(FAST, steps=1000), seed=0, record_every=250)
    assert len(r["snaps"]) >= 3


def test_reproducible():
    a = run_regime("stripes", FAST, seed=2)["V"]
    b = run_regime("stripes", FAST, seed=2)["V"]
    assert np.array_equal(a, b)
