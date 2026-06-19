import numpy as np

from alife.ising3d import (
    TC2D, TC3D, mean_field_tc, _checker3d, _neighbour_sum, mc_sweep, magnetization,
    energy, run, sweep_temperature, locate_tc, binder_crossing,
)


def test_checkerboard_partitions_cubic_lattice():
    chk = _checker3d(8)
    assert chk.sum() == 8 ** 3 // 2                       # exactly half the sites
    # a site and each of its 6 neighbours are opposite colours (3D bipartite lattice)
    assert chk[0, 0, 0] != chk[1, 0, 0] != chk[1, 1, 0]


def test_neighbour_sum_counts_six():
    s = np.ones((4, 4, 4), dtype=np.int8)
    assert np.all(_neighbour_sum(s) == 6)                 # z = 6 in 3D


def test_low_temperature_stays_ordered():
    # deep in the ordered phase the lattice keeps a large spontaneous magnetisation
    s = np.ones((12, 12, 12), dtype=np.int8)
    r = run(L=12, T=2.0, sweeps=120, seed=1, start=s)
    assert r["mag"][-20:].mean() > 0.9


def test_high_temperature_disorders():
    # well above T_c thermal noise wins -> magnetisation near zero
    r = run(L=12, T=7.0, sweeps=200, seed=1)
    assert r["mag"][-50:].mean() < 0.2


def test_dimension_lifts_critical_temperature():
    # the headline: more neighbours (z: 4 -> 6) push the transition higher
    assert TC3D > TC2D
    # mean field predicts T_c = z and overestimates BOTH real values (worse in low dimension)
    assert mean_field_tc(6) > TC3D > TC2D
    assert mean_field_tc(4) > TC2D
    assert mean_field_tc(6) > mean_field_tc(4)


def test_susceptibility_peak_locates_3d_tc():
    # the susceptibility peak sits near the known 3D T_c ~ 4.51 (far above the 2D 2.27)
    res = sweep_temperature(L=12, temps=np.linspace(5.2, 3.8, 8), equil=200, measure=200, seed=2)
    tc = locate_tc(res["T"], res["chi"])
    assert TC2D < tc and 4.2 < tc < 4.9


def test_binder_crossing_brackets_tc():
    temps = np.linspace(5.0, 4.0, 7)
    small = sweep_temperature(L=8, temps=temps, equil=200, measure=200, seed=3)
    large = sweep_temperature(L=14, temps=temps, equil=200, measure=200, seed=3)
    tc = binder_crossing(temps, small["binder"], large["binder"])
    assert 4.2 < tc < 4.9                                 # size-independent crossing near T_c


def test_energy_lower_when_ordered():
    ordered = energy(np.ones((6, 6, 6), dtype=np.int8))
    rng = np.random.default_rng(0)
    disordered = energy(rng.choice([-1, 1], (6, 6, 6)).astype(np.int8))
    assert ordered == -3.0                                # all aligned: -J * 3 bonds/site
    assert disordered > ordered


def test_reproducible():
    a = run(L=8, T=4.5, sweeps=80, seed=7)["mag"]
    b = run(L=8, T=4.5, sweeps=80, seed=7)["mag"]
    assert np.array_equal(a, b)
