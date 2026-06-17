"""Tests for evolution of communication (Lewis signalling game)."""

from __future__ import annotations

import numpy as np

from alife.signals import SignalConfig, evolve, mutual_information


def test_mutual_information_bounds():
    k = 4
    # a perfect bijection state->signal carries log2(k) bits
    perfect = np.tile(np.arange(k), (50, 1))
    assert abs(mutual_information(perfect, k) - np.log2(k)) < 1e-6
    # everyone sends the same signal -> zero information
    constant = np.zeros((50, k), dtype=int)
    assert mutual_information(constant, k) < 1e-9


def test_communication_evolves():
    cfg = SignalConfig()
    _, _, succ, mi = evolve(cfg, seed=0)
    assert succ[0] < 0.6, "should start near chance (~0.25)"
    assert succ[-1] > 0.88, f"a signalling convention should evolve (success {succ[-1]:.2f})"
    # MI climbs from ~0 toward log2(k)=2; ~1.7 reflects near-but-imperfect conventions (dialects)
    assert mi[-1] > 1.4, f"signals should carry real information (MI {mi[-1]:.2f} bits)"
    assert mi[0] < 0.3, "should start with ~no shared meaning"


def test_evolves_across_seeds():
    cfg = SignalConfig()
    finals = [evolve(cfg, seed=s)[2][-1] for s in (0, 1, 2)]
    assert all(f > 0.85 for f in finals), f"communication should evolve every run: {finals}"
