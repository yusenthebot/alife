import numpy as np

from alife.sexevo import SexEvoConfig, evolve


def test_starts_mutation_free():
    cfg = SexEvoConfig(generations=10)
    r = evolve(cfg, sexual=False, seed=0)
    assert r["mean_load"][0] == 0.0


def test_asexual_load_ratchets_up():
    cfg = SexEvoConfig(generations=600)
    r = evolve(cfg, sexual=False, seed=0)
    assert r["mean_load"][-1] > 40                  # load climbs far past balance
    # the ratchet: the cleanest genome only ever gets more loaded
    assert r["min_load"][-1] > r["min_load"][0] + 20


def test_sexual_load_stays_near_balance():
    cfg = SexEvoConfig(generations=600)
    r = evolve(cfg, sexual=True, seed=0)
    balance = cfg.mut_rate / cfg.sel
    assert r["mean_load"][-1] < 3 * balance         # bounded near U/s
    assert r["min_load"][-1] < 15                    # clean class regenerated


def test_sex_beats_asex_robustly():
    cfg = SexEvoConfig(generations=600)
    for seed in range(3):
        a = evolve(cfg, False, seed)["mean_load"][-1]
        s = evolve(cfg, True, seed)["mean_load"][-1]
        assert a > 2 * s


def test_fitness_erodes_without_sex():
    cfg = SexEvoConfig(generations=600)
    a = evolve(cfg, False, 0)["mean_fitness"]
    s = evolve(cfg, True, 0)["mean_fitness"]
    assert a[-1] < a[0]                  # asexual fitness declines
    assert s[-1] > a[-1]                 # sexual ends fitter


def test_reproducible():
    cfg = SexEvoConfig(generations=200)
    a = evolve(cfg, True, 5)["mean_load"]
    b = evolve(cfg, True, 5)["mean_load"]
    assert np.array_equal(a, b)
