"""R26 — the memory win: a task where reactive policies provably fail.

R6 tried to show that recurrent (memory) brains beat memoryless ones, and got an
honest negative: the foraging tasks there didn't *require* memory, so reactive
policies stayed competitive. This is the rematch with a task built so memory is
unavoidable — a delayed-cue latch.

A creature gets a directional cue at the very start of a foraging bout ("food is
that way"). The cue then vanishes. After a delay it reaches a junction and must
commit to a direction. At the decision step the observation is [0, go=1] — the
SAME for both cue directions. So a feedforward brain, which sees only the current
observation, is mathematically incapable of doing better than chance (0.5). A
recurrent brain can store the cue in its hidden state and act on it.

Both brain types are evolved by the identical GA on the identical task. The
separation — RNN -> ~1.0, FF pinned at 0.5 — is the memory win R6 never got, and
it is a provable separation, not a tuning artifact.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from alife.brain import (
    BrainSpec,
    RecurrentSpec,
    forward,
    forward_recurrent,
    mutate_brains,
    random_brains,
)

N_IN = 2   # [cue, go]
N_OUT = 1  # signed action; sign must match the cue


@dataclass(frozen=True)
class MemoryTaskConfig:
    delay: int = 4          # blank steps between cue and decision
    n_hidden: int = 8
    pop: int = 200
    generations: int = 120
    n_episodes: int = 24    # balanced +/- cues evaluated per brain per generation
    elite_frac: float = 0.1
    parent_frac: float = 0.3
    mut_rate: float = 0.25
    mut_sigma: float = 0.4


def _episode_inputs(cue: float, delay: int) -> np.ndarray:
    """Observation stream for one episode: cue at t=0, blanks, go-flag at the end."""
    T = delay + 2
    x = np.zeros((T, N_IN))
    x[0, 0] = cue          # cue shown only at the first step
    x[-1, 1] = 1.0         # go-signal only at the decision step
    return x


def _decisions_ff(w: np.ndarray, spec: BrainSpec, cue: float, delay: int) -> np.ndarray:
    """Final-step output of every FF brain for one episode. (N,)"""
    x = _episode_inputs(cue, delay)
    out = None
    for t in range(x.shape[0]):
        xt = np.tile(x[t], (w.shape[0], 1))
        out = forward(w, spec, xt)[:, 0]
    return out  # only the decision-step output matters


def _decisions_rnn(w: np.ndarray, spec: RecurrentSpec, cue: float, delay: int) -> np.ndarray:
    """Final-step output of every RNN brain for one episode, hidden state carried."""
    x = _episode_inputs(cue, delay)
    hidden = np.zeros((w.shape[0], spec.n_hidden))
    out = None
    for t in range(x.shape[0]):
        xt = np.tile(x[t], (w.shape[0], 1))
        out, hidden = forward_recurrent(w, spec, xt, hidden)
        out = out[:, 0]
    return out


def evaluate(w, spec, recurrent: bool, cues: np.ndarray, delay: int):
    """Return (fitness, accuracy) per brain over the given cues."""
    decide = _decisions_rnn if recurrent else _decisions_ff
    fit = np.zeros(w.shape[0])
    acc = np.zeros(w.shape[0])
    for cue in cues:
        out = decide(w, spec, float(cue), delay)
        fit += np.tanh(out * cue)              # graded: reward sign match
        acc += (np.sign(out) == np.sign(cue))  # 0/1 correct
    return fit / cues.size, acc / cues.size


def _balanced_cues(n: int) -> np.ndarray:
    half = n // 2
    return np.concatenate([np.full(half, 1.0), np.full(n - half, -1.0)])


@dataclass(frozen=True)
class MemoryResult:
    best: np.ndarray        # per-generation best accuracy
    mean: np.ndarray        # per-generation mean accuracy
    held_out: float         # final best brain's accuracy on fresh cues
    brain: np.ndarray       # the evolved best weight vector
    spec: object            # its BrainSpec / RecurrentSpec
    recurrent: bool


def evolve(cfg: MemoryTaskConfig, recurrent: bool, seed: int = 0) -> MemoryResult:
    """Evolve a population on the delayed-cue task. Returns per-gen best/mean accuracy
    and the held-out accuracy of the final best brain on fresh cues."""
    rng = np.random.default_rng(seed)
    spec = (RecurrentSpec(N_IN, cfg.n_hidden, N_OUT) if recurrent
            else BrainSpec(N_IN, cfg.n_hidden, N_OUT))
    w = random_brains(cfg.pop, spec, rng)
    cues = _balanced_cues(cfg.n_episodes)
    n_elite = max(1, int(cfg.elite_frac * cfg.pop))
    n_parent = max(2, int(cfg.parent_frac * cfg.pop))
    best_hist, mean_hist = [], []
    best_w = w[0].copy()
    for _ in range(cfg.generations):
        fit, acc = evaluate(w, spec, recurrent, cues, cfg.delay)
        order = np.argsort(fit)[::-1]
        best_hist.append(float(acc[order[0]])); mean_hist.append(float(acc.mean()))
        best_w = w[order[0]].copy()
        elite = w[order[:n_elite]]
        parents = w[order[:n_parent]]
        # fill the rest by mutating random parents
        kids = parents[rng.integers(0, n_parent, cfg.pop - n_elite)]
        kids = mutate_brains(kids, rng, cfg.mut_rate, cfg.mut_sigma)
        w = np.vstack([elite, kids])
    # held-out: a fresh, larger balanced cue set the GA never optimized against
    ho_cues = _balanced_cues(200)
    _, ho_acc = evaluate(best_w[None, :], spec, recurrent, ho_cues, cfg.delay)
    return MemoryResult(np.array(best_hist), np.array(mean_hist), float(ho_acc[0]),
                        best_w, spec, recurrent)


def delay_sweep(cfg: MemoryTaskConfig, delays, seed: int = 0):
    """Held-out accuracy of FF vs RNN across increasing memory delays."""
    ff, rnn = [], []
    for d in delays:
        c = MemoryTaskConfig(delay=int(d), n_hidden=cfg.n_hidden, pop=cfg.pop,
                             generations=cfg.generations, n_episodes=cfg.n_episodes,
                             elite_frac=cfg.elite_frac, parent_frac=cfg.parent_frac,
                             mut_rate=cfg.mut_rate, mut_sigma=cfg.mut_sigma)
        ff.append(evolve(c, recurrent=False, seed=seed).held_out)
        rnn.append(evolve(c, recurrent=True, seed=seed).held_out)
    return np.array(ff), np.array(rnn)


def hidden_trace(res: MemoryResult, cue: float, delay: int) -> np.ndarray:
    """Hidden-state trajectory of an evolved RNN for one cue — memory made visible.
    Returns (T, n_hidden)."""
    assert res.recurrent, "hidden_trace needs a recurrent brain"
    x = _episode_inputs(cue, delay)
    w = res.brain[None, :]
    hidden = np.zeros((1, res.spec.n_hidden))
    trace = []
    for t in range(x.shape[0]):
        xt = np.tile(x[t], (1, 1))
        _, hidden = forward_recurrent(w, res.spec, xt, hidden)
        trace.append(hidden[0].copy())
    return np.array(trace)

