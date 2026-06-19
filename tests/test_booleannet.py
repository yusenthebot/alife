import numpy as np

from alife.booleannet import (make_network, step, derrida_slope, damage_spread,
                              attractor_length, count_attractors)


def test_step_is_deterministic_and_binary():
    net = make_network(100, 3, seed=0)
    s = (np.random.default_rng(0).random(100) < 0.5).astype(np.int8)
    a, b = step(s, net), step(s.copy(), net)
    assert np.array_equal(a, b)                          # deterministic
    assert set(np.unique(a)).issubset({0, 1})


def test_derrida_slope_is_about_k_over_2():
    # the sensitivity law: slope ~ K/2 for unbiased rules
    for k in (1, 2, 4):
        s = np.mean([derrida_slope(make_network(600, k, seed=sd), trials=300, seed=sd) for sd in range(3)])
        assert abs(s - k / 2) < 0.25


def test_order_chaos_transition_at_k2():
    s1 = np.mean([derrida_slope(make_network(600, 1, seed=sd), trials=300, seed=sd) for sd in range(3)])
    s3 = np.mean([derrida_slope(make_network(600, 3, seed=sd), trials=300, seed=sd) for sd in range(3)])
    assert s1 < 1.0 < s3                                 # K=1 ordered, K=3 chaotic, K=2 between


def test_damage_heals_when_ordered_spreads_when_chaotic():
    heal = np.mean([damage_spread(make_network(600, 1, seed=sd), steps=40, seed=sd)[-1] for sd in range(5)])
    spread = np.mean([damage_spread(make_network(600, 5, seed=sd), steps=40, seed=sd)[-1] for sd in range(5)])
    assert heal < 0.02                                   # ordered: a flip dies out
    assert spread > 0.2                                  # chaotic: it avalanches


def test_ordered_attractors_are_short():
    net = make_network(120, 1, seed=0)
    clen, _ = attractor_length(net, seed=0)
    assert 0 < clen <= 4                                 # K=1: short (often fixed-point) cycles


def test_count_attractors_returns_sane_values():
    n_att, med_len = count_attractors(make_network(120, 2, seed=1), n_init=20, seed=1)
    assert 1 <= n_att <= 20 and med_len >= 1
