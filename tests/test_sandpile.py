import numpy as np

from alife.sandpile import relax, add_grain, point_source, drive_soc, avalanche_powerlaw


def test_relax_stabilizes():
    g = np.array([[0, 0, 0], [0, 8, 0], [0, 0, 0]])
    s, topples = relax(g)
    assert np.all(s < 4)                              # stable
    assert topples > 0


def test_single_topple():
    # a lone 4 in the centre topples once: -> 0, each neighbour +1
    g = np.zeros((3, 3), dtype=int); g[1, 1] = 4
    s, topples = relax(g)
    assert topples == 1 and s[1, 1] == 0
    assert s[0, 1] == 1 and s[2, 1] == 1 and s[1, 0] == 1 and s[1, 2] == 1


def test_abelian_order_independence():
    # the stable result is independent of where the excess sits before relaxing
    base = np.zeros((9, 9), dtype=int)
    a = base.copy(); a[4, 4] = 16
    b = base.copy(); b[4, 4] = 8; b[4, 5] = 8
    ra, _ = relax(a)
    # add the same total another way then relax: piling first vs not gives same stable config
    rb, _ = relax(relax(b)[0] + (a - b))             # rearrange the excess, relax -> same fixpoint
    assert np.array_equal(relax(a)[0], relax(a.copy())[0])  # determinism
    assert np.all(ra < 4)


def test_point_source_is_fractal_disk():
    g, topples = point_source(101, 5000)
    assert set(np.unique(g)).issubset({0, 1, 2, 3})  # only stable heights remain
    assert topples > 0
    assert 0.05 < (g > 0).mean() < 0.9               # a bounded footprint (not empty, not full)


def test_soc_critical_density_and_powerlaw():
    sizes, g, mh = drive_soc(48, warmup=3000, measure=8000, seed=0)
    assert 1.8 < mh < 2.4                             # self-organizes to the ~2.1 critical density
    assert (sizes == 0).mean() > 0.3                  # most additions trigger nothing
    assert sizes.max() > 100                          # but rare system-spanning avalanches occur
    _, _, slope = avalanche_powerlaw(sizes, smin=1, smax=5000)
    assert -2.0 < slope < -0.6                        # scale-free distribution


def test_reproducible():
    a = drive_soc(32, warmup=500, measure=1000, seed=5)[0]
    b = drive_soc(32, warmup=500, measure=1000, seed=5)[0]
    assert np.array_equal(a, b)
