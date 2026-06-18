"""R41 — the Baldwin effect: how learning guides (and is absorbed by) evolution.

Hinton & Nowlan's famous 1987 model. A genome of 20 loci must exactly match a
single target ("the needle") to score; every other genotype is equally useless,
so the fitness landscape is a flat plain with one infinitely thin spike. Pure
evolution is blind here — it cannot climb a gradient that does not exist, and the
needle is essentially never found.

Now let some alleles be *plastic*: instead of a fixed 0 or 1, a locus can be a "?"
that the individual sets by trial and error during its lifetime. An individual
whose fixed loci are all correct can *learn* the rest, and the fewer "?"s it has,
the faster it learns — so it scores higher. Learning smooths the spike into a hill
that selection CAN climb: correct fixed alleles spread, and the "?"s are gradually
replaced by the now-known correct values. Behaviour first learned within a
lifetime becomes innate — the Baldwin effect / genetic assimilation, with no
Lamarckism (nothing learned is written back to the genome; selection does it all).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# allele encoding: 0 = fixed-wrong, 1 = fixed-correct, 2 = plastic ("?")


@dataclass(frozen=True)
class BaldwinConfig:
    pop: int = 1000
    loci: int = 20
    life_trials: int = 1000     # learning guesses per lifetime
    generations: int = 500
    p_plastic: float = 0.5      # initial fraction of "?" loci
    mut_rate: float = 0.0       # Hinton-Nowlan use recombination only


def _init(cfg: BaldwinConfig, rng, learning: bool) -> np.ndarray:
    g = np.empty((cfg.pop, cfg.loci), dtype=np.int8)
    if learning:
        r = rng.random((cfg.pop, cfg.loci))
        g[:] = np.where(r < cfg.p_plastic, 2, (r < cfg.p_plastic + (1 - cfg.p_plastic) / 2).astype(np.int8))
        # r in [p,(p+ (1-p)/2)) -> 1 (fixed correct), r>= that -> 0 (fixed wrong)
    else:
        g[:] = (rng.random((cfg.pop, cfg.loci)) < 0.5).astype(np.int8)   # only 0/1, no plasticity
    return g


def _fitness(g: np.ndarray, cfg: BaldwinConfig) -> np.ndarray:
    """Expected Hinton-Nowlan fitness. Target = all-1.
    - any fixed-wrong (0) locus  -> can never match -> base fitness 1.
    - else k plastic loci: each lifetime guess solves with prob (1/2)^k; expected
      remaining-trials reward 1 + 19*(life_trials - g_used)/life_trials, in closed form."""
    fixed_wrong = np.any(g == 0, axis=1)
    k = (g == 2).sum(axis=1)                       # plastic loci to learn
    p = 0.5 ** k                                   # prob a single guess hits the needle
    n = cfg.life_trials
    # expected fraction of trials remaining after first success (capped at n):
    # E[(n - G)/n] with G ~ geometric(p) truncated at n. With q=1-p:
    #   E[max(0, n - G)] / n  -> closed form below; if never solved within n, reward 0.
    q = 1.0 - p
    # expected (trials saved)/n = (1/(n)) * sum_{g=1..n} (n-g) p q^{g-1}
    # = (n - (1 - q^n)/p) / n   (standard truncated-geometric identity), clamped >=0
    with np.errstate(over="ignore"):
        saved = (n - (1.0 - q ** n) / p) / n
    saved = np.clip(saved, 0.0, 1.0)
    fit = np.where(fixed_wrong, 1.0, 1.0 + 19.0 * saved)
    return fit


def _solvable(g: np.ndarray) -> np.ndarray:
    """An individual can (eventually) reach the target iff no fixed-wrong locus."""
    return ~np.any(g == 0, axis=1)


def _reproduce(g: np.ndarray, fit: np.ndarray, cfg: BaldwinConfig, rng) -> np.ndarray:
    p = fit / fit.sum()
    pa = rng.choice(cfg.pop, cfg.pop, p=p)
    pb = rng.choice(cfg.pop, cfg.pop, p=p)
    mask = rng.random((cfg.pop, cfg.loci)) < 0.5
    kids = np.where(mask, g[pa], g[pb])
    if cfg.mut_rate > 0:
        flip = rng.random((cfg.pop, cfg.loci)) < cfg.mut_rate
        rand = rng.integers(0, 3, (cfg.pop, cfg.loci)).astype(np.int8)
        kids = np.where(flip, rand, kids)
    return kids


def evolve(cfg: BaldwinConfig, learning: bool = True, seed: int = 0):
    rng = np.random.default_rng(seed)
    g = _init(cfg, rng, learning)
    hist = {"correct": [], "plastic": [], "wrong": [], "solvable": [], "max_fit": []}
    for _ in range(cfg.generations):
        fit = _fitness(g, cfg)
        hist["correct"].append(float((g == 1).mean()))
        hist["plastic"].append(float((g == 2).mean()))
        hist["wrong"].append(float((g == 0).mean()))
        hist["solvable"].append(float(_solvable(g).mean()))
        hist["max_fit"].append(float(fit.max()))
        g = _reproduce(g, fit, cfg, rng)
    fit = _fitness(g, cfg)
    hist["correct"].append(float((g == 1).mean()))
    hist["plastic"].append(float((g == 2).mean()))
    hist["wrong"].append(float((g == 0).mean()))
    hist["solvable"].append(float(_solvable(g).mean()))
    hist["max_fit"].append(float(fit.max()))
    return {k: np.array(v) for k, v in hist.items()}
