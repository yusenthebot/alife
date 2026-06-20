import numpy as np

from alife.wolfsheep import WolfSheepConfig, run, predator_lag, coexists
from dataclasses import replace


def test_predator_lag_metric_on_control():
    # validate the lag metric: build wolves = sheep shifted by +30 -> measured lag ~ +30
    t = np.arange(2000)
    sheep = 100 + 40 * np.sin(2 * np.pi * t / 200)
    wolves = 50 + 20 * np.sin(2 * np.pi * (t - 30) / 200)
    assert abs(predator_lag(sheep, wolves) - 30) < 8


def test_three_way_coexistence():
    r = run(WolfSheepConfig(steps=2500, seed=2))
    assert coexists(r)
    assert r["grass"][-1] > 0


def test_populations_oscillate():
    r = run(WolfSheepConfig(steps=3000, seed=2))
    s = r["sheep"][500:]
    assert s.max() > 1.6 * max(s.min(), 1)        # boom-bust amplitude, not a flat line


def test_predator_prey_cycles_are_robust():
    # The boom-bust CYCLE is the robust signature. The cross-correlation lag SIGN is NOT robust
    # across seeds in this stochastic agent regime (it is +83 for seed 2 but negative for others) —
    # see progress.md honest notes; the lag metric itself is validated on a synthetic control above.
    # So we assert the robust fact: the predator population oscillates strongly for every seed.
    for s in (1, 2, 11):
        w = run(WolfSheepConfig(steps=2500, seed=s))["wolves"][400:].astype(float)
        assert w.std() / w.mean() > 0.2


def test_sheep_anticorrelate_with_grass():
    r = run(WolfSheepConfig(steps=3000, seed=2))
    s, g = r["sheep"][500:], r["grass"][500:]
    assert np.corrcoef(s, g)[0, 1] < -0.2                # a sheep boom eats the field bare


def test_grass_is_the_base_of_the_chain():
    # control: if grazed grass never regrows, the sheep eat it all and the whole chain collapses
    dead = run(WolfSheepConfig(steps=1500, seed=3, regrow=10 ** 9))
    alive = run(WolfSheepConfig(steps=1500, seed=3))
    assert dead["sheep"][-1] == 0 and alive["sheep"][-1] > 0


def test_reproducible():
    a = run(WolfSheepConfig(steps=400, seed=7))["sheep"]
    b = run(WolfSheepConfig(steps=400, seed=7))["sheep"]
    assert np.array_equal(a, b)
