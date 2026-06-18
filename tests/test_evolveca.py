import numpy as np

from alife.evolveca import (
    CAConfig, table_size, _neighbour_index, evolve_step, evolve,
    sync_fitness, sync_rate, hard_accuracy, spacetime, random_rule,
)


def test_table_and_index():
    assert table_size(3) == 128
    # neighbourhood index packs the width-(2r+1) window MSB=leftmost
    s = np.array([[0, 0, 1, 0, 0, 0, 0]], np.int8)     # a single 1 at position 2
    idx = _neighbour_index(s, 1)                        # r=1 -> 3-bit windows, leftmost=LSB
    # cell 1 sees the 1 as its RIGHT neighbour (bit2); cell 2 as CENTRE (bit1); cell 3 as LEFT (bit0)
    assert idx[0, 1] == 0b100 and idx[0, 2] == 0b010 and idx[0, 3] == 0b001


def test_identity_and_constant_rules():
    cfg = CAConfig(r=2, width=20)
    ts = table_size(2)
    # identity: output = centre bit (bit r of the index)
    ident = np.array([(i >> 2) & 1 for i in range(ts)], np.int8)
    g = (np.random.default_rng(0).random((3, 20)) < 0.5).astype(np.int8)
    assert np.array_equal(evolve_step(g, ident, 2), g)         # unchanged
    assert evolve_step(g, np.ones(ts, np.int8), 2).all()       # all-ones rule -> all 1
    assert not evolve_step(g, np.zeros(ts, np.int8), 2).any()  # all-zeros rule -> all 0


def test_sync_score_logic():
    cfg = CAConfig(r=2, width=21)
    ts = table_size(2)
    # global flip rule: output = NOT centre. A UNIFORM start blinks in unison -> synchronized.
    flip = np.array([1 - ((i >> 2) & 1) for i in range(ts)], np.int8)
    # uniform ICs -> always synced
    rng = np.random.default_rng(0)
    from alife.evolveca import _sync_score
    uniform_ics = np.repeat(rng.integers(0, 2, (10, 1)), cfg.width, axis=1).astype(np.int8)
    assert _sync_score(flip, uniform_ics, cfg, 10) == 1.0
    # a constant all-1 rule is uniform but NOT alternating -> not synchronized
    assert sync_rate(np.ones(ts, np.int8), cfg, 200) == 0.0


def test_trivial_density_baseline():
    cfg = CAConfig(r=3, width=99)
    # always-1 rule classifies correctly exactly when the majority was 1 -> ~0.5 on hard ICs
    acc = hard_accuracy(np.ones(table_size(3), np.int8), cfg, 2000)
    assert 0.4 < acc < 0.6


def test_ga_improves_synchronization():
    cfg = CAConfig(r=3, width=49)
    r = evolve(cfg, pop_size=60, gens=30, n_ics=50, seed=2, fitness_fn=sync_fitness)
    h = r["history"]
    assert h[-1, 0] > h[0, 0] + 0.2                    # fitness climbs substantially
    assert sync_rate(r["best"], cfg, 500) > 0.4         # the evolved rule genuinely synchronizes


def test_spacetime_shape_and_reproducible():
    cfg = CAConfig(r=3, width=40)
    rule = random_rule(np.random.default_rng(1), 3)
    a = spacetime(rule, cfg, 0.5, steps=30, seed=3)
    b = spacetime(rule, cfg, 0.5, steps=30, seed=3)
    assert a.shape == (31, 40) and np.array_equal(a, b)
