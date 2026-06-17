"""Tests for sustained predator-prey cycles (the R5/R10 gap, resolved).

Headline: a genuine limit cycle — both species persist and the predator
population oscillates (multiple peaks), thanks to the prey refuge floor that
prevents trough-extinction.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks

from alife.cycles import CyclesConfig, CyclesEcosystem


def test_step_consistency_and_refuge_floor():
    cfg = CyclesConfig()
    eco = CyclesEcosystem(cfg, seed=0)
    for _ in range(60):
        eco.step()
        assert eco.prey["pos"].shape[0] >= cfg.prey_refuge  # refuge floor holds
        for sp in (eco.prey, eco.pred):
            n = sp["pos"].shape[0]
            assert all(sp[k].shape[0] == n for k in ("pos", "energy", "age", "cooldown"))


def test_no_extinction_and_predators_oscillate():
    # The limit cycle period is ~2000 steps, so we need a long enough window to
    # see repetition (boom-bust-boom).
    eco = CyclesEcosystem(CyclesConfig(), seed=0)
    pred = []
    for _ in range(5500):
        eco.step()
        pred.append(eco.snapshot()["pred"])
        assert eco.pred["pos"].shape[0] > 0, "predators must not go extinct"
        assert eco.prey["pos"].shape[0] > 0, "prey must not go extinct"
    pred = np.array(pred[600:])
    peaks, _ = find_peaks(pred, prominence=pred.std() * 0.4, distance=120)
    assert len(peaks) >= 2, f"expected sustained oscillation (repeated predator peaks), got {len(peaks)}"
    assert pred.max() > 100 and pred.min() < 60, \
        f"expected clear boom-bust amplitude, got {int(pred.min())}-{int(pred.max())}"
