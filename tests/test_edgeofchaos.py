import numpy as np

from alife.edgeofchaos import (
    Rule, CONWAY, lam, run, step, metrics, lambda_sweep, search_complex_rules, random_rule, _luts,
)


def test_lambda_value():
    assert abs(lam(CONWAY) - 3 / 18) < 1e-9          # |B|=1, |S|=2 -> 3/18
    assert lam(Rule(tuple(range(9)), tuple(range(9)))) == 1.0


def test_conway_blinker_period_2():
    blut, slut = _luts(CONWAY)
    g = np.zeros((5, 5), np.int8); g[2, 1:4] = 1      # horizontal blinker
    g1 = step(g, blut, slut)
    assert g1[1, 2] == 1 and g1[3, 2] == 1 and g1[2, 2] == 1   # becomes vertical
    g2 = step(g1, blut, slut)
    assert np.array_equal(g2, g)                      # period 2


def test_conway_block_still_life():
    blut, slut = _luts(CONWAY)
    g = np.zeros((6, 6), np.int8); g[2:4, 2:4] = 1    # 2x2 block
    assert np.array_equal(step(g, blut, slut), g)     # stable


def test_conway_is_complex():
    m = metrics(CONWAY, steps=200)
    assert m["complexity"] > 0.5                      # Conway sits in the Life-like regime
    assert 0.01 < m["density"] < 0.3 and m["activity"] < 0.2   # sparse + slow


def test_regimes_separate():
    ordered = metrics(Rule((3, 4), (4, 5, 6, 7, 8)), steps=200)    # freezes
    chaotic = metrics(Rule((2, 3), (5, 6, 7, 8)), steps=200)       # boils
    assert ordered["activity"] < 0.05                # frozen: little change
    assert chaotic["activity"] > 0.2                 # boiling: lots of change


def test_frac_complex_peaks_at_intermediate_lambda():
    lams, A, D, F = lambda_sweep(np.linspace(0.05, 0.95, 13), per_lambda=16, seed=1)
    peak = lams[np.argmax(F)]
    assert 0.1 < peak < 0.5                           # edge of chaos at intermediate lambda
    assert F[0] < F.max() and F[-1] < F.max()         # zero/low at both extremes
    assert D[-1] > D[0]                               # density rises with lambda (order parameter)


def test_search_finds_complex_rules_at_edge():
    top, all_lam = search_complex_rules(n_samples=800, seed=0, top=5)
    assert top[0][0] > 0.4                            # found genuinely complex rules
    found_lams = [m["lambda"] for _, _, m in top]
    assert all(0.1 < lv < 0.55 for lv in found_lams)  # they cluster at intermediate lambda


def test_reproducible():
    a = run(CONWAY, size=40, steps=50, seed=2)["grid"]
    b = run(CONWAY, size=40, steps=50, seed=2)["grid"]
    assert np.array_equal(a, b)
