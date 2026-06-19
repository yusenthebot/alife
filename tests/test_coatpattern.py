import numpy as np

from alife.coatpattern import (
    CoatConfig, run_strip, run_shape, body_tail_mask, n_spots, mean_blob_elongation,
    pattern_type, _masked_lap,
)
from dataclasses import replace


def test_blob_metrics_on_controls():
    dots = np.zeros((60, 60)); dots[5::10, 5::10] = 1.0       # grid of round spots
    bands = np.zeros((60, 60)); bands[:, 5::12] = 1.0         # vertical stripes
    assert pattern_type(dots) == "spots" and mean_blob_elongation(dots) < 1.5
    assert pattern_type(bands) == "stripes" and mean_blob_elongation(bands) > 5


def test_wide_domain_makes_a_spot_lattice():
    v = run_strip(CoatConfig(steps=8000, seed=1), H=120, W=120)
    assert pattern_type(v) == "spots"
    assert n_spots(v) > 40                                    # many spots fill the wide sheet


def test_narrowing_reduces_spot_count():
    wide = n_spots(run_strip(CoatConfig(steps=8000, seed=1), H=120, W=120))
    narrow = n_spots(run_strip(CoatConfig(steps=8000, seed=1), H=120, W=34))
    assert wide > 1.5 * narrow                                # far fewer spot rows fit in a narrow strip


def test_narrowing_elongates_toward_stripes():
    # Murray's mechanism: squeezing the domain forces spots to merge/elongate toward stripes
    wide = mean_blob_elongation(run_strip(CoatConfig(steps=8000, seed=1), H=120, W=120))
    narrow = mean_blob_elongation(run_strip(CoatConfig(steps=8000, seed=1), H=120, W=30))
    assert narrow > 1.3 * wide


def test_subwavelength_goes_blank():
    # below one intrinsic wavelength no pattern fits (the R92 failure mode, now controlled)
    v = run_strip(CoatConfig(steps=8000, seed=1), H=120, W=14)
    assert pattern_type(v) == "blank"


def test_masked_laplacian_is_no_flux():
    # a uniform field has zero Laplacian even at the mask boundary (no spurious flux out of the domain)
    m = np.zeros((20, 20), bool); m[5:15, 5:15] = True
    a = np.ones((20, 20))
    assert np.abs(_masked_lap(a, m)).max() < 1e-12


def test_tapered_creature_has_spotted_body():
    m = body_tail_mask(90, 200, 72, 22)
    v = run_shape(CoatConfig(steps=9000, seed=1), m)
    # the wide body holds many spots
    body = v[:, :80]
    assert n_spots(body) > 8 and v.max() > 0.2


def test_reproducible():
    a = run_strip(CoatConfig(steps=500, seed=3), H=60, W=60)
    b = run_strip(CoatConfig(steps=500, seed=3), H=60, W=60)
    assert np.array_equal(a, b)
