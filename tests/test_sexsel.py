import numpy as np

from alife.sexsel import SexSelConfig, evolve, preference_sweep


def test_runaway_exaggerates_ornament():
    """With female choice the ornament runs away far past its survival optimum (0)."""
    cfg = SexSelConfig(generations=200)
    r = evolve(cfg, female_choice=True, seed=0)
    assert abs(r.ornament[-1]) > 0.8  # exaggerated, not near 0


def test_no_choice_collapses_to_survival_optimum():
    """Without choice, survival selection pins the ornament at ~0."""
    cfg = SexSelConfig(generations=200)
    r = evolve(cfg, female_choice=False, seed=0)
    assert abs(r.ornament[-1]) < 0.25


def test_choice_beats_no_choice():
    cfg = SexSelConfig(generations=200)
    c = evolve(cfg, female_choice=True, seed=1)
    n = evolve(cfg, female_choice=False, seed=1)
    assert abs(c.ornament[-1]) > abs(n.ornament[-1]) + 0.5


def test_genetic_covariance_is_the_engine():
    """Fisher's mechanism: choosy females x ornamented males build a positive
    within-population genetic correlation (linkage disequilibrium) between the genes.
    Choice creates it; no choice leaves it near zero."""
    cfg = SexSelConfig(generations=200)
    c = evolve(cfg, female_choice=True, seed=0)
    n = evolve(cfg, female_choice=False, seed=0)
    # per-generation linkage is small (random-parent transmission dilutes it) but
    # persistently positive over the run, and absent without choice.
    assert np.nanmean(c.gene_corr) > 0.005        # linkage disequilibrium builds
    assert np.nanmean(c.gene_corr) > np.nanmean(n.gene_corr) + 0.01


def test_dose_response_monotone():
    """Stronger preference -> larger ornament."""
    cfg = SexSelConfig(generations=150)
    sweep = preference_sweep(cfg, [0.0, 2.0, 5.0], seeds=(0, 1))
    assert sweep[0] < sweep[1] < sweep[2]
    assert sweep[0] < 0.3  # no preference -> no ornament


def test_cost_paradox():
    """Ornamented males end with lower survival than they started (they pay a cost)."""
    cfg = SexSelConfig(generations=200)
    r = evolve(cfg, female_choice=True, seed=0)
    assert r.survival[-1] < r.survival[0]
    assert r.survival[-1] < 0.9


def test_reproducible():
    cfg = SexSelConfig(generations=80)
    a = evolve(cfg, female_choice=True, seed=3)
    b = evolve(cfg, female_choice=True, seed=3)
    assert np.allclose(a.ornament, b.ornament)
