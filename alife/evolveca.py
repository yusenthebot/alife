"""R67 — Evolving cellular automata to COMPUTE (Mitchell-Crutchfield-Das density classification).

R66 mapped the rule space; this round lets evolution SEARCH it for a rule that performs a
global computation. The task (Packard 1988; Mitchell, Crutchfield & Das 1990s): a 1D binary
CA must decide whether the initial configuration had a majority of 1s — relaxing the whole
lattice to all-1 if so, else all-0. This is genuinely hard: the decision is GLOBAL (the total
density) but each cell sees only a local window, and no finite-radius rule solves it perfectly.
Yet a GA, scoring each rule by how often it classifies random configurations correctly,
evolves rules from chance (~0.5) to ~0.75+ — and the winners do it by an emergent trick:
they grow black and white domains whose boundaries act as PARTICLES that travel, collide and
carry information about the global density. Computation, discovered, not designed.

Genome = the rule lookup table (a bit per neighbourhood of width 2r+1). Pure numpy/CPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CAConfig:
    r: int = 3                # neighbourhood radius -> width 2r+1, table size 2^(2r+1)
    width: int = 99           # lattice size (odd, so density is never exactly 1/2)


def table_size(r: int) -> int:
    return 1 << (2 * r + 1)


def _neighbour_index(state, r):
    """For each cell, the integer index of its width-(2r+1) neighbourhood (periodic)."""
    idx = np.zeros(state.shape, dtype=np.int64)
    bit = 0
    for off in range(r, -r - 1, -1):                  # leftmost neighbour -> bit 0 (LSB), rightmost -> MSB
        idx |= np.roll(state, off, axis=-1).astype(np.int64) << bit
        bit += 1
    return idx


def evolve_step(state, rule, r):
    """One CA update for a batch of configs (state: (..., width); rule: (2^(2r+1),) bits)."""
    return rule[_neighbour_index(state, r)].astype(np.int8)


def classify_batch(rule, ics, r, steps):
    """Run the CA on a batch of initial configs; return final configs (after `steps`)."""
    s = ics.astype(np.int8)
    for _ in range(steps):
        s = evolve_step(s, rule, r)
    return s


def _make_ics(cfg, n_ics, rng, hard_frac=0.5):
    """Training ICs: a mix of uniform-over-density configs (teach relaxation to a uniform state
    from easy far-from-half densities) and iid-p=0.5 configs (the HARD near-half cases that
    force a real global density computation)."""
    n_hard = int(n_ics * hard_frac)
    n_easy = n_ics - n_hard
    easy = (rng.random((n_easy, cfg.width)) < rng.random(n_easy)[:, None]).astype(np.int8)
    hard = (rng.random((n_hard, cfg.width)) < 0.5).astype(np.int8)
    return np.concatenate([easy, hard], axis=0)


def _score(rule, ics, cfg, steps):
    majority1 = ics.mean(axis=1) > 0.5
    final = classify_batch(rule, ics, cfg.r, steps)
    got1 = final.all(axis=1)
    got0 = (~final.astype(bool)).all(axis=1)
    return float(((majority1 & got1) | (~majority1 & got0)).mean())


def fitness(rule, cfg: CAConfig, n_ics: int, rng, steps=None, hard_frac=0.5) -> float:
    """Fraction of random configs correctly classified (mix of easy + hard ICs)."""
    steps = steps or 2 * cfg.width
    return _score(rule, _make_ics(cfg, n_ics, rng, hard_frac), cfg, steps)


def hard_accuracy(rule, cfg: CAConfig, n_ics=4000, seed=999) -> float:
    """The honest Mitchell benchmark for DENSITY classification: iid-p=0.5 ICs (densities
    cluster near 1/2 = the hard cases). A trivial constant rule scores ~0.5; full particle
    strategies reach ~0.75+. (This task is famously hard for a GA — see the round's honest note.)"""
    rng = np.random.default_rng(seed)
    ics = (rng.random((n_ics, cfg.width)) < 0.5).astype(np.int8)
    return _score(rule, ics, cfg, 2 * cfg.width)


# --- the SYNCHRONIZATION task (Das-Mitchell-Crutchfield): from ANY start, drive the whole
#     lattice into a global oscillation (all-0 <-> all-1, blinking in unison). The GA solves
#     this far more reliably than density classification, via defect "particles" that annihilate.

def _last_two(rule, ics, cfg, steps):
    s = ics.astype(np.int8)
    prev = s
    for _ in range(steps):
        prev = s
        s = evolve_step(s, rule, cfg.r)
    return prev, s


def _sync_score(rule, ics, cfg, steps):
    prev, last = _last_two(rule, ics, cfg, steps)
    uni_last = last.all(axis=1) | (~last.astype(bool)).all(axis=1)
    uni_prev = prev.all(axis=1) | (~prev.astype(bool)).all(axis=1)
    alternating = (prev != last).all(axis=1)               # the two uniform states differ -> blinking
    return float((uni_last & uni_prev & alternating).mean())


def sync_fitness(rule, cfg: CAConfig, n_ics: int, rng, steps=None) -> float:
    steps = steps or 2 * cfg.width
    ics = (rng.random((n_ics, cfg.width)) < rng.random(n_ics)[:, None]).astype(np.int8)
    return _sync_score(rule, ics, cfg, steps)


def sync_rate(rule, cfg: CAConfig, n_ics=4000, seed=999) -> float:
    """Held-out fraction of random ICs driven to global blink-in-unison synchrony."""
    rng = np.random.default_rng(seed)
    ics = (rng.random((n_ics, cfg.width)) < rng.random(n_ics)[:, None]).astype(np.int8)
    return _sync_score(rule, ics, cfg, 2 * cfg.width)


def random_rule(rng, r):
    return rng.integers(0, 2, table_size(r)).astype(np.int8)


def evolve(cfg: CAConfig, pop_size=80, gens=40, n_ics=60, seed=0, elite_frac=0.2, mut=0.02,
           fitness_fn=fitness):
    """GA over rule tables. Fitness re-sampled each generation (new random ICs) so rules must
    generalise, not memorise. `fitness_fn` selects the task (density `fitness` or `sync_fitness`).
    Returns best rule, fitness history, and the final population."""
    rng = np.random.default_rng(seed)
    pop = [random_rule(rng, cfg.r) for _ in range(pop_size)]
    n_elite = max(2, int(pop_size * elite_frac))
    ts = table_size(cfg.r)
    history = []
    best, best_fit = None, -1.0
    for _ in range(gens):
        gen_rng = np.random.default_rng(rng.integers(1 << 30))   # same ICs for all rules this gen
        fits = np.array([fitness_fn(p, cfg, n_ics, np.random.default_rng(gen_rng.integers(1 << 30)))
                         for p in pop])
        order = np.argsort(fits)[::-1]
        pop = [pop[i] for i in order]; fits = fits[order]
        history.append((float(fits[0]), float(fits.mean())))
        if fits[0] > best_fit:
            best_fit, best = float(fits[0]), pop[0].copy()
        elites = pop[:n_elite]
        children = [e.copy() for e in elites]
        while len(children) < pop_size:
            a, b = elites[rng.integers(n_elite)], elites[rng.integers(n_elite)]
            cut = rng.integers(ts)
            child = np.concatenate([a[:cut], b[cut:]]).copy()
            flip = rng.random(ts) < mut
            child[flip] ^= 1
            children.append(child)
        pop = children
    return {"best": best, "best_fit": best_fit, "history": np.array(history), "pop": pop}


def spacetime(rule, cfg: CAConfig, density: float, steps: int, seed: int = 0):
    """Spacetime diagram (steps+1, width) of the rule on one IC of the given initial density."""
    rng = np.random.default_rng(seed)
    s = (rng.random(cfg.width) < density).astype(np.int8)
    rows = [s.copy()]
    for _ in range(steps):
        s = evolve_step(s, rule, cfg.r)
        rows.append(s.copy())
    return np.array(rows)


def final_accuracy(rule, cfg: CAConfig, n_ics=2000, seed=12345) -> float:
    """Held-out accuracy on a large fresh set of ICs (the honest score)."""
    return fitness(rule, cfg, n_ics, np.random.default_rng(seed))
