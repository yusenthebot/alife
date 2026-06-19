import numpy as np

from alife.schelling import init_grid, step, run, segregation, happiness, tipping_curve


def test_random_init_is_mixed():
    assert abs(segregation(init_grid(80, seed=0)) - 0.5) < 0.05   # 50/50 random ≈ 0.5


def test_zero_tolerance_stays_mixed():
    # control: agents with no preference never move -> grid stays as mixed as it started
    r = run(size=80, frac_empty=0.1, tau=0.0, steps=50, seed=1)
    assert abs(r["final_seg"] - 0.5) < 0.05
    assert r["final_happy"] == 1.0


def test_mild_preference_segregates_yet_everyone_content():
    # the headline: a mild tau drives strong segregation, but all agents end up content
    r = run(size=80, frac_empty=0.1, tau=0.3, steps=80, seed=1)
    assert r["final_seg"] > 0.65                        # far above the mixed 0.5
    assert r["final_happy"] > 0.98                      # nobody actually wanted segregation


def test_more_preference_more_segregation():
    _, seg = tipping_curve(np.array([0.1, 0.4]), size=70, steps=80, seed=3)
    assert seg[1] > seg[0] + 0.15                       # higher tau -> more segregated


def test_relocation_conserves_agents():
    rng = np.random.default_rng(0)
    g = init_grid(60, frac_empty=0.1, seed=0)
    n1, n2 = (g == 1).sum(), (g == 2).sum()
    g2, _ = step(g, 0.4, rng)
    assert (g2 == 1).sum() == n1 and (g2 == 2).sum() == n2   # agents move, never created/destroyed


def test_reproducible():
    a = run(size=50, tau=0.4, steps=30, seed=7)["final_seg"]
    b = run(size=50, tau=0.4, steps=30, seed=7)["final_seg"]
    assert a == b
