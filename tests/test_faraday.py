import numpy as np
from dataclasses import replace

from alife.faraday import (FaradayConfig, run, dominant_k, resonant_k,
                           subharmonic_peak, w0)

BASE = FaradayConfig(N=64, Lx=2 * np.pi * 5, steps=6500, seed=1)


def test_above_threshold_grows():
    r = run(BASE)
    assert r["rms"][-1] > 20 * r["rms"][0]                 # parametric instability pumps the surface up


def test_subthreshold_stays_flat():
    r = run(replace(BASE, a=0.2))                          # below the forcing threshold
    assert r["rms"][-1] < r["rms"][0]                      # surface stays flat (damping wins) -> control


def test_selected_wavelength_matches_resonance():
    r = run(BASE)
    kstar = resonant_k(BASE)
    assert abs(dominant_k(r["field"], BASE) - kstar) < 0.1 * kstar   # drive picks w0(k*)=Omega/2


def test_response_is_subharmonic():
    r = run(BASE, sample_every=2)
    peak = subharmonic_peak(r["series"], r["ts"])
    assert abs(peak - BASE.Omega / 2) < 0.2 * (BASE.Omega / 2)       # responds at Omega/2 ...
    assert peak < 0.75 * BASE.Omega                                  # ... not at the drive Omega


def test_higher_drive_makes_finer_pattern():
    lo = replace(BASE, Omega=BASE.Omega * 0.8)
    hi = replace(BASE, Omega=BASE.Omega * 1.3)
    klo = dominant_k(run(lo)["field"], lo)
    khi = dominant_k(run(hi)["field"], hi)
    assert khi > klo                                       # shake faster -> shorter waves
    assert abs(klo - resonant_k(lo)) < 0.12 * resonant_k(lo)
    assert abs(khi - resonant_k(hi)) < 0.12 * resonant_k(hi)


def test_resonant_k_solves_dispersion():
    assert abs(w0(resonant_k(BASE), BASE) - BASE.Omega / 2) < 1e-6   # helper is self-consistent


def test_no_blowup_finite():
    r = run(BASE)
    assert np.isfinite(r["field"]).all() and np.abs(r["field"]).max() < 5.0  # cubic term saturates


def test_reproducible():
    a = run(replace(BASE, steps=2000))["field"]
    b = run(replace(BASE, steps=2000))["field"]
    assert np.array_equal(a, b)
