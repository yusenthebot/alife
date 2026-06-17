"""Tests for recurrent (memory-capable) brains and the memory-task harnesses.

These verify the MACHINERY (recurrence is real, state persists and changes
behavior, the task evaluators run) — not that memory wins, which R6 found is NOT
robust (reactive strategies stay competitive; see progress.md). The point of the
infrastructure is to be correct and reusable, whatever the evolutionary outcome.
"""

from __future__ import annotations

import numpy as np

from alife import brain, sensors
from alife.brain import RecurrentSpec
from alife.evolve import EvolveConfig
from alife.memory import Occlusion, evolve_task, forage_occluded, nest_forage
from alife.neuro import NeuroConfig
from alife.world import World


def _spec() -> RecurrentSpec:
    return RecurrentSpec(n_in=sensors.n_inputs(), n_hidden=8, n_out=2)


def test_recurrent_weight_count():
    s = RecurrentSpec(n_in=13, n_hidden=8, n_out=2)
    assert s.n_weights == 13 * 8 + 8 * 8 + 8 + 8 * 2 + 2  # 194


def test_forward_recurrent_shapes():
    s = _spec()
    rng = np.random.default_rng(0)
    w = brain.random_brains(20, s, rng)
    x = rng.normal(size=(20, s.n_in))
    h = np.zeros((20, s.n_hidden))
    out, h2 = brain.forward_recurrent(w, s, x, h)
    assert out.shape == (20, 2) and h2.shape == (20, 8)
    assert np.all(np.isfinite(out)) and np.all(np.isfinite(h2))


def test_hidden_state_changes_output():
    """Recurrence is real: output depends on hidden state, not only input."""
    s = _spec()
    rng = np.random.default_rng(1)
    w = brain.random_brains(16, s, rng)
    x = rng.normal(size=(16, s.n_in))
    out_a, _ = brain.forward_recurrent(w, s, x, np.zeros((16, s.n_hidden)))
    out_b, _ = brain.forward_recurrent(w, s, x, np.ones((16, s.n_hidden)))
    assert not np.allclose(out_a, out_b)


def test_memory_persists_under_constant_input():
    """With constant input, a recurrent net's output still evolves over time."""
    s = _spec()
    rng = np.random.default_rng(2)
    w = brain.random_brains(16, s, rng)
    x = rng.normal(size=(16, s.n_in))
    h = np.zeros((16, s.n_hidden))
    out1, h = brain.forward_recurrent(w, s, x, h)
    out2, h = brain.forward_recurrent(w, s, x, h)
    assert not np.allclose(out1, out2)  # dynamics carried by hidden state


def test_forage_occluded_runs():
    s = _spec()
    cfg = NeuroConfig(world=World(160.0, 160.0, toroidal=True))
    w = brain.random_brains(12, s, np.random.default_rng(0))
    fit = forage_occluded(w, s, cfg, Occlusion(6, 10), n_food=120, steps=120, seed=1, recurrent=True)
    assert fit.shape == (12,) and (fit >= 0).all()


def test_nest_forage_runs():
    s = _spec()
    cfg = NeuroConfig(world=World(200.0, 200.0, toroidal=True), sense_range=34.0)
    w = brain.random_brains(12, s, np.random.default_rng(0))
    dep = nest_forage(w, s, cfg, n_food=150, steps=150, seed=1, recurrent=True)
    assert dep.shape == (12,) and (dep >= 0).all()


def test_evolve_task_runs_and_improves_or_finite():
    s = _spec()
    cfg = NeuroConfig(world=World(180.0, 180.0, toroidal=True), sense_range=34.0)
    ec = EvolveConfig(pop=60, generations=8, eval_steps=160, n_food=160)
    brains, hist = evolve_task(nest_forage, s, cfg, ec, recurrent=True, seed=0, nest_sense=20.0)
    assert brains.shape == (60, s.n_weights)
    assert np.all(np.isfinite(hist))
