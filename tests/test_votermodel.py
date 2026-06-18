import numpy as np

from alife.votermodel import (
    run, voter_step, majority_step, interface_density, magnetization, ensemble_mag_drift,
)


def test_interface_density_extremes():
    g = np.ones((10, 10), np.int8)
    assert interface_density(g) == 0.0                 # uniform -> no boundaries
    chec = np.indices((10, 10)).sum(0) % 2 * 2 - 1     # checkerboard -> every bond differs
    assert interface_density(chec.astype(np.int8)) == 1.0


def test_steps_preserve_binary_and_shape():
    rng = np.random.default_rng(0)
    g = np.where(rng.random((20, 20)) < 0.5, 1, -1).astype(np.int8)
    for step in (voter_step, majority_step):
        out = step(g, rng)
        assert out.shape == g.shape and set(np.unique(out)).issubset({-1, 1})


def test_both_coarsen():
    # from a random start, interface density falls (domains form) under both rules
    rv = run(120, 300, "voter", seed=0)
    rm = run(120, 300, "majority", seed=0, noise=0.03)
    assert rv["interface"][-1] < 0.45 and rm["interface"][-1] < 0.45


def test_majority_has_surface_tension():
    # majority coarsens faster (lower interface density) than voter -> surface tension
    rv = run(160, 600, "voter", seed=0)
    rm = run(160, 600, "majority", seed=0, noise=0.03)
    assert rm["interface"][-1] < rv["interface"][-1] * 0.75


def test_voter_mean_opinion_driftless():
    # voter conserves the mean opinion on average (martingale): ensemble mean stays ~0
    finals = ensemble_mag_drift(96, 400, "voter", trials=16, seed=2)
    assert abs(finals.mean()) < 0.12                   # no systematic drift
    assert finals.std() > 0.02                          # but individual runs random-walk


def test_reproducible():
    a = run(60, 100, "voter", seed=5)["grid"]
    b = run(60, 100, "voter", seed=5)["grid"]
    assert np.array_equal(a, b)
