import numpy as np

from alife.network import (
    ba_graph, er_graph, degrees, ccdf, powerlaw_exponent, attack_curve, spring_layout,
)


def test_graph_sizes():
    ba = ba_graph(500, 3, seed=0)
    assert ba[:, 0].max() < 500 and degrees(ba, 500).sum() == 2 * len(ba)
    er = er_graph(500, 800, seed=0)
    assert len(er) == 800 and len({tuple(sorted(e)) for e in er}) == 800   # distinct edges


def test_ba_has_hubs_er_does_not():
    n = 3000
    ba, er = ba_graph(n, 2, seed=0), er_graph(n, 6000, seed=0)
    assert degrees(ba, n).max() > 5 * degrees(er, n).max()   # BA grows giant hubs


def test_ba_is_scale_free_er_is_not():
    n = 3000
    ba, er = ba_graph(n, 2, seed=0), er_graph(n, 6000, seed=0)
    # BA CCDF is a shallow power law (~ -2); ER falls off much more steeply (no heavy tail)
    assert powerlaw_exponent(ba, n) > powerlaw_exponent(er, n) + 1.0
    assert -3 < powerlaw_exponent(ba, n) < -1.0


def test_robustness_fragility():
    n = 3000
    ba = ba_graph(n, 2, seed=0)
    rand = attack_curve(ba, n, [0.15], "random", seed=1)[0]
    targ = attack_curve(ba, n, [0.15], "targeted")[0]
    assert rand > 0.6                                  # robust to random failure
    assert targ < 0.2                                  # fragile to targeted hub attack


def test_er_degrades_similarly():
    n = 3000
    er = er_graph(n, 6000, seed=0)
    rand = attack_curve(er, n, [0.15], "random", seed=1)[0]
    targ = attack_curve(er, n, [0.15], "targeted")[0]
    assert abs(rand - targ) < 0.3                      # random graph: no special hub vulnerability at 15%


def test_spring_layout_and_reproducible():
    ba = ba_graph(60, 2, seed=0)
    p = spring_layout(ba, 60, iters=50, seed=1)
    assert p.shape == (60, 2) and np.all(np.isfinite(p))
    assert np.array_equal(ba_graph(100, 2, seed=7), ba_graph(100, 2, seed=7))
