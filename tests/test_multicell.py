"""Tests for the evolution of multicellularity (predation-driven clustering)."""

from __future__ import annotations

import numpy as np

from alife.multicell import MulticellConfig, cluster_size, evolve, fitness


def test_cluster_size_monotonic():
    cfg = MulticellConfig()
    assert cluster_size(np.array([0.0, 1.0]), cfg)[0] == 1.0
    assert cluster_size(np.array([0.0, 1.0]), cfg)[1] == cfg.max_cluster


def test_no_predation_stays_unicellular():
    cfg = MulticellConfig()
    hist, csize = evolve(cfg, predation=False, seed=0)
    assert hist[-1] < 0.1, f"without predation, cost should keep cells unicellular ({hist[-1]:.2f})"
    assert csize < 2.5


def test_predation_drives_multicellularity():
    cfg = MulticellConfig()
    hist, csize = evolve(cfg, predation=True, seed=0)
    assert hist[-1] > 0.25, f"predation should select for clustering ({hist[-1]:.2f})"
    # clusters evolve large enough to clear the predator's size threshold
    assert csize >= cfg.pred_threshold, f"evolved clusters ({csize:.1f}) should escape predation (>{cfg.pred_threshold})"


def test_predation_beats_no_predation():
    cfg = MulticellConfig()
    with_pred, _ = evolve(cfg, predation=True, seed=1)
    without, _ = evolve(cfg, predation=False, seed=1)
    assert with_pred[-1] > without[-1] + 0.2
