import numpy as np

from alife.divlabor import (task_outputs, colony_fitness, specialization_index,
                            evolve, sweep_alpha, jensen_prediction)


def test_jensen_prediction_matches_math():
    assert not jensen_prediction(0.5)            # concave -> generalists
    assert not jensen_prediction(1.0)            # linear -> neutral (not strictly specialists)
    assert jensen_prediction(2.0)                # convex -> specialists
    assert jensen_prediction(3.0)


def test_specialists_beat_generalists_iff_convex():
    n = 20
    specialists = np.array([0.0] * (n // 2) + [1.0] * (n // 2))   # balanced castes
    generalists = np.full(n, 0.5)
    # convex: specialist colony is fitter
    assert colony_fitness(specialists, 3.0) > colony_fitness(generalists, 3.0)
    # concave: generalist colony is fitter (inequality flips)
    assert colony_fitness(generalists, 0.5) > colony_fitness(specialists, 0.5)


def test_specialization_index_extremes():
    assert specialization_index(np.full(10, 0.5)) == 0.0           # all generalists
    assert specialization_index(np.array([0.0, 1.0, 0.0, 1.0])) == 1.0   # all specialists


def test_convex_evolves_division_of_labor():
    r = evolve(alpha=3.0, gens=200, seed=1)
    assert r["final_spec"] > 0.6                                   # specialists evolved
    assert r["prod"][-1] > 2.0 * r["prod"][0]                      # productivity rises (superadditive)
    th = r["final_thetas"]
    # bimodal: substantial mass at both extremes, little in the generalist middle
    assert np.mean(th < 0.1) > 0.2 and np.mean(th > 0.9) > 0.2
    assert np.mean((th > 0.4) & (th < 0.6)) < 0.1


def test_concave_keeps_generalists():
    r = evolve(alpha=0.5, gens=200, seed=1)
    assert r["final_spec"] < 0.4                                   # stays generalist
    assert r["prod"][-1] < 1.2 * r["prod"][0]                      # no productivity gain
    assert np.mean((r["final_thetas"] > 0.4) & (r["final_thetas"] < 0.6)) > 0.3


def test_sweep_transition_direction():
    a, s = sweep_alpha(np.array([0.5, 3.0]), gens=140, seed=5)
    assert s[1] > s[0] + 0.3                                       # far more specialised at alpha=3
