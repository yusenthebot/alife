"""R72 — Genetic programming: evolution discovers an equation (Koza symbolic regression).

Every GA so far evolved a FIXED-structure genome — a float vector, a rule table, a bit string,
a force matrix. Genetic programming (Koza) evolves variable-structure PROGRAMS: expression
trees built from operators (+ - * / sin cos) and terminals (the variable x, constants). Given
only (x, y) samples of a hidden function, a tree-GA — tournament selection, subtree crossover,
subtree mutation — rediscovers a formula that reproduces the data. The genotype is a program
and the search space is open-ended in size and shape: evolution writes its own equations.

Pure numpy/CPU. Trees are nested tuples: 'x', a float constant, or (op, child[, child]).
"""

from __future__ import annotations

import numpy as np

BINARY = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / np.where(np.abs(b) < 1e-6, 1e-6, b),   # protected division
}
UNARY = {"sin": np.sin, "cos": np.cos}
FUNCS = list(BINARY) + list(UNARY)


def eval_tree(t, x):
    if t == "x":
        return x
    if isinstance(t, (int, float)):
        return np.full_like(x, float(t))
    op = t[0]
    if op in BINARY:
        return BINARY[op](eval_tree(t[1], x), eval_tree(t[2], x))
    return UNARY[op](eval_tree(t[1], x))


def random_tree(rng, max_depth=4, full=False):
    if max_depth == 0 or (not full and rng.random() < 0.3):
        return "x" if rng.random() < 0.6 else round(float(rng.uniform(-2, 2)), 2)
    op = rng.choice(FUNCS)
    if op in BINARY:
        return (op, random_tree(rng, max_depth - 1, full), random_tree(rng, max_depth - 1, full))
    return (op, random_tree(rng, max_depth - 1, full))


def size(t):
    if t == "x" or isinstance(t, (int, float)):
        return 1
    return 1 + sum(size(c) for c in t[1:])


def depth(t):
    if t == "x" or isinstance(t, (int, float)):
        return 0
    return 1 + max(depth(c) for c in t[1:])


def _paths(t, prefix=()):
    """All node addresses (paths of child-indices) in the tree."""
    out = [prefix]
    if not (t == "x" or isinstance(t, (int, float))):
        for i, c in enumerate(t[1:], start=1):
            out += _paths(c, prefix + (i,))
    return out


def get_at(t, path):
    for i in path:
        t = t[i]
    return t


def set_at(t, path, new):
    if not path:
        return new
    i = path[0]
    return tuple(set_at(c, path[1:], new) if k == i else c for k, c in enumerate(t))


def crossover(a, b, rng):
    pa = _paths(a)[rng.integers(len(_paths(a)))]
    pb = _paths(b)[rng.integers(len(_paths(b)))]
    return set_at(a, pa, get_at(b, pb))


def mutate(t, rng, max_depth=3):
    p = _paths(t)[rng.integers(len(_paths(t)))]
    return set_at(t, p, random_tree(rng, max_depth=rng.integers(1, max_depth + 1)))


def rmse(t, x, y):
    pred = np.nan_to_num(eval_tree(t, x), nan=1e6, posinf=1e6, neginf=1e6)
    return float(np.sqrt(np.mean((pred - y) ** 2)))


def fitness(t, x, y, parsimony=0.001):
    """Negative error with a small size penalty (parsimony pressure curbs bloat)."""
    return -rmse(t, x, y) - parsimony * size(t)


def stringify(t):
    if t == "x":
        return "x"
    if isinstance(t, (int, float)):
        return f"{t:g}"
    op = t[0]
    if op in BINARY:
        return f"({stringify(t[1])} {op} {stringify(t[2])})"
    return f"{op}({stringify(t[1])})"


def evolve(x, y, pop_size=500, gens=60, seed=0, max_depth=4, tourn=5,
           p_cross=0.7, p_mut=0.25, parsimony=0.001, max_size=60):
    """Tournament-selection tree GA. Returns best tree, history of (best_rmse, best_size)."""
    rng = np.random.default_rng(seed)
    pop = [random_tree(rng, max_depth, full=(i % 2 == 0)) for i in range(pop_size)]

    def fit(t):
        return fitness(t, x, y, parsimony)

    fits = np.array([fit(t) for t in pop])
    history = []
    best, best_f = pop[int(fits.argmax())], fits.max()

    def select():
        idx = rng.integers(0, pop_size, tourn)
        return pop[idx[np.argmax(fits[idx])]]

    for _ in range(gens):
        children = [best]                               # elitism
        while len(children) < pop_size:
            a = select()
            r = rng.random()
            if r < p_cross:
                child = crossover(a, select(), rng)
            elif r < p_cross + p_mut:
                child = mutate(a, rng)
            else:
                child = a
            if size(child) > max_size:                   # cap bloat
                child = a
            children.append(child)
        pop = children
        fits = np.array([fit(t) for t in pop])
        i = int(fits.argmax())
        if fits[i] > best_f:
            best_f, best = fits[i], pop[i]
        history.append((rmse(best, x, y), size(best)))
    return {"best": best, "history": np.array(history), "rmse": rmse(best, x, y)}
