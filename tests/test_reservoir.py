import numpy as np

from alife.reservoir import (
    lorenz_series, ESNConfig, build_reservoir, fit_and_predict, valid_time,
)


def test_lorenz_on_attractor():
    s = lorenz_series(3000, dt=0.02, seed=0)
    assert np.all(np.isfinite(s))
    assert -25 < s[:, 0].min() and s[:, 0].max() < 25      # bounded chaotic attractor
    assert s[1000:, 2].max() > 35                           # z reaches the wings


def test_spectral_radius_scaled():
    cfg = ESNConfig(n_res=120, spectral_radius=0.95)
    W, W_in = build_reservoir(cfg, 3, seed=0)
    assert abs(np.max(np.abs(np.linalg.eigvals(W))) - 0.95) < 1e-6
    assert W_in.shape == (120, 3)


def test_esn_tracks_then_diverges():
    cfg = ESNConfig(n_res=400, spectral_radius=1.1, leak=0.7, ridge=1e-6)
    r = fit_and_predict(cfg, train_len=5000, predict_len=1500, seed=0)
    assert np.all(np.isfinite(r["gen"]))                   # free-run stays bounded (no blow-up)
    vt = valid_time(r["gen_n"], r["true_n"], r["dt"])
    assert vt > 1.0                                         # tracks the true chaos for >1 Lyapunov time


def test_climate_reconstructed():
    cfg = ESNConfig(n_res=400, spectral_radius=1.2, leak=0.6, ridge=1e-6)
    r = fit_and_predict(cfg, train_len=6000, predict_len=2000, seed=0)
    gstd, tstd = r["gen"].std(0), r["true"].std(0)
    assert np.all(np.abs(gstd - tstd) / tstd < 0.5)        # the attractor 'climate' is reproduced
    assert r["gen"][:, 2].max() > 30                       # generated trajectory visits the wings


def test_reproducible():
    cfg = ESNConfig(n_res=150)
    a = fit_and_predict(cfg, train_len=1500, predict_len=300, seed=2)["gen"]
    b = fit_and_predict(cfg, train_len=1500, predict_len=300, seed=2)["gen"]
    assert np.allclose(a, b)
