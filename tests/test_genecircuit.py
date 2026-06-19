import numpy as np

from alife.genecircuit import (repressor_ring, oscillation_amplitude, is_oscillating,
                               oscillation_period, toggle_final_state)


def test_three_gene_ring_oscillates():
    r = repressor_ring(n_genes=3, hill=2.5, alpha=12, seed=1)
    assert is_oscillating(r)
    assert oscillation_period(r) > 1.0


def test_loop_parity_rule():
    # odd repression rings oscillate; even rings do not
    for n in (3, 5):
        assert is_oscillating(repressor_ring(n_genes=n, hill=2.5, alpha=12, seed=1))
    for n in (2, 4):
        assert not is_oscillating(repressor_ring(n_genes=n, hill=2.5, alpha=12, seed=1))


def test_cooperativity_required():
    assert not is_oscillating(repressor_ring(n_genes=3, hill=1.0, alpha=12, seed=1))   # no Hill -> no clock
    assert is_oscillating(repressor_ring(n_genes=3, hill=3.0, alpha=12, seed=1))


def test_toggle_switch_is_bistable():
    a = toggle_final_state(hill=3, bias=+0.5)
    b = toggle_final_state(hill=3, bias=-0.5)
    assert a[0] > 5 * a[1]                                 # bias+ -> gene 0 high, gene 1 low
    assert b[1] > 5 * b[0]                                 # bias- -> the opposite stable state


def test_amplitude_zero_for_even_ring():
    assert oscillation_amplitude(repressor_ring(n_genes=4, hill=2.5, alpha=12, seed=1)) < 0.2


def test_reproducible():
    a = repressor_ring(n_genes=3, hill=2.5, alpha=12, seed=7)["proteins"]
    b = repressor_ring(n_genes=3, hill=2.5, alpha=12, seed=7)["proteins"]
    assert np.allclose(a, b)
