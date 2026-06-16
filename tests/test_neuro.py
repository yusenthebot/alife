"""Tests for the neuro-ecosystem.

Mechanics first (the lifecycle a dynamic population needs), then the headline:
brains evolve competence — an evolved population forages far better than the
random brains it started from, measured by a controlled assay.
"""

from __future__ import annotations

import numpy as np

from alife.neuro import NeuroConfig, NeuroEcosystem
from alife.world import World


def _lengths_match(eco: NeuroEcosystem) -> bool:
    n = eco.pos.shape[0]
    return all(a.shape[0] == n for a in (eco.heading, eco.vel, eco.energy, eco.brains,
                                         eco.generation, eco.age))


def test_step_keeps_arrays_consistent():
    eco = NeuroEcosystem(NeuroConfig(), seed=0)
    for _ in range(40):
        eco.step()
        assert _lengths_match(eco)
    assert np.all(np.isfinite(eco.pos))
    assert np.all(np.isfinite(eco.energy))
    assert np.all(np.isfinite(eco.brains))


def test_reproduction_grows_and_advances_generation():
    eco = NeuroEcosystem(NeuroConfig(n0=40), seed=1)
    eco.energy[:] = eco.cfg.e_repro + 5.0
    n0 = eco.pos.shape[0]
    eco._reproduce()
    assert eco.pos.shape[0] > n0
    assert eco.generation.max() == 1
    assert _lengths_match(eco)


def test_starvation_culls():
    eco = NeuroEcosystem(NeuroConfig(n0=30), seed=2)
    eco.energy[:6] = -1.0
    eco._cull()
    assert eco.pos.shape[0] == 24


def test_assay_runs_and_scores_nonnegative():
    eco = NeuroEcosystem(NeuroConfig(), seed=3)
    scores = eco.assay_brains(eco.brains[:6], steps=120)
    assert scores.shape == (6,)
    assert (scores >= 0).all()

# Note: foraging intelligence is evolved by the generational GA (see
# test_evolve.py). In-situ continuous-ecosystem selection was found to be too
# noisy (crowding dilutes the foraging signal), so the headline selection claim
# is tested there, not here. These tests cover only the lifecycle mechanics.
