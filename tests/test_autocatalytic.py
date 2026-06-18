import numpy as np

from alife.autocatalytic import (
    RAFConfig, build_polymer_model, production_closure, max_raf, verify_raf,
    random_catalysis, has_raf, phase_transition,
)


def test_polymer_model_sizes():
    cfg = RAFConfig(max_len=4, food_len=2)
    mols, idx, reactions, food = build_polymer_model(cfg)
    assert len(mols) == 2 + 4 + 8 + 16            # strings length 1..4
    assert len(food) == 2 + 4                      # length 1..2
    # reaction count = sum over strings length 2..L of (len-1)
    assert len(reactions) == 4 * 1 + 8 * 2 + 16 * 3


def test_production_closure_builds_products():
    # m0+m1->m2, m0+m2->m3 ; from food {0,1} both products are reachable
    reactions = [(0, 1, 2), (0, 2, 3)]
    food = {0, 1}
    W = production_closure(reactions, food, {0, 1})
    assert W == {0, 1, 2, 3}
    # without the second reaction, m3 cannot form
    assert production_closure(reactions, food, {0}) == {0, 1, 2}


def test_circular_raf_is_found():
    """The key correctness case: r0's catalyst is r1's product and vice versa.
    A temporal bootstrap deadlocks; the fixpoint maxRAF must still find the set."""
    reactions = [(0, 1, 2), (0, 2, 3)]
    food = {0, 1}
    catalysts = [{3}, {2}]                          # circular mutual catalysis
    active, W = max_raf(reactions, food, catalysts)
    assert active == {0, 1}
    assert verify_raf(reactions, food, catalysts, active)


def test_uncatalysable_set_has_no_raf():
    reactions = [(0, 1, 2), (0, 2, 3)]
    food = {0, 1}
    catalysts = [{9}, {9}]                          # catalyst 9 never producible
    active, _ = max_raf(reactions, food, catalysts)
    assert active == set()
    assert not has_raf(reactions, food, catalysts)


def test_no_catalysis_no_raf():
    cfg = RAFConfig(max_len=6, food_len=2)
    _, _, reactions, food = build_polymer_model(cfg)
    catalysts = [set() for _ in reactions]
    assert not has_raf(reactions, food, catalysts)


def test_maxraf_axioms_hold_on_random_instances():
    cfg = RAFConfig(max_len=6, food_len=2)
    mols, _, reactions, food = build_polymer_model(cfg)
    for s in range(8):
        rng = np.random.default_rng(s)
        cat = random_catalysis(len(reactions), len(mols), 3.0, rng)
        active, _ = max_raf(reactions, food, cat)
        assert verify_raf(reactions, food, cat, active)   # construction obeys both axioms


def test_phase_transition_giant_set_emerges():
    cfg = RAFConfig(max_len=7, food_len=2)
    f, prob, size, dims = phase_transition(cfg, [0.0, 1.0, 4.0], trials=30, seed=3)
    assert prob[0] == 0.0                            # no catalysis -> never
    assert prob[2] > prob[0]                         # high catalysis -> RAFs appear
    assert size[2] > 20                              # and they are GIANT (many reactions)
