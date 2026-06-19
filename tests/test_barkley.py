import numpy as np

from alife.barkley import (
    BarkleyConfig, step, run_spiral, run_target, wave_speed, excited_fraction, ring_count,
)
from dataclasses import replace


def _blob(amp, cfg, steps=1200):
    N = cfg.N
    u = np.zeros((N, N))
    v = np.zeros((N, N))
    u[N // 2 - 3:N // 2 + 3, N // 2 - 3:N // 2 + 3] = amp
    for _ in range(steps):
        u, v = step(u, v, cfg)
    return excited_fraction(u)


def test_rest_state_is_stable():
    # an unperturbed medium stays at rest (no spontaneous firing)
    cfg = BarkleyConfig(N=80)
    u = np.zeros((80, 80))
    v = np.zeros((80, 80))
    for _ in range(800):
        u, v = step(u, v, cfg)
    assert u.max() < 1e-6


def test_excitability_threshold():
    # below the threshold (v+b)/a = b/a ~ 0.027 a kick dies; above it a wave propagates
    cfg = BarkleyConfig(N=120)
    assert _blob(0.015, cfg) < 1e-3          # sub-threshold -> dies
    assert _blob(0.6, cfg) > 0.01            # supra-threshold -> propagating wave


def test_wave_speed_positive_and_finite():
    s = wave_speed(BarkleyConfig(), length=400, steps=1500)
    assert 1.0 < s < 12.0                    # a sensible constant front speed (cells/time)


def test_spiral_is_re_entrant():
    # a broken front winds into a spiral that sustains activity indefinitely (no external drive)
    r = run_spiral(BarkleyConfig(N=160, steps=4000, seed=1))
    assert r["activity"] > 0.05


def test_target_waves_form_rings():
    r = run_target(BarkleyConfig(N=200, steps=4500, seed=1), pace_period=350)
    assert ring_count(r["u"]) >= 2           # concentric target rings from the pacemaker


def test_no_pacemaker_no_rings():
    # without the pacemaker the medium stays at rest -> no rings
    cfg = BarkleyConfig(N=120, steps=1500)
    u = np.zeros((120, 120)); v = np.zeros((120, 120))
    for _ in range(cfg.steps):
        u, v = step(u, v, cfg)
    assert ring_count(u) == 0


def test_reproducible():
    a = run_spiral(BarkleyConfig(N=100, steps=300, seed=3))["u"]
    b = run_spiral(BarkleyConfig(N=100, steps=300, seed=3))["u"]
    assert np.array_equal(a, b)
