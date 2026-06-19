"""R89 — A major transition: the evolution of division of labor.

One of evolution's great leaps (Maynard Smith & Szathmary) is the move from generalist individuals to
specialised castes inside a superorganism — workers vs reproductives, foragers vs nurses. When does
specialisation pay? The answer is a clean piece of mathematics. A colony must get two tasks done;
each member splits its effort theta in [0,1] between task A and task B, and a member's output on a
task is g(effort) with g(x)=x**alpha, g(0)=0. By Jensen's inequality, if g is CONVEX (alpha>1,
accelerating returns) a colony of SPECIALISTS — half doing only A, half only B — beats a colony of
identical generalists (everyone at theta=0.5), because g(1)/2 > g(0.5). If g is CONCAVE (alpha<1,
diminishing returns) the inequality flips and generalists win. So division of labor should evolve if
and only if returns to specialisation accelerate.

We test that prediction by evolving colonies under COLONY-LEVEL selection (a major-transition model:
the group is the unit of selection) and sweeping the convexity alpha. Pure numpy; CPU-fast.
"""

from __future__ import annotations

import numpy as np


def task_outputs(thetas, alpha):
    """Colony outputs (A, B) given each member's effort split theta. g(x)=x**alpha, g(0)=0."""
    a = np.power(thetas, alpha).sum()
    b = np.power(1.0 - thetas, alpha).sum()
    return a, b


def colony_fitness(thetas, alpha):
    """A colony needs BOTH tasks done: fitness = the limiting (smaller) output. Rewards balance."""
    a, b = task_outputs(thetas, alpha)
    return min(a, b)


def specialization_index(thetas):
    """0 = everyone a generalist (theta=0.5); 1 = everyone a full specialist (theta in {0,1})."""
    return float(np.mean(2.0 * np.abs(thetas - 0.5)))


def evolve(alpha, n_colonies=200, colony_size=20, gens=200, mut=0.05, seed=0):
    """Colony-level selection: each colony is a vector of member efforts; fitter colonies reproduce
    (copy + per-member mutation). Returns history + the final pooled effort distribution."""
    rng = np.random.default_rng(seed)
    pop = rng.uniform(0.4, 0.6, (n_colonies, colony_size))      # start as near-generalists
    spec_hist, prod_hist = [], []
    for _ in range(gens):
        fit = np.array([colony_fitness(pop[c], alpha) for c in range(n_colonies)])
        spec_hist.append(float(np.mean([specialization_index(pop[c]) for c in range(n_colonies)])))
        prod_hist.append(float(fit.mean()))
        # fitness-proportional selection of parent colonies (rank-softened to avoid degeneracy)
        order = np.argsort(fit)
        rank = np.empty(n_colonies); rank[order] = np.arange(n_colonies)
        p = (rank + 1.0); p /= p.sum()
        parents = rng.choice(n_colonies, n_colonies, p=p)
        child = pop[parents].copy()
        child += rng.normal(0, mut, child.shape)                # mutate member efforts
        pop = np.clip(child, 0.0, 1.0)
    return {"spec": np.asarray(spec_hist), "prod": np.asarray(prod_hist),
            "final_thetas": pop.ravel(), "final_spec": spec_hist[-1]}


def sweep_alpha(alphas, gens=160, seed=0, **kw):
    """Evolved specialization index as a function of convexity alpha (transition expected at alpha=1)."""
    out = []
    for i, a in enumerate(alphas):
        out.append(evolve(float(a), gens=gens, seed=seed + i, **kw)["final_spec"])
    return np.asarray(alphas, float), np.asarray(out)


def jensen_prediction(alpha):
    """Analytic: do specialists beat generalists? True iff g(1)/2 > g(0.5), i.e. 0.5 > 0.5**alpha."""
    return 0.5 > 0.5 ** alpha
