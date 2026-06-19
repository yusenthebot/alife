from dataclasses import replace

import numpy as np

from alife.chimera import (
    ChimeraConfig, kernel, run, local_order, global_order, is_chimera, coherent_fraction,
)

BASE = ChimeraConfig(N=256, kappa=4.0, alpha=1.46, steps=2500, seed=1)


def test_chimera_forms_with_nonlocal_coupling():
    # nonlocal kernel + alpha just below pi/2 -> coherent and incoherent regions coexist
    r = run(BASE)
    R = local_order(r["theta"])
    assert is_chimera(r["theta"])
    assert R.max() > 0.9 and R.min() < 0.7


def test_coherent_and_incoherent_regions_coexist():
    f = coherent_fraction(run(BASE)["theta"])
    assert 0.15 < f < 0.7                                  # part coherent, part incoherent


def test_chimera_has_partial_global_order():
    # neither full sync (R=1) nor full incoherence (R=0) -- the signature of a chimera
    g = global_order(run(BASE)["theta"])
    assert 0.45 < g < 0.92


def test_global_coupling_gives_full_sync_not_chimera():
    r = run(replace(BASE, global_coupling=True))
    assert not is_chimera(r["theta"])
    assert global_order(r["theta"]) > 0.98                 # all-to-all -> global synchrony


def test_no_phase_lag_gives_full_sync():
    r = run(replace(BASE, alpha=0.0))
    assert not is_chimera(r["theta"])
    assert global_order(r["theta"]) > 0.98


def test_chimera_persists():
    # the split is not a transient -- it is still a chimera much later
    assert is_chimera(run(replace(BASE, steps=2000))["theta"])
    assert is_chimera(run(replace(BASE, steps=4000))["theta"])


def test_kernel_normalized_and_nonlocal():
    g = kernel(BASE)
    assert abs(g.sum() - 1.0) < 1e-12
    assert g[0] > g[BASE.N // 2]                           # exponential: peaks at zero distance
    gflat = kernel(replace(BASE, global_coupling=True))
    assert np.allclose(gflat, gflat[0])                    # control kernel is flat (all-to-all)


def test_local_order_bounded():
    R = local_order(run(BASE)["theta"])
    assert R.min() >= -1e-9 and R.max() <= 1.0 + 1e-9


def test_reproducible():
    a = run(replace(BASE, steps=400, seed=7))["theta"]
    b = run(replace(BASE, steps=400, seed=7))["theta"]
    assert np.array_equal(a, b)
    c = run(replace(BASE, steps=400, seed=8))["theta"]
    assert not np.array_equal(a, c)
