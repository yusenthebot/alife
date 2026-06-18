"""R77 — The evolution of cooperation: iterated Prisoner's Dilemma strategy evolution.

Earlier cooperation rounds used FIXED strategies (R19 kin selection, R38 spatial reciprocity).
Here the STRATEGY itself evolves. Each agent plays the iterated Prisoner's Dilemma with a
memory-1 reactive rule: four probabilities of cooperating given last round's outcome
(p_CC, p_CD, p_DC, p_DD), which span the famous strategies — ALLD (0,0,0,0), ALLC (1,1,1,1),
Tit-for-Tat (1,0,1,0), Win-Stay-Lose-Shift / Pavlov (1,0,0,1). The expected payoff between any
two memory-1 strategies is computed exactly from the stationary distribution of their 4-state
Markov game (no simulation noise). Three results: (1) a round-robin Axelrod TOURNAMENT —
reciprocators (TFT/GRIM/WSLS) thrive among nice strategies, while ALLD profits only by
exploiting unconditional cooperators; (2) the NOISE effect — under implementation error TFT is
fragile (two TFTs fall into vendettas, cooperation collapses to ~0.5), while WSLS/Pavlov
self-corrects and stays cooperative (why Pavlov beats Tit-for-Tat in a noisy world); (3) in a
WELL-MIXED population the evolution of cooperation is CONTINGENT — runs are bistable, some
climbing to cooperation and some collapsing to defection, echoing why spatial structure (R38)
is what makes cooperation robust.

Pure numpy/CPU. T>R>P>S with 2R>T+S (the Prisoner's Dilemma).
"""

from __future__ import annotations

import numpy as np

T, R, P, S = 5.0, 3.0, 1.0, 0.0          # temptation, reward, punishment, sucker
PAYOFF = np.array([R, S, T, P])          # for own-states [CC, CD, DC, DD]

# named memory-1 strategies: P(cooperate | own last, opp last) over [CC, CD, DC, DD]
NAMED = {
    "ALLD": np.array([0, 0, 0, 0.0]),
    "ALLC": np.array([1, 1, 1, 1.0]),
    "TFT": np.array([1, 0, 1, 0.0]),     # copy opponent's last move
    "GTFT": np.array([1, 0.33, 1, 0.33]),
    "WSLS": np.array([1, 0, 0, 1.0]),    # Pavlov: repeat if last round "won" (CC or DD)
    "GRIM": np.array([1, 0, 0, 0.0]),    # cooperate until first defection, then defect forever
    "RAND": np.array([0.5, 0.5, 0.5, 0.5]),
}


def _clamp(p, eps=0.001):
    return np.clip(p, eps, 1 - eps)       # implementation error -> ergodic Markov chain


def stationary_payoff(p, q, eps=0.001):
    """Exact expected payoffs and cooperation rate for memory-1 strategies p vs q, via the
    stationary distribution of the 4-state game (states from p's view: CC, CD, DC, DD)."""
    p = _clamp(np.asarray(p, float), eps)
    q = _clamp(np.asarray(q, float), eps)
    # q sees the mirrored state: p-state CD (p=C,q=D) is q-state DC, etc. mirror index map:
    mirror = [0, 2, 1, 3]                  # CC->CC, CD->DC, DC->CD, DD->DD
    M = np.zeros((4, 4))
    for s in range(4):                     # current state (own=a, opp=b)
        pc = p[s]                          # P(own cooperates next)
        qc = q[mirror[s]]                  # P(opp cooperates next)
        # next state index: own*2 + opp with C=0,D=1 -> CC=0,CD=1,DC=2,DD=3
        M[s, 0] = pc * qc
        M[s, 1] = pc * (1 - qc)
        M[s, 2] = (1 - pc) * qc
        M[s, 3] = (1 - pc) * (1 - qc)
    # stationary distribution: solve (M^T - I) pi = 0 with sum(pi)=1 (replace one row by the
    # normalisation) — a fast 4x4 solve.
    A = M.T - np.eye(4)
    A[3] = 1.0
    b = np.array([0, 0, 0, 1.0])
    pi = np.linalg.solve(A, b)
    pi = np.clip(pi, 0, None); pi /= pi.sum()
    payoff_p = float(pi @ PAYOFF)
    payoff_q = float(pi @ PAYOFF[[0, 2, 1, 3]])   # q's payoff uses mirrored states
    coop = float(pi[0] + pi[1])                    # fraction of rounds own cooperates
    return payoff_p, payoff_q, coop


def tournament(strategies: dict, eps=0.001):
    """Round-robin (incl. self): mean payoff of each strategy against the field."""
    names = list(strategies)
    n = len(names)
    score = np.zeros((n, n))
    for i, a in enumerate(names):
        for j, b in enumerate(names):
            score[i, j] = stationary_payoff(strategies[a], strategies[b], eps)[0]
    return names, score, score.mean(axis=1)


def classify(p, tol=0.35):
    """Nearest named archetype to a memory-1 strategy vector (for reading evolved populations)."""
    best, bd = "other", 1e9
    for name in ("ALLD", "ALLC", "TFT", "WSLS", "GRIM"):
        d = np.abs(np.asarray(p) - np.round(NAMED[name])).mean()
        if d < bd:
            bd, best = d, name
    return best if bd < tol else "other"


def evolve(pop_size=200, gens=300, mut=0.06, eps=0.02, seed=0, sample=30):
    """Payoff-proportional evolution of memory-1 strategies. Fitness = mean payoff against a
    random sample of the population. Returns mean cooperation over time, mean strategy, and the
    archetype composition over time. eps = implementation error (favours self-correcting WSLS)."""
    rng = np.random.default_rng(seed)
    pop = rng.random((pop_size, 4))
    coop_hist, mean_strat, comp_hist = [], [], []
    arch = ["ALLD", "TFT", "WSLS", "ALLC", "GRIM", "other"]
    for _ in range(gens):
        # fitness vs a random sample of opponents
        fit = np.zeros(pop_size)
        coops = np.zeros(pop_size)
        for i in range(pop_size):
            opp = rng.integers(0, pop_size, sample)
            vals = [stationary_payoff(pop[i], pop[o], eps) for o in opp]
            fit[i] = np.mean([v[0] for v in vals])
            coops[i] = np.mean([v[2] for v in vals])
        coop_hist.append(float(coops.mean()))
        mean_strat.append(pop.mean(axis=0))
        labels = [classify(s) for s in pop]
        comp_hist.append([labels.count(a) / pop_size for a in arch])
        # payoff-proportional (roulette) selection + mutation
        w = fit - fit.min() + 1e-9
        parents = pop[rng.choice(pop_size, pop_size, p=w / w.sum())]
        children = np.clip(parents + mut * rng.standard_normal((pop_size, 4)), 0, 1)
        pop = children
    return {"coop": np.array(coop_hist), "mean_strat": np.array(mean_strat),
            "composition": np.array(comp_hist), "archetypes": arch, "pop": pop}
