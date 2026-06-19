import numpy as np

from alife.phyllotaxis import (
    GOLDEN_ANGLE, PHI, vogel, nn_distance, packing_uniformity, uniformity_curve,
    douady_couder, emergent_angle, bifurcation, fibonacci_convergents,
)


def test_golden_angle_value():
    assert abs(GOLDEN_ANGLE - 137.5077) < 1e-3
    assert abs(PHI - 1.6180339) < 1e-6


def test_vogel_radius_grows_as_sqrt():
    P = vogel(GOLDEN_ANGLE, 400)
    assert P.shape == (400, 2)
    radii = np.hypot(P[:, 0], P[:, 1])
    assert np.allclose(radii, np.sqrt(np.arange(1, 401)), atol=1e-9)


def test_golden_angle_maximizes_packing():
    # the golden angle spreads organs out more than any nearby angle (larger min nearest-neighbour gap)
    g = packing_uniformity(vogel(GOLDEN_ANGLE, 600))["min_nn"]
    for off in (-1.0, -0.3, 0.3, 1.0):
        assert g > packing_uniformity(vogel(GOLDEN_ANGLE + off, 600))["min_nn"]


def test_uniformity_peaks_at_golden():
    alphas = np.arange(135.0, 140.0, 0.05)
    a, mn = uniformity_curve(alphas, n=500)
    assert abs(a[int(np.argmax(mn))] - GOLDEN_ANGLE) < 0.1


def test_off_golden_creates_spokes():
    # a rational fraction (144 = 2/5*360) packs into 5 radial spokes -> very non-uniform
    assert packing_uniformity(vogel(GOLDEN_ANGLE, 600))["cv"] < 0.1
    assert packing_uniformity(vogel(144.0, 600))["cv"] > 0.4


def test_least_crowding_rule_emerges_near_golden():
    # Douady-Couder: the greedy local rule self-selects ~the golden angle (golden branch)
    ang = emergent_angle(G=0.28, n=220, drop=100, n_ang=1440)
    assert abs(ang - GOLDEN_ANGLE) < 5.0


def test_bifurcation_has_golden_and_lucas_branches():
    # different growth rates lock onto distinct branches (golden ~138 vs Lucas ~101)
    _, ang = bifurcation([0.15, 0.28], n=200, drop=90)
    lucas, golden = sorted(ang)
    assert 90 < lucas < 115 and 130 < golden < 145


def test_emergent_angle_locks_in():
    # the divergence angle converges (the tail has tiny spread once locked)
    div = douady_couder(n=220, G=0.28, n_ang=1440)["divergence"]
    assert div[120:].std() < 1.0


def test_fibonacci_convergents():
    assert fibonacci_convergents(6) == [1, 1, 2, 3, 5, 8, 13, 21]
