import numpy as np
from dataclasses import replace

from alife.fisherfront import (FrontConfig, run1d, run2d,
                               fisher_speed_theory, allee_speed_theory)


def test_fisher_speed_near_2sqrtrD():
    c = FrontConfig(r=1.0, D=1.0)
    sp = run1d(c)["speed"]
    th = fisher_speed_theory(c)
    assert abs(sp - th) < 0.12 * th        # pulled-front speed selection
    assert sp < th                         # approaches 2*sqrt(rD) from below (Bramson correction)


def test_fisher_speed_scales_with_diffusion():
    slow = run1d(FrontConfig(r=1.0, D=0.25))["speed"]
    fast = run1d(FrontConfig(r=1.0, D=1.0))["speed"]
    assert abs(fast / slow - 2.0) < 0.2    # c ~ sqrt(D): 4x D -> 2x speed


def test_allee_speed_matches_nagumo():
    c = FrontConfig(allee=0.2)
    sp = run1d(c)["speed"]
    assert abs(sp - allee_speed_theory(c)) < 0.1 * abs(allee_speed_theory(c))  # pushed front, exact


def test_allee_advances_below_threshold():
    assert run1d(FrontConfig(allee=0.3))["speed"] > 0.05    # a<1/2 -> population invades


def test_allee_retreats_above_threshold():
    assert run1d(FrontConfig(allee=0.7))["speed"] < -0.05   # a>1/2 -> founder population goes extinct


def test_allee_stalls_at_threshold():
    assert abs(run1d(FrontConfig(allee=0.5))["speed"]) < 0.05   # a=1/2 -> front pinned


def test_2d_fisher_colony_grows():
    r = run2d(FrontConfig(), N=140, steps=800, seed_radius=15)
    assert r["radius"][-1] > 1.5 * r["radius"][0]   # radial invasion expands


def test_2d_allee_colony_collapses():
    r = run2d(FrontConfig(allee=0.7), N=140, steps=800, seed_radius=22)
    assert r["radius"][-1] < 0.7 * r["radius"][0]   # over-threshold founder shrinks to extinction


def test_field_bounded_and_reproducible():
    a = run1d(FrontConfig(), steps=500)["u"]
    b = run1d(FrontConfig(), steps=500)["u"]
    assert np.array_equal(a, b)
    assert a.min() >= 0.0 and a.max() <= 1.0
