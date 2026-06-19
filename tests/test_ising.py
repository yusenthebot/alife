import numpy as np

from alife.ising import mc_sweep, energy, run, sweep_temperature, TC


def test_critical_temperature_value():
    assert abs(TC - 2.2691853) < 1e-4                  # Onsager 2/ln(1+sqrt2)


def test_sweep_preserves_spins():
    rng = np.random.default_rng(0)
    s = np.where(rng.random((16, 16)) < 0.5, 1, -1).astype(np.int8)
    out = mc_sweep(s.copy(), 2.0, rng)
    assert out.shape == s.shape and set(np.unique(out)).issubset({-1, 1})


def test_ground_state_energy():
    s = np.ones((10, 10), np.int8)
    assert abs(energy(s) - (-2.0)) < 1e-9              # all aligned: -2 per spin (2 bonds/spin)


def test_low_T_orders_high_T_disorders():
    lo = run(48, T=1.2, sweeps=300, seed=0)["mag"]
    hi = run(48, T=3.5, sweeps=300, seed=0)["mag"]
    assert abs(lo[-50:].mean()) > 0.85                 # low T: magnetised (ordered)
    assert abs(hi[-50:].mean()) < 0.2                  # high T: disordered


def test_phase_transition_and_susceptibility_peak():
    T, M, X, E = sweep_temperature(size=40, temps=np.linspace(1.6, 3.2, 17), equil=250, measure=250, seed=0)
    assert M[0] > 0.85 and M[-1] < 0.25                # magnetisation collapses across the sweep
    assert 2.0 < T[np.argmax(X)] < 2.6                 # susceptibility peaks near T_c
    assert E[-1] > E[0]                                 # energy rises with temperature


def test_reproducible():
    a = run(24, T=2.3, sweeps=80, seed=3)["spin"]
    b = run(24, T=2.3, sweeps=80, seed=3)["spin"]
    assert np.array_equal(a, b)
