"""Tests for the evolution of aging (Medawar/Williams)."""

from __future__ import annotations

import numpy as np

from alife.aging import AgingConfig, evolve, lifetime_reproduction


def test_lrs_decreases_with_mortality():
    s = np.full((1, 10), 0.9)
    assert lifetime_reproduction(s, 0.5, 1.0)[0] < lifetime_reproduction(s, 0.0, 1.0)[0]


def test_senescence_emerges():
    cfg = AgingConfig()
    s = evolve(cfg, extrinsic_mortality=0.15, seed=0)
    # intrinsic survival stays high when young, decays at old age (senescence)
    assert s[1] > 0.8, f"young survival should stay high ({s[1]:.2f})"
    assert s[-1] < s[1] - 0.2, f"old-age survival should decay ({s[1]:.2f} -> {s[-1]:.2f})"


def _onset(s):
    below = np.where(s < 0.5)[0]
    return int(below[0]) if below.size else len(s)


def test_williams_prediction_higher_mortality_faster_aging():
    cfg = AgingConfig()
    low = evolve(cfg, extrinsic_mortality=0.05, seed=0)
    high = evolve(cfg, extrinsic_mortality=0.35, seed=0)
    # Williams: higher extrinsic mortality => senescence sets in EARLIER
    assert _onset(low) > _onset(high) + 2, \
        f"low extrinsic mortality should age later: onset low-m {_onset(low)} vs high-m {_onset(high)}"
    # and mid-life survival is far higher under low extrinsic mortality
    assert low[11] > high[11] + 0.3, f"mid-life survival: low-m {low[11]:.2f} vs high-m {high[11]:.2f}"
