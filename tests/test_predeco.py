import numpy as np

from alife.predeco import PredEcoConfig, run


def test_coexistence_is_robust():
    """The Huffaker refuge keeps both species alive (no extinction) across seeds."""
    cfg = PredEcoConfig(steps=2500)
    for seed in range(3):
        r = run(cfg, seed)
        assert r["prey"][-1] > 0 and r["pred"][-1] > 0
        assert r["prey"].min() > 0          # prey never wiped out


def test_populations_within_caps():
    cfg = PredEcoConfig(steps=2000)
    r = run(cfg, 0)
    assert r["prey"].max() <= cfg.max_prey
    assert r["pred"].max() <= cfg.max_pred


def test_refuge_prevents_collapse():
    """Without the refuge prey are far more likely to crash; with it they persist."""
    cfg = PredEcoConfig(steps=2500, refuge_radius=15.0)
    r = run(cfg, 0)
    assert r["prey"].min() > 20          # a solid floor of survivors


def test_prey_evolve_evasion():
    """The co-evolution signal: prey move away from predators more over time."""
    cfg = PredEcoConfig(steps=4000)
    r = run(cfg, 0)
    ev = r["evasion"]
    early = np.nanmean(ev[:8]); late = np.nanmean(ev[-15:])
    assert late > early + 0.03

def test_predators_pursue_from_the_start():
    """Honest asymmetry: predators sense prey directly, so pursuit is positive throughout
    (it does not need to evolve up the way evasion does)."""
    cfg = PredEcoConfig(steps=2500)
    r = run(cfg, 0)
    assert np.nanmean(r["pursuit"]) > 0.05

def test_snapshots_have_both_species():
    cfg = PredEcoConfig(steps=1500)
    r = run(cfg, 0, record_every=300)
    assert len(r["snaps"]) >= 4
    s = r["snaps"][-1]
    assert "prey" in s and "pred" in s and "food" in s


def test_reproducible():
    cfg = PredEcoConfig(steps=1200)
    a = run(cfg, 1)["prey"]
    b = run(cfg, 1)["prey"]
    assert np.array_equal(a, b)
