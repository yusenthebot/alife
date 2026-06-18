import numpy as np

from alife.conway import (
    GLIDER,
    glider_gun,
    place,
    random_soup,
    run,
    step,
)


def test_blinker_oscillates_period_2():
    g = place([(1, 0), (1, 1), (1, 2)], (3, 3))
    g1 = step(g)
    g2 = step(g1)
    assert not np.array_equal(g, g1)        # changes
    assert np.array_equal(g, g2)            # period-2 oscillator


def test_block_is_still_life():
    g = place([(0, 0), (0, 1), (1, 0), (1, 1)], (4, 4))
    assert np.array_equal(step(g), g)       # stable


def test_glider_moves_c_over_4():
    g = place(GLIDER, (24, 24), (2, 2))
    g4 = g.copy()
    for _ in range(4):
        g4 = step(g4)
    assert np.array_equal(g4, place(GLIDER, (24, 24), (3, 3)))   # translated (1,1)
    assert g4.sum() == 5                     # glider preserved


def test_gun_grows_unboundedly():
    r = run(glider_gun((120, 120)), 200)
    assert r["population"][-1] > r["population"][0] + 20   # gliders accumulate


def test_soup_decays_and_stabilizes():
    r = run(random_soup((100, 100), 0.30, seed=0), 250)
    p = r["population"]
    assert p[-1] < p[0] * 0.6                # decays from initial density
    assert abs(int(p[-1]) - int(p[-20])) < p[0] * 0.1   # roughly stable at the end


def test_empty_stays_empty():
    g = np.zeros((10, 10), dtype=bool)
    assert step(g).sum() == 0


def test_reproducible():
    a = run(random_soup((60, 60), 0.3, seed=1), 50)["population"]
    b = run(random_soup((60, 60), 0.3, seed=1), 50)["population"]
    assert np.array_equal(a, b)
