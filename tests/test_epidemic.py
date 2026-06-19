import numpy as np

from alife.epidemic import (
    ba_graph, er_graph, sir, sir_timeseries, epidemic_size, infection_by_degree, immunize,
)


def test_sir_states_and_conservation():
    g = ba_graph(800, 2, seed=0)
    state, ever = sir(g, 800, beta=0.3, gamma=0.3, seed=0)
    assert np.all((state == 0) | (state == 2))         # no infected remain at the end
    assert ever.sum() >= (state == 2).sum() - 5        # ever-infected ~ recovered (+ seeds)
    assert set(np.unique(state)).issubset({0, 1, 2})


def test_immune_nodes_never_infected():
    g = ba_graph(800, 2, seed=0)
    immune = set(range(50))
    state, _ = sir(g, 800, beta=0.5, gamma=0.3, seed=1, immune=immune)
    assert np.all(state[list(immune)] == 2)            # vaccinated stay removed (never S/I)


def test_scale_free_threshold_below_random():
    n = 3000
    ba, er = ba_graph(n, 2, seed=0), er_graph(n, 6000, seed=0)
    # at a low infection rate, the scale-free net has a real outbreak while the random graph fizzles
    sb = epidemic_size(ba, n, beta=0.08, gamma=0.3, trials=12, seed=1)
    se = epidemic_size(er, n, beta=0.08, gamma=0.3, trials=12, seed=1)
    assert sb > 5 * se and sb > 0.02


def test_hubs_are_super_spreaders():
    n = 3000
    ba = ba_graph(n, 2, seed=0)
    deg, prob = infection_by_degree(ba, n, beta=0.12, gamma=0.3, trials=25, seed=2, nbins=8)
    assert prob[-1] > prob[0] + 0.05                   # high-degree nodes infected more often


def test_targeted_immunization_beats_random():
    n = 3000
    ba = ba_graph(n, 2, seed=0)
    base = epidemic_size(ba, n, 0.2, gamma=0.3, trials=14, seed=3)
    rnd = immunize(ba, n, 0.2, 0.05, "random", gamma=0.3, trials=14, seed=3)
    tgt = immunize(ba, n, 0.2, 0.05, "targeted", gamma=0.3, trials=14, seed=3)
    assert tgt < 0.1 * base + 0.02                     # 5% targeted nearly stops the epidemic
    assert tgt < rnd                                   # and beats random vaccination


def test_timeseries_and_reproducible():
    g = ba_graph(600, 2, seed=0)
    S, I, R = sir_timeseries(g, 600, 0.3, gamma=0.3, seed=4)
    assert np.all(S + I + R == 600)                    # population conserved each step
    a = epidemic_size(g, 600, 0.25, gamma=0.3, trials=4, seed=7)
    b = epidemic_size(g, 600, 0.25, gamma=0.3, trials=4, seed=7)
    assert a == b
