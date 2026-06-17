"""Evolution of communication — the Lewis signalling game.

How does a signal come to *mean* something, with no shared code to start? Each
individual is born with a random SENDER map (world-state → signal) and a random
RECEIVER map (signal → action). They pair up: the sender sees the state and emits
a signal, the receiver sees only the signal and acts; both are rewarded when the
action matches the state. Selection over these maps drives the population to a
shared signalling convention — signals acquire meaning, and the mutual
information between state and signal climbs from zero toward its maximum. This is
the textbook origin-of-meaning result, evolved from scratch.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SignalConfig:
    k: int = 4               # states = signals = actions
    pop: int = 200
    generations: int = 120
    partners: int = 10       # random partners each individual plays per generation
    elite_frac: float = 0.3
    mut_rate: float = 0.05   # per-gene resample probability (low => converge on one convention)


def _success(senders, receivers, k):
    """success[i, j] = fraction of states where receiver j decodes sender i correctly."""
    states = np.arange(k)
    sent = senders[:, states]                       # (P, k) signal per state
    # receiver j action on sender i's signals: receivers[j, sent[i]] -> (P_i, P_j, k)
    acts = receivers[:, sent]                        # (P_j, P_i, k)
    correct = (acts == states[None, None, :]).mean(2)  # (P_j, P_i)
    return correct.T                                 # (P_i sender, P_j receiver)


def mutual_information(senders, k):
    """I(state; signal) in bits, given the population's senders (uniform states)."""
    joint = np.zeros((k, k))                          # P(state, signal)
    for s in range(k):
        sig = senders[:, s]
        for m in range(k):
            joint[s, m] = (sig == m).mean()
    joint /= joint.sum()
    ps = joint.sum(1, keepdims=True); pm = joint.sum(0, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        terms = joint * np.log2(joint / (ps * pm))
    return float(np.nansum(terms))


def evolve(cfg: SignalConfig, seed: int = 0):
    rng = np.random.default_rng(seed)
    senders = rng.integers(0, cfg.k, (cfg.pop, cfg.k))
    receivers = rng.integers(0, cfg.k, (cfg.pop, cfg.k))
    n_elite = max(1, int(cfg.pop * cfg.elite_frac))
    hist_success, hist_mi = [], []

    for _ in range(cfg.generations):
        succ = _success(senders, receivers, cfg.k)    # (P sender, P receiver)
        # each individual's fitness: avg as sender (random receivers) + as receiver (random senders)
        rp = rng.integers(0, cfg.pop, (cfg.pop, cfg.partners))
        as_sender = succ[np.arange(cfg.pop)[:, None], rp].mean(1)
        as_recv = succ[rp, np.arange(cfg.pop)[:, None]].mean(1)
        fit = as_sender + as_recv
        hist_success.append(float(succ[np.arange(cfg.pop), np.arange(cfg.pop)].mean()))  # self-play success
        hist_mi.append(mutual_information(senders, cfg.k))

        order = np.argsort(fit)[::-1][:n_elite]
        es, er = senders[order], receivers[order]
        idx = rng.integers(0, n_elite, cfg.pop - n_elite)
        cs, cr = es[idx].copy(), er[idx].copy()
        ms = rng.random(cs.shape) < cfg.mut_rate
        cr_m = rng.random(cr.shape) < cfg.mut_rate
        cs[ms] = rng.integers(0, cfg.k, ms.sum())
        cr[cr_m] = rng.integers(0, cfg.k, cr_m.sum())
        senders = np.vstack([es, cs]); receivers = np.vstack([er, cr])

    succ = _success(senders, receivers, cfg.k)
    hist_success.append(float(succ[np.arange(cfg.pop), np.arange(cfg.pop)].mean()))
    hist_mi.append(mutual_information(senders, cfg.k))
    return senders, receivers, np.array(hist_success), np.array(hist_mi)
