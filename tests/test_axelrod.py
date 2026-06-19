import numpy as np

from alife.axelrod import init_culture, domains, run, sweep_traits


def test_uniform_culture_is_one_domain():
    c = np.zeros((10, 10, 4), int)                          # everyone identical
    n, largest = domains(c)
    assert n == 1 and largest == 1.0


def test_all_distinct_many_domains():
    c = np.arange(6 * 6 * 3).reshape(6, 6, 3)               # every cell unique
    n, largest = domains(c)
    assert n == 36 and abs(largest - 1 / 36) < 1e-9


def test_low_diversity_reaches_monoculture():
    r = run(L=16, F=10, q=3, seed=1, max_sweeps=9000)
    assert r["largest"] > 0.9                                # few traits -> contact unifies
    assert r["n_regions"] <= 3


def test_high_diversity_stays_fragmented():
    r = run(L=16, F=10, q=120, seed=1, max_sweeps=9000)
    assert r["largest"] < 0.2                                # many traits -> frozen multiculture
    assert r["n_regions"] > 20


def test_diversity_transition_is_monotone_direction():
    qv, largest = sweep_traits(np.array([5, 200]), L=16, F=10, seed=3, max_sweeps=9000)
    assert largest[0] > 0.8 and largest[1] < 0.2            # mono at low q, fragmented at high q


def test_run_freezes_or_caps():
    r = run(L=14, F=10, q=50, seed=0, max_sweeps=9000)
    assert 0.0 <= r["largest"] <= 1.0 and r["n_regions"] >= 1
