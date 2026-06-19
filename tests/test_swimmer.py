import numpy as np
from dataclasses import replace

from alife.swimmer import simulate, _body_mask_and_vel, SwimConfig

# lean config: smaller grid, fewer steps (fluid sims are slow)
BASE = SwimConfig(nx=160, ny=90, length=44, amp=6.0, freq=0.0015, steps=2500, mass=600.0)


def test_undulating_body_self_propels():
    r = simulate(BASE, record_every=0)
    assert np.isfinite(r["net_disp"])                     # stable, no blow-up
    assert abs(r["net_disp"]) > 3.0                       # it swims a meaningful distance


def test_rigid_control_does_not_move():
    r = simulate(replace(BASE, amp=0.0))
    assert abs(r["net_disp"]) < 0.5                       # no gait -> no net motion (decisive control)


def test_swimming_is_monotone_directed():
    r = simulate(BASE, record_every=0)
    xc = r["xc"]
    disp = xc - xc[0]
    # net displacement dominates the wiggle: directed swimming, not a random walk
    assert abs(disp[-1]) > 0.5 * np.max(np.abs(disp))


def test_amplitude_controls_speed():
    slow = abs(simulate(replace(BASE, amp=3.0))["net_disp"])
    fast = abs(simulate(replace(BASE, amp=7.0))["net_disp"])
    assert fast > slow                                    # bigger gait -> faster swimming


def test_body_velocity_within_low_mach():
    # gait velocity must stay well below the LBM stability limit
    _, ux_b, uy_b = _body_mask_and_vel(BASE, xc=100.0, V=0.0, t=10)
    assert np.max(np.abs(uy_b)) < 0.1


def test_reproducible():
    a = simulate(replace(BASE, steps=400))["xc"]
    b = simulate(replace(BASE, steps=400))["xc"]
    assert np.array_equal(a, b)
