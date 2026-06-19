import numpy as np

from alife.cgle import (
    CGLEConfig, run, step, winding, defect_count, net_charge, benjamin_feir, _expL,
)
from dataclasses import replace


def test_winding_counts_a_single_spiral():
    N = 120
    y, x = np.mgrid[-N // 2:N // 2, -N // 2:N // 2].astype(float)
    spiral = np.arctan2(y, x)                               # one +1 topological defect at the centre
    A = np.exp(1j * spiral)
    assert defect_count(A, periodic=False) == 1
    assert net_charge(A, periodic=False) == 1


def test_winding_pair_nets_to_zero():
    N = 120
    y, x = np.mgrid[-N // 2:N // 2, -N // 2:N // 2].astype(float)
    th = np.arctan2(y, x - 20) - np.arctan2(y, x + 20)      # a +1 and a -1
    A = np.exp(1j * th)
    assert defect_count(A, periodic=False) == 2
    assert net_charge(A, periodic=False) == 0


def test_uniform_has_no_defects():
    A = np.exp(1j * np.full((40, 40), 0.7))
    assert defect_count(A, periodic=False) == 0


def test_benjamin_feir_sign():
    assert benjamin_feir(1.0, -0.5) > 0      # frozen/spiral side
    assert benjamin_feir(2.0, -1.0) < 0      # turbulent side


def test_periodic_torus_total_charge_zero():
    # on a periodic domain defects are born/die in +/- pairs -> net charge is exactly 0
    r = run(CGLEConfig(N=128, b=1.0, c=-0.7, steps=2500, seed=1))
    assert net_charge(r["A"]) == 0


def test_turbulent_regime_has_more_defects():
    frozen = run(CGLEConfig(N=128, b=0.6, c=-0.5, steps=2500, seed=1))      # 1+bc=0.70
    turb = run(CGLEConfig(N=128, b=2.0, c=-1.4, steps=2500, seed=1))        # 1+bc=-1.8
    assert defect_count(turb["A"]) > 1.5 * defect_count(frozen["A"])
    assert defect_count(frozen["A"]) > 0                                    # spirals are still defects


def test_amplitude_is_low_at_defect_cores():
    # where a phase defect sits, |A| must dip well below the bulk amplitude (~1)
    r = run(CGLEConfig(N=128, b=2.0, c=-1.4, steps=2500, seed=2))
    A = r["A"]
    w = np.abs(winding(np.angle(A)))
    core = w > 0.5
    assert np.abs(A)[core].mean() < 0.6 * np.abs(A)[~core].mean()


def test_reproducible():
    a = run(CGLEConfig(N=64, steps=200, seed=5))["A"]
    b = run(CGLEConfig(N=64, steps=200, seed=5))["A"]
    assert np.allclose(a, b)
