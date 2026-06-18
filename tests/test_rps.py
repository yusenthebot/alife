import numpy as np

from alife.rps import RPSConfig, diversity, run


def test_lattice_preserves_all_three_species():
    cfg = RPSConfig(steps=250)
    for seed in range(3):
        r = run(cfg, well_mixed=False, seed=seed)
        assert diversity(r) > 0.15          # all three coexist, none rare


def test_well_mixed_loses_diversity():
    cfg = RPSConfig(steps=250)
    r = run(cfg, well_mixed=True, seed=0)
    assert diversity(r) < 0.05              # at least one species (usually two) lost


def test_lattice_beats_well_mixed():
    cfg = RPSConfig(steps=250)
    for seed in range(3):
        sp = diversity(run(cfg, False, seed))
        wm = diversity(run(cfg, True, seed))
        assert sp > wm + 0.1


def test_fractions_sum_to_one():
    cfg = RPSConfig(size=60, steps=50)
    r = run(cfg, well_mixed=False, seed=0)
    assert np.allclose(r["fractions"].sum(axis=1), 1.0)


def test_snapshots_have_all_types_early():
    cfg = RPSConfig(size=80, steps=120)
    r = run(cfg, well_mixed=False, seed=0)
    assert set(np.unique(r["snaps"][cfg.steps])).issubset({0, 1, 2})
    assert r["final"].shape == (80, 80)


def test_reproducible():
    cfg = RPSConfig(size=60, steps=60)
    a = run(cfg, False, 2)["fractions"]
    b = run(cfg, False, 2)["fractions"]
    assert np.array_equal(a, b)
