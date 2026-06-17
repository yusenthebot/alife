import numpy as np

from alife.memory_task import (
    MemoryTaskConfig,
    _episode_inputs,
    delay_sweep,
    evolve,
    hidden_trace,
)


def test_decision_step_observation_is_cue_blind():
    """The crux: at the decision step the observation is identical for both cues,
    so a feedforward brain cannot possibly distinguish them."""
    xp = _episode_inputs(+1.0, delay=4)
    xn = _episode_inputs(-1.0, delay=4)
    assert np.array_equal(xp[-1], xn[-1])      # decision-step input identical
    assert not np.array_equal(xp[0], xn[0])    # cue differs only at t=0


def test_recurrent_brain_solves_it():
    cfg = MemoryTaskConfig(delay=4, generations=120)
    rnn = evolve(cfg, recurrent=True, seed=0)
    assert rnn.held_out > 0.9


def test_feedforward_brain_is_pinned_at_chance():
    """Reactive policy provably cannot exceed chance on this task."""
    cfg = MemoryTaskConfig(delay=4, generations=120)
    ff = evolve(cfg, recurrent=False, seed=0)
    assert abs(ff.held_out - 0.5) < 0.06


def test_memory_beats_reactive_across_seeds():
    cfg = MemoryTaskConfig(delay=4, generations=120)
    for seed in (0, 1, 2):
        rnn = evolve(cfg, recurrent=True, seed=seed)
        ff = evolve(cfg, recurrent=False, seed=seed)
        assert rnn.held_out > ff.held_out + 0.3


def test_hidden_state_holds_the_cue():
    """Mechanistic check: the evolved RNN's hidden state diverges by cue and stays
    separated through the delay (it is storing the cue)."""
    cfg = MemoryTaskConfig(delay=4, generations=120)
    rnn = evolve(cfg, recurrent=True, seed=0)
    tp = hidden_trace(rnn, +1.0, cfg.delay)
    tn = hidden_trace(rnn, -1.0, cfg.delay)
    sep = np.linalg.norm(tp - tn, axis=1)
    assert sep[-1] > 0.3            # still separated at the decision step
    assert sep[-1] > sep[0] * 0.5   # memory persists, not just a transient


def test_delay_sweep_ff_flat_rnn_high_at_short_delay():
    ff, rnn = delay_sweep(MemoryTaskConfig(generations=100), [2, 4], seed=0)
    assert np.all(np.abs(ff - 0.5) < 0.08)   # FF flat at chance for all delays
    assert rnn[0] > 0.9                       # RNN solves short delays


def test_reproducible():
    cfg = MemoryTaskConfig(delay=3, generations=40)
    a = evolve(cfg, recurrent=True, seed=5)
    b = evolve(cfg, recurrent=True, seed=5)
    assert np.allclose(a.best, b.best)
