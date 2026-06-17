"""Tests for evolution of cooperation — Hamilton's rule (assortment*b > c)."""

from __future__ import annotations

import numpy as np

from alife.cooperation import CooperationConfig, evolve, sweep_assortment


def test_low_assortment_defects():
    cfg = CooperationConfig()           # c/b = 0.25
    coop = evolve(cfg, assortment=0.0, seed=0)
    assert coop[-1] < 0.25, f"with no assortment, defection should win ({coop[-1]:.2f})"


def test_high_assortment_cooperates():
    cfg = CooperationConfig()
    coop = evolve(cfg, assortment=0.6, seed=0)
    assert coop[-1] > 0.6, f"with high assortment, cooperation should evolve ({coop[-1]:.2f})"


def test_hamilton_threshold():
    cfg = CooperationConfig()           # threshold c/b = 0.25
    ass = np.array([0.0, 0.1, 0.4, 0.6])
    coop = sweep_assortment(cfg, ass, seed=0)
    # below threshold low, above threshold high — monotone-ish switch
    assert coop[0] < 0.3 and coop[1] < 0.4
    assert coop[2] > 0.55 and coop[3] > 0.6
    assert coop[-1] > coop[0] + 0.4
