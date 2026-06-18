import numpy as np

from alife.genprog import (
    eval_tree, random_tree, size, depth, crossover, mutate, rmse, stringify, evolve,
)


def test_eval_tree():
    x = np.array([0.0, 1.0, 2.0])
    assert np.allclose(eval_tree(("+", "x", 1.0), x), x + 1)
    assert np.allclose(eval_tree(("*", "x", "x"), x), x * x)
    assert np.allclose(eval_tree(("sin", "x"), x), np.sin(x))


def test_protected_division_no_inf():
    x = np.array([0.0, 1.0])
    out = eval_tree(("/", 1.0, "x"), x)               # divide by zero at x=0
    assert np.all(np.isfinite(out))


def test_size_depth():
    t = ("+", ("*", "x", "x"), 1.0)
    assert size(t) == 5 and depth(t) == 2              # + * x x 1.0 ; depth 2


def test_crossover_mutate_valid():
    rng = np.random.default_rng(0)
    x = np.linspace(-2, 2, 10)
    a, b = random_tree(rng, 4), random_tree(rng, 4)
    for _ in range(20):
        c = crossover(a, b, rng)
        m = mutate(a, rng)
        assert np.all(np.isfinite(np.nan_to_num(eval_tree(c, x))))  # still evaluable
        assert size(m) >= 1


def test_evolve_recovers_quadratic():
    x = np.linspace(-3, 3, 40)
    y = x ** 2 + x                                     # an easy target
    r = evolve(x, y, pop_size=300, gens=40, seed=1)
    assert r["rmse"] < 0.3                             # evolution fits the hidden function well


def test_evolve_error_decreases():
    x = np.linspace(-3, 3, 40)
    y = x ** 2 + np.sin(2 * x)
    r = evolve(x, y, pop_size=300, gens=40, seed=2)
    assert r["history"][-1, 0] < r["history"][0, 0]   # best error improves over generations


def test_stringify_and_reproducible():
    x = np.linspace(-2, 2, 20); y = x * x
    a = evolve(x, y, pop_size=120, gens=15, seed=3)["best"]
    b = evolve(x, y, pop_size=120, gens=15, seed=3)["best"]
    assert stringify(a) == stringify(b)               # deterministic given the seed
