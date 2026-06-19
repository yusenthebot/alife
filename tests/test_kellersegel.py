from dataclasses import replace

import numpy as np

from alife.kellersegel import (
    KSConfig, run, make_state, aggregation, chi_critical, sweep_chi, onset_chi,
    growth_rate, growth_rate_theory,
)

BASE = KSConfig(L=64, steps=2000, seed=1)


def test_mass_conserved_to_machine_precision():
    # conservative flux form: total cell mass must not drift even as peaks sharpen (supercritical)
    r = run(replace(BASE, chi=4.0))
    rel = abs(r["mass"][-1] - r["mass0"]) / r["mass0"]
    assert rel < 1e-10


def test_density_stays_nonnegative():
    # upwind chemotactic flux keeps cell density physical even in the collapse regime
    r = run(replace(BASE, chi=4.0))
    assert r["rho"].min() >= -1e-12


def test_subcritical_stays_uniform():
    # below chi_c the uniform lawn is linearly stable -> perturbation decays
    xc = chi_critical(BASE)
    r = run(replace(BASE, chi=0.5 * xc))
    assert aggregation(r["rho"], BASE.rho0) < 1.1


def test_supercritical_aggregates():
    # well above chi_c the lawn collapses into dense aggregates
    xc = chi_critical(BASE)
    r = run(replace(BASE, chi=4.0 * xc))
    assert aggregation(r["rho"], BASE.rho0) > 10.0


def test_attractant_tracks_cells():
    # at collapse the chemoattractant peaks co-locate with the cell aggregates
    r = run(replace(BASE, chi=4.0))
    rho, c = r["rho"], r["c"]
    corr = np.corrcoef(rho.ravel(), c.ravel())[0, 1]
    assert corr > 0.5


def test_growth_rate_changes_sign_at_chi_c():
    # THE linear-stability prediction: the k_min mode decays below chi_c and grows above it
    cfg = KSConfig(L=96, Dc=6.0, seed=3)
    xc = chi_critical(cfg)
    from dataclasses import replace
    assert growth_rate(replace(cfg, chi=0.5 * xc)) < 0          # subcritical: mode decays
    assert growth_rate(replace(cfg, chi=2.5 * xc)) > 0          # supercritical: mode grows
    # the zero-crossing sits at chi_c (within a few % — measured very near marginal)
    assert abs(growth_rate(replace(cfg, chi=xc))) < 5e-3


def test_measured_growth_rate_matches_dispersion_theory():
    # the measured single-mode rate quantitatively reproduces the dispersion relation
    cfg = KSConfig(L=96, Dc=6.0, seed=3)
    for chi in (1.5, 2.5):
        from dataclasses import replace
        m = growth_rate(replace(cfg, chi=chi))
        t = growth_rate_theory(cfg, chi, mode=(1, 0))
        assert abs(m - t) < 0.1 * abs(t) + 1e-4


def test_finite_time_onset_above_linear_threshold():
    # end-state aggregation appears only above chi_c (critical slowing-down delays the visible onset)
    xc = chi_critical(BASE)
    chis, met = sweep_chi(np.linspace(0.2, 4.0, 11), BASE)
    onset = onset_chi(chis, met, thresh=2.0)
    assert onset >= xc


def test_chi_critical_scaling():
    # chi_c = Drho*(Dc*kmin^2 + b)/(a*rho0): rises with motility, falls with production/density
    base = KSConfig(L=64)
    assert chi_critical(replace(base, Drho=2.0)) > chi_critical(base)
    assert chi_critical(replace(base, prod=2.0)) < chi_critical(base)
    assert chi_critical(replace(base, rho0=2.0)) < chi_critical(base)


def test_reproducible():
    a = run(replace(BASE, chi=4.0, steps=300))["rho"]
    b = run(replace(BASE, chi=4.0, steps=300))["rho"]
    assert np.array_equal(a, b)
    # and a different seed gives a different collapse pattern
    c = run(replace(BASE, chi=4.0, steps=300, seed=2))["rho"]
    assert not np.array_equal(a, c)
