import numpy as np

from alife.growingturing import (
    GrowTuringConfig, run_static, run_growing, count_peaks, wavelength, step, make_fields,
)

CFG = GrowTuringConfig(gamma=4.0, seed=1)


def test_static_pattern_forms_stripes():
    s = run_static(CFG, N=200, steps=45000)
    assert s["n"] > 8                                       # a periodic stripe train
    assert s["u"].max() - s["u"].min() > 0.5               # real amplitude, not flat


def test_growing_domain_inserts_stripes():
    g = run_growing(CFG, N0=70, Nmax=300, grow_factor=1.07, settle=35000, grow_steps=2500)
    assert g["counts"][-1] > g["counts"][0] + 5            # stripes added as the domain grew


def test_stripe_count_proportional_to_length():
    g = run_growing(CFG, N0=70, Nmax=320, grow_factor=1.07, settle=35000, grow_steps=2500)
    assert np.corrcoef(g["lengths"], g["counts"])[0, 1] > 0.9     # n ~ L


def test_wavelength_is_maintained_not_growing():
    # the headline: the spacing stays bounded (does NOT grow with the domain) -- it is reset by insertion
    g = run_growing(CFG, N0=70, Nmax=320, grow_factor=1.07, settle=35000, grow_steps=2500)
    wl = g["lengths"] / np.maximum(g["counts"], 1)
    assert wl.std() / wl.mean() < 0.25                     # roughly constant
    assert wl[-1] < 1.6 * wl[0]                             # not proportional to length


def test_growing_wavelength_near_intrinsic():
    # the maintained spacing matches the static (intrinsic) Turing wavelength within the sawtooth band
    s = run_static(CFG, N=240, steps=45000)
    g = run_growing(CFG, N0=70, Nmax=320, grow_factor=1.07, settle=35000, grow_steps=2500)
    wl = g["lengths"] / np.maximum(g["counts"], 1)
    assert 0.6 * s["wavelength"] < wl.min() < 1.5 * s["wavelength"]


def test_higher_gamma_more_stripes():
    lo = run_static(GrowTuringConfig(gamma=2.0, seed=2), N=240, steps=45000)["n"]
    hi = run_static(GrowTuringConfig(gamma=8.0, seed=2), N=240, steps=45000)["n"]
    assert hi > lo                                          # shorter intrinsic wavelength


def test_intrinsic_wavelength_independent_of_domain_size():
    # static wavelength is set by chemistry, not domain length: doubling N ~ doubles stripe count
    short = run_static(CFG, N=150, steps=45000)
    long = run_static(CFG, N=300, steps=45000)
    assert abs(short["wavelength"] - long["wavelength"]) / short["wavelength"] < 0.3


def test_reproducible():
    rng = np.random.default_rng(3)
    u, v = make_fields(CFG, 100, rng)
    a = step(u.copy(), v.copy(), CFG, 500)[0]
    rng2 = np.random.default_rng(3)
    u2, v2 = make_fields(CFG, 100, rng2)
    b = step(u2.copy(), v2.copy(), CFG, 500)[0]
    assert np.array_equal(a, b)
