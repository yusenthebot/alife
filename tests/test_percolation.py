import numpy as np

from alife.percolation import (occupy, spans, largest_fraction, cluster_sizes,
                               spanning_probability, cluster_size_distribution, PC_2D)


def test_full_grid_spans_one_cluster():
    g = np.ones((30, 30), bool)
    assert spans(g)
    assert largest_fraction(g) == 1.0
    assert len(cluster_sizes(g)) == 1


def test_empty_and_sparse_do_not_span():
    assert not spans(np.zeros((30, 30), bool))
    assert not spans(occupy(80, 0.2, seed=0))               # well below p_c


def test_spanning_probability_transition():
    lo = spanning_probability(100, 0.50, trials=60, seed=1)
    mid = spanning_probability(100, PC_2D, trials=80, seed=1)
    hi = spanning_probability(100, 0.70, trials=60, seed=1)
    assert lo < 0.15                                         # below p_c: rarely spans
    assert hi > 0.9                                          # above p_c: almost always
    assert 0.3 < mid < 0.7                                   # at p_c: ~half


def test_order_parameter_jumps_at_pc():
    lo = np.mean([largest_fraction(occupy(100, 0.50, s)) for s in range(15)])
    hi = np.mean([largest_fraction(occupy(100, 0.70, s)) for s in range(15)])
    assert lo < 0.15 and hi > 0.5                            # giant cluster only above p_c


def test_scale_free_clusters_at_pc():
    cx, cy = cluster_size_distribution(320, PC_2D, trials=20, seed=3)
    mask = (cx > 2) & (cx < 4000)
    slope = np.polyfit(np.log(cx[mask]), np.log(cy[mask]), 1)[0]
    assert -2.6 < slope < -1.5                               # power-law near Fisher tau ~2.05


def test_reproducible():
    assert np.array_equal(occupy(50, 0.6, seed=7), occupy(50, 0.6, seed=7))
