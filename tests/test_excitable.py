import numpy as np

from alife.excitable import (gh_step, run, planar_wave_ic, two_wave_ic, spiral_ic,
                             wavefront_speed, dominant_period)

K = 8


def test_refractory_cycle_advances():
    # an isolated refractory cell advances one step and wraps k-1 -> 0; isolated rest stays rest
    s = np.zeros((3, 3), np.int32)
    s[1, 1] = 3
    assert gh_step(s, K)[1, 1] == 4
    s[1, 1] = K - 1
    assert gh_step(s, K)[1, 1] == 0                  # end of refractory -> resting
    assert gh_step(np.zeros((3, 3), np.int32), K).sum() == 0   # quiescent stays quiescent


def test_resting_cell_fires_from_excited_neighbour():
    s = np.zeros((3, 3), np.int32)
    s[1, 1] = 1                                       # one excited cell
    nxt = gh_step(s, K, thresh=1)
    assert nxt[0, 1] == 1 and nxt[1, 0] == 1         # neighbours ignite
    assert nxt[1, 1] == 2                             # the firing cell enters refractory


def test_planar_wave_constant_speed():
    f, _ = run(planar_wave_ic(80, 160, K, col=6), K, steps=100, record_every=4)
    assert abs(wavefront_speed(f, 4) - 1.0) < 0.15   # ~1 cell/step for Moore thresh=1


def test_colliding_waves_annihilate():
    _, act = run(two_wave_ic(100, 200, K, gap=40), K, steps=160, record_every=160)
    assert act[0] > 0                                 # waves present initially
    assert act[-1] == 0                               # collide on refractory tails -> gone


def test_broken_wave_reenters_but_planar_dies():
    # the headline + its control, in one test (same medium, same params)
    _, spiral = run(spiral_ic(140, 140, K), K, steps=500, record_every=500)
    _, planar = run(planar_wave_ic(140, 140, K, col=6), K, steps=500, record_every=500)
    assert spiral[250:].min() > 0                     # spiral self-sustains (re-entry)
    assert planar[-1] == 0                            # uncut wave exits and dies (no re-entry)
    assert dominant_period(spiral, burn=120) > 1      # the spiral has a rotation period


def test_deterministic():
    a = run(spiral_ic(60, 60, K), K, steps=60, record_every=60)[1]
    b = run(spiral_ic(60, 60, K), K, steps=60, record_every=60)[1]
    assert np.array_equal(a, b)
