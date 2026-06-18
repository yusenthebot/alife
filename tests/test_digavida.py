import numpy as np

from alife.digavida import (
    ANCESTOR,
    SoupConfig,
    compete,
    is_replicator,
    padded_ancestor,
    replicate_once,
    run_soup,
)


def test_ancestor_self_replicates_exactly():
    off, cycles = replicate_once(ANCESTOR, mut=0.0)
    assert off is not None
    assert np.array_equal(off, ANCESTOR)        # a faithful copy of itself
    assert cycles < 60


def test_padded_ancestor_is_a_replicator():
    assert is_replicator(padded_ancestor(30))
    assert is_replicator(padded_ancestor(15))


def test_random_genome_usually_not_a_replicator():
    rng = np.random.default_rng(0)
    viable = sum(is_replicator(rng.integers(0, 14, 12)) for _ in range(40))
    assert viable < 10                          # self-replication is rare by chance


def test_soup_fills_and_diversifies():
    soup = run_soup(SoupConfig(sweeps=1500), seed=0)
    assert soup["pop"][-1] > 0.8 * SoupConfig().n_slots     # fills
    assert soup["diversity"][-1] > 20                        # mutations accumulate


def test_selection_purges_broken_mutants():
    """Most of the living population are viable replicators — broken code dies out."""
    soup = run_soup(SoupConfig(sweeps=1500), seed=0)
    alive = soup["final_genomes"]
    viable = sum(is_replicator(g) for g in alive)
    assert viable > 0.7 * len(alive)


def test_evolved_organism_still_replicates():
    soup = run_soup(SoupConfig(sweeps=1500), seed=0)
    alive = soup["final_genomes"]
    mutated = [g for g in alive if not np.array_equal(g, padded_ancestor(len(g)))]
    assert any(is_replicator(g) for g in mutated)   # evolved (changed) code that still copies


def test_faster_replicator_outcompetes_slower():
    c = compete(len_short=7, len_long=30, sweeps=2000, seed=0)
    assert c["short"][-1] > 0.8 * (c["short"][-1] + c["long"][-1])   # short dominates
    assert c["long"][-1] < c["long"][0]                              # long declines


def test_reproducible():
    a = run_soup(SoupConfig(sweeps=400), seed=3)["diversity"]
    b = run_soup(SoupConfig(sweeps=400), seed=3)["diversity"]
    assert np.array_equal(a, b)
