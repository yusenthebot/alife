"""Tests for generational neuroevolution — the headline R3 claim.

Selection turns random networks into competent foragers, robustly: fitness rises
across generations, and the result generalizes to a held-out food field the
brains never trained on (so it is real foraging skill, not memorization).
"""

from __future__ import annotations

import numpy as np

from alife import sensors
from alife.brain import BrainSpec
from alife.evolve import EvolveConfig, batch_forage, evolve
from alife.neuro import NeuroConfig, NeuroEcosystem
from alife.world import World


def _spec(cfg: NeuroConfig) -> BrainSpec:
    return BrainSpec(n_in=sensors.n_inputs(), n_hidden=cfg.hidden, n_out=2)


def test_batch_forage_shape_and_nonnegative():
    cfg = NeuroConfig(world=World(160.0, 160.0, toroidal=True))
    spec = _spec(cfg)
    rng = np.random.default_rng(0)
    from alife import brain
    fit = batch_forage(brain.random_brains(20, spec, rng), spec, cfg, n_food=150, steps=120, seed=1)
    assert fit.shape == (20,)
    assert (fit >= 0).all()


def test_ga_improves_fitness():
    cfg = NeuroConfig(world=World(180.0, 180.0, toroidal=True))
    spec = _spec(cfg)
    _, hist, _ = evolve(spec, cfg, EvolveConfig(pop=100, generations=22, eval_steps=220), seed=0)
    gen0_mean, final_mean = hist[0, 1], hist[-1, 1]
    assert final_mean > gen0_mean + 15.0, f"fitness should climb: {gen0_mean:.1f} -> {final_mean:.1f}"


def test_evolved_generalizes_to_heldout_field():
    """Evolved brains forage far better than random on a field never trained on."""
    cfg = NeuroConfig(world=World(180.0, 180.0, toroidal=True))
    spec = _spec(cfg)
    brains, _, gen0 = evolve(spec, cfg, EvolveConfig(pop=110, generations=28, eval_steps=240), seed=1)
    eco = NeuroEcosystem(cfg, seed=12345)        # held-out world/seed
    rand = eco.assay_brains(gen0[:24], steps=300).mean()
    evo = eco.assay_brains(brains[:24], steps=300).mean()
    assert evo > rand * 3.0, f"evolved should generalize: random {rand:.1f} -> evolved {evo:.1f}"
