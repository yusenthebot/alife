import numpy as np

from alife.ecoseasons import SeasonConfig, run


def _per_flip_recovery(r, cfg):
    ab = r["approach_bias"]; sl = cfg.season_len
    out = []
    for s in range(1, cfg.steps // sl):     # seasons after the first flip
        a = int(s * sl / 50); b = int(((s + 1) * sl) / 50) - 1
        seg = ab[a:b]
        if len(seg) > 4:
            out.append(np.nanmean(seg[-3:]) - np.nanmean(seg[:3]))
    return out


def test_population_survives_flips():
    cfg = SeasonConfig(steps=12000)
    r = run(cfg, 0)
    assert r["pop"].min() > 0
    assert r["pop"][-1] > 0


def test_population_tracks_each_flip():
    """After each environmental flip the population re-evolves toward the new good
    colour: approach-bias starts low (maladapted) and recovers."""
    cfg = SeasonConfig(steps=16000)
    r = run(cfg, 0)
    rec = _per_flip_recovery(r, cfg)
    assert len(rec) >= 2
    assert all(x > 0.1 for x in rec)        # every flip is followed by recovery


def test_adapts_within_a_season():
    """By the end of a season the population is net-biased toward the good colour."""
    cfg = SeasonConfig(steps=16000)
    r = run(cfg, 0)
    ab = r["approach_bias"]; sl = cfg.season_len
    # end-of-season bias (sampled before each flip) should be positive on average
    ends = []
    for s in range(cfg.steps // sl):
        b = int(((s + 1) * sl) / 50) - 1
        ends.append(np.nanmean(ab[max(0, b - 3):b]))
    assert np.nanmean(ends) > 0.1


def test_poison_creates_discrimination_pressure():
    """With an inert wrong colour (no poison) there is little pressure to discriminate,
    so tracking is much weaker than with poison."""
    poison = run(SeasonConfig(steps=16000, bad_energy=-12.0), 0)
    inert = run(SeasonConfig(steps=16000, bad_energy=0.0), 0)
    assert np.nanmean(_per_flip_recovery(poison, SeasonConfig(steps=16000))) > \
           np.nanmean(_per_flip_recovery(inert, SeasonConfig(steps=16000)))


def test_reproducible():
    cfg = SeasonConfig(steps=6000)
    a = run(cfg, 3)["approach_bias"]
    b = run(cfg, 3)["approach_bias"]
    assert np.array_equal(np.nan_to_num(a), np.nan_to_num(b))
