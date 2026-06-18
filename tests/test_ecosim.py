import numpy as np

from alife.ecosim import EcoConfig, run


def test_run_returns_metrics_within_cap():
    cfg = EcoConfig(steps=2000)
    r = run(cfg, seed=0)
    assert r["pop"].max() <= cfg.max_pop
    assert r["pop"].min() > 0                 # population survives, no extinction


def test_population_is_food_limited_not_cap_limited():
    """The carrying capacity is set by food, not the population cap."""
    cfg = EcoConfig(steps=4000)
    r = run(cfg, seed=0)
    assert r["pop"].max() < 0.7 * cfg.max_pop  # never approaches the cap


def test_directed_foraging_evolves_in_situ():
    """The key capstone claim: with no GA, only life/death/reproduction, the
    population evolves to move toward food (directedness rises)."""
    cfg = EcoConfig(steps=5000)
    r = run(cfg, seed=0)
    d = r["directedness"]
    early = np.nanmean(d[:5]); late = np.nanmean(d[-10:])
    assert late > early + 0.1
    assert late > 0.2


def test_evolution_robust_across_seeds():
    cfg = EcoConfig(steps=4000)
    lates = []
    for s in range(3):
        d = run(cfg, seed=s)["directedness"]
        lates.append(np.nanmean(d[-10:]))
    assert np.mean(lates) > 0.2
    assert min(lates) > 0.12


def test_lineages_turn_over():
    """Real generational turnover: descendants many generations deep appear."""
    cfg = EcoConfig(steps=4000)
    r = run(cfg, seed=0)
    assert r["mean_gen"][-1] > 8
    assert r["mean_gen"][-1] > r["mean_gen"][0]


def test_snapshots_recorded():
    cfg = EcoConfig(steps=1000)
    r = run(cfg, seed=0, record_every=200)
    assert len(r["snaps"]) >= 4
    s = r["snaps"][-1]
    assert s["pos"].shape[1] == 2 and s["head"].ndim == 1


def test_reproducible():
    cfg = EcoConfig(steps=800)
    a = run(cfg, seed=2)["directedness"]
    b = run(cfg, seed=2)["directedness"]
    assert np.array_equal(np.nan_to_num(a), np.nan_to_num(b))
