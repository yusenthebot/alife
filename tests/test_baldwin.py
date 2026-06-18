import numpy as np

from alife.baldwin import BaldwinConfig, evolve


def test_learning_finds_the_needle():
    cfg = BaldwinConfig(generations=400)
    r = evolve(cfg, learning=True, seed=0)
    assert r["solvable"][-1] > 0.9          # population reaches the target


def test_learning_assimilates_plasticity():
    """The Baldwin signature: '?' alleles are replaced by fixed-correct ones."""
    cfg = BaldwinConfig(generations=400)
    r = evolve(cfg, learning=True, seed=0)
    assert r["plastic"][-1] < 0.2           # plasticity largely assimilated away
    assert r["correct"][-1] > 0.8           # fixed-correct sweeps up
    assert r["correct"][-1] > r["correct"][0] + 0.4


def test_no_learning_stays_blind():
    """Without learning the landscape is a flat plain with one spike: no climb."""
    cfg = BaldwinConfig(generations=400)
    r = evolve(cfg, learning=False, seed=0)
    assert r["solvable"][-1] < 0.1
    assert abs(r["correct"][-1] - 0.5) < 0.2   # stays near chance

def test_learning_beats_no_learning():
    cfg = BaldwinConfig(generations=400)
    for seed in range(3):
        L = evolve(cfg, learning=True, seed=seed)["solvable"][-1]
        N = evolve(cfg, learning=False, seed=seed)["solvable"][-1]
        assert L > N + 0.5


def test_wrong_alleles_purged_with_learning():
    cfg = BaldwinConfig(generations=400)
    r = evolve(cfg, learning=True, seed=0)
    assert r["wrong"][-1] < 0.05            # fixed-wrong alleles selected out


def test_reproducible():
    cfg = BaldwinConfig(generations=80)
    a = evolve(cfg, learning=True, seed=4)["correct"]
    b = evolve(cfg, learning=True, seed=4)["correct"]
    assert np.array_equal(a, b)
