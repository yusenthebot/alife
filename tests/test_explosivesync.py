import numpy as np

from alife.network import ba_graph
from alife.explosivesync import degree_frequencies, hysteresis_area, run


def test_degree_frequencies_correlation_and_shuffle():
    edges = ba_graph(300, m=3, seed=0)
    from alife.network import degrees
    k = degrees(edges, 300).astype(float)
    omega = degree_frequencies(edges, 300, shuffle=False)
    shuf = degree_frequencies(edges, 300, shuffle=True, seed=0)
    assert np.corrcoef(omega, k)[0, 1] > 0.99                 # correlated with degree
    assert abs(np.corrcoef(shuf, k)[0, 1]) < 0.3              # shuffle breaks the correlation
    assert np.allclose(np.sort(omega), np.sort(shuf))         # same frequency distribution
    assert abs(omega.mean()) < 1e-6 and abs(omega.std() - 1) < 1e-6


def test_hysteresis_area_zero_for_identical_curves():
    K = np.linspace(0, 1, 10)
    assert hysteresis_area(K, np.ones(10), np.ones(10)) == 0.0


def test_correlated_is_explosive_with_hysteresis():
    r = run(n=400, m=3, Ks=np.linspace(0, 2.5, 16), seed=1, shuffle=False, equil=300, measure=100)
    assert np.max(np.diff(r["rf"])) > 0.4                     # an abrupt forward jump (first-order)
    assert r["area"] > 0.2                                    # forward != backward -> hysteresis


def test_shuffled_control_is_smooth_no_hysteresis():
    r = run(n=400, m=3, Ks=np.linspace(0, 2.5, 16), seed=1, shuffle=True, equil=300, measure=100)
    assert np.max(np.diff(r["rf"])) < 0.4                     # gradual, no cliff
    assert r["area"] < 0.2                                    # forward ~ backward -> reversible


def test_strong_coupling_synchronizes_both():
    for sh in (False, True):
        r = run(n=400, m=3, Ks=np.linspace(0, 2.5, 16), seed=1, shuffle=sh, equil=300, measure=100)
        assert r["rf"][-1] > 0.8                              # high K -> synchronized


def test_reproducible():
    a = run(n=300, m=3, Ks=np.linspace(0, 2, 8), seed=3, equil=150, measure=60)["rf"]
    b = run(n=300, m=3, Ks=np.linspace(0, 2, 8), seed=3, equil=150, measure=60)["rf"]
    assert np.array_equal(a, b)
