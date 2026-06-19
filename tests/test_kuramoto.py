import numpy as np

from alife.kuramoto import order_parameter, gaussian_kc, run, sweep_coupling


def test_order_parameter_extremes():
    r_sync, _ = order_parameter(np.full(500, 0.7))          # all in phase
    r_inc, _ = order_parameter(np.linspace(0, 2 * np.pi, 500, endpoint=False))  # uniform
    assert r_sync > 0.999
    assert r_inc < 0.01


def test_critical_coupling_formula():
    assert abs(gaussian_kc(1.0) - 1.5958) < 1e-3            # Kc = 2sqrt(2/pi) sigma
    assert abs(gaussian_kc(2.0) - 2 * gaussian_kc(1.0)) < 1e-9   # scales linearly with sigma


def test_below_kc_incoherent_above_kc_synced():
    kc = gaussian_kc(1.0)
    lo = run(n=800, K=0.5 * kc, sigma=1.0, seed=1)["final_r"]
    hi = run(n=800, K=2.5 * kc, sigma=1.0, seed=1)["final_r"]
    assert lo < 0.15                                         # incoherent (near finite-size baseline)
    assert hi > 0.85                                         # synchronized


def test_transition_is_monotone_and_sharp():
    kc = gaussian_kc(1.0)
    Ks, rs = sweep_coupling(np.array([0.3 * kc, 0.8 * kc, 1.5 * kc, 3.0 * kc]), n=800, sigma=1.0, seed=2)
    assert rs[0] < 0.15 and rs[-1] > 0.9                     # flat low -> high
    assert rs[-1] > rs[0] + 0.7                              # large jump across Kc


def test_partial_sync_locks_central_oscillators():
    kc = gaussian_kc(1.0)
    r = run(n=800, K=1.3 * kc, sigma=1.0, seed=1, track_freq=True)
    central = np.abs(r["omega"]) < 0.3                       # near the mean frequency
    edge = np.abs(r["omega"]) > 2.0                          # far from the mean
    assert np.mean(np.abs(r["eff_freq"][central]) < 0.15) > 0.8   # central oscillators lock
    assert np.mean(np.abs(r["eff_freq"][edge]) > 0.15) > 0.5      # far ones still drift


def test_reproducible():
    a = run(n=300, K=2.0, sigma=1.0, steps=200, seed=5)["r"]
    b = run(n=300, K=2.0, sigma=1.0, steps=200, seed=5)["r"]
    assert np.array_equal(a, b)
