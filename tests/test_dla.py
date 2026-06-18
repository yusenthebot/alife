import numpy as np

from alife.dla import grow, fractal_dimension


def test_grows_a_cluster():
    r = grow(size=121, n_particles=1500, seed=0)
    assert r["placed"] > 200                          # particles actually aggregate
    assert r["occ"].sum() == r["placed"] + 1          # occupied = stuck particles + seed
    assert r["rmax"] > 5                               # cluster spreads from the seed


def test_is_fractal_not_disk_or_line():
    r = grow(size=261, n_particles=6000, seed=0)
    _, _, D = fractal_dimension(r["occ"], r["center"], rmin=6, rmax=int(r["rmax"] * 0.7))
    assert 1.3 < D < 1.9                               # genuinely fractal (line=1, filled disk=2)


def test_lower_sticking_is_denser():
    # same size/N: very low sticking lets walkers penetrate deep -> a denser cluster -> higher D
    # (the effect is clear at the extremes; near stick=1 it is small/noisy)
    d_high = fractal_dimension(grow(171, 3000, stick=1.0, seed=1)["occ"], 85, rmin=6)[2]
    d_low = fractal_dimension(grow(171, 3000, stick=0.03, seed=1)["occ"], 85, rmin=6)[2]
    assert d_low > d_high + 0.1


def test_line_seed_grows_upward():
    r = grow(size=160, n_particles=4000, seed=2, seed_shape="line")
    top = np.nonzero(r["occ"])[0].min()
    assert top < 160 - 2 - 20                          # the deposit grows well above the seed line


def test_arrival_order_consistent():
    r = grow(size=101, n_particles=800, seed=3)
    assert np.all((r["order"] >= 0) == r["occ"])       # order set exactly where occupied
    assert r["order"].max() <= 800


def test_reproducible():
    a = grow(size=121, n_particles=600, seed=5)["occ"]
    b = grow(size=121, n_particles=600, seed=5)["occ"]
    assert np.array_equal(a, b)
