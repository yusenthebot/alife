import numpy as np

from alife.murmuration import MurmurConfig, run
from dataclasses import replace

BASE = MurmurConfig(N=140, steps=800, seed=1)


def test_fleeing_protects_the_flock():
    on = run(BASE)
    off = run(replace(BASE, flee=0.0))
    assert off["catches"] > 10 * max(on["catches"], 1)        # collective evasion -> far fewer catches


def test_fleeing_keeps_distance_from_predator():
    on = run(BASE)
    off = run(replace(BASE, flee=0.0))
    assert on["near_dist"].mean() > off["near_dist"].mean()


def test_flock_more_clustered_than_uniform():
    r = run(BASE)
    uniform = BASE.L / np.sqrt(6)                            # RMS-from-centroid of a uniform box fill
    assert r["spread"] < uniform                            # prey clump, not spread uniformly


def test_flock_is_polarized():
    r = run(BASE)
    random_pol = 1.0 / np.sqrt(BASE.N)                       # ~0.085 for N=140
    assert r["polarization"] > 2.0 * random_pol             # clearly aligned, well above random heading


def test_respawn_holds_flock_size():
    r = run(replace(BASE, steps=500))
    assert r["p"].shape[0] == BASE.N                         # caught prey respawn -> N constant


def test_positions_in_box():
    r = run(replace(BASE, steps=400))
    assert r["p"].min() >= 0 and r["p"].max() < BASE.L


def test_reproducible():
    a = run(replace(BASE, steps=300))["p"]
    b = run(replace(BASE, steps=300))["p"]
    assert np.array_equal(a, b)
