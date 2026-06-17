"""Sexual selection — Fisherian runaway.

Every individual carries two heritable genes: an ornament `t` (expressed in males,
costly to survival) and a preference `p` (expressed in females, for larger
ornaments). Choosy females mate with ornamented males, so their offspring inherit
BOTH genes — a genetic correlation builds between ornament and preference. That
correlation is a positive feedback: bigger ornaments make preference pay, stronger
preference makes ornaments pay. The ornament runs away from its survival optimum
(t=0) to an exaggerated value — until the survival cost finally brakes it. Turn
off female choice and the ornament collapses back to t=0.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SexSelConfig:
    pop: int = 600
    generations: int = 300
    cost: float = 0.15       # survival cost of the ornament: exp(-cost * t^2)
    pref: float = 3.5        # strength of female preference: exp(pref * p * t)
    mut: float = 0.08
    p0_mean: float = 0.5     # seeded pre-existing preference (sensory-bias origin)
    init_std: float = 0.2


@dataclass(frozen=True)
class SexSelResult:
    ornament: np.ndarray     # mean ornament gene per generation
    preference: np.ndarray   # mean preference gene per generation
    survival: np.ndarray     # mean male survival per generation (the cost paradox)
    gene_corr: np.ndarray    # within-pop genetic correlation ornament<->preference (Fisher's engine)


def evolve(cfg: SexSelConfig, female_choice: bool, seed: int = 0) -> SexSelResult:
    rng = np.random.default_rng(seed)
    t = rng.normal(0, cfg.init_std, cfg.pop)            # ornament gene
    p = rng.normal(cfg.p0_mean, cfg.init_std, cfg.pop)  # preference gene
    hist_t, hist_p, hist_s, hist_c = [], [], [], []
    for _ in range(cfg.generations):
        sex = rng.random(cfg.pop) < 0.5          # True = male
        males = np.where(sex)[0]
        females = np.where(~sex)[0]
        hist_t.append(float(t.mean())); hist_p.append(float(p.mean()))
        hist_c.append(float(np.corrcoef(t, p)[0, 1]))   # linkage disequilibrium
        if males.size == 0 or females.size == 0:
            hist_s.append(float("nan"))
            continue
        surv = np.exp(-cfg.cost * t[males] ** 2)  # male survival (ornament is costly)
        hist_s.append(float(surv.mean()))
        # mate choice: female f picks male m ~ survival * preference
        logw = np.log(surv)[None, :]
        if female_choice:
            logw = logw + cfg.pref * np.outer(p[females], t[males])
        g = rng.gumbel(size=(females.size, males.size))   # vectorized categorical sampling
        fathers = males[np.argmax(logw + g, axis=1)]
        # each female is a mother once; offspring fill the population
        moms = rng.integers(0, females.size, cfg.pop)
        mother = females[moms]
        father = fathers[moms]
        t = (t[mother] + t[father]) / 2 + rng.normal(0, cfg.mut, cfg.pop)
        p = (p[mother] + p[father]) / 2 + rng.normal(0, cfg.mut, cfg.pop)
    hist_t.append(float(t.mean())); hist_p.append(float(p.mean()))
    hist_s.append(float(np.exp(-cfg.cost * t.mean() ** 2)))
    hist_c.append(float(np.corrcoef(t, p)[0, 1]))
    return SexSelResult(np.array(hist_t), np.array(hist_p), np.array(hist_s), np.array(hist_c))


def preference_sweep(cfg: SexSelConfig, prefs, seeds=(0, 1, 2)) -> np.ndarray:
    """Final ornament size vs preference strength — the runaway dose-response."""
    out = []
    for pr in prefs:
        c = SexSelConfig(pop=cfg.pop, generations=cfg.generations, cost=cfg.cost,
                         pref=float(pr), mut=cfg.mut, p0_mean=cfg.p0_mean,
                         init_std=cfg.init_std)
        finals = [abs(evolve(c, True, seed=s).ornament[-1]) for s in seeds]
        out.append(float(np.mean(finals)))
    return np.array(out)
