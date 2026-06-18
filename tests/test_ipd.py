import numpy as np

from alife.ipd import stationary_payoff, tournament, NAMED, classify, evolve, T, R, P, S


def test_payoff_engine_known_cases():
    # mutual defection -> P; ALLC exploited by ALLD -> S vs T
    assert abs(stationary_payoff(NAMED["ALLD"], NAMED["ALLD"])[0] - P) < 0.05
    a, d, _ = stationary_payoff(NAMED["ALLC"], NAMED["ALLD"])
    assert abs(a - S) < 0.05 and abs(d - T) < 0.05


def test_tft_not_exploited():
    # TFT vs ALLD: both end near mutual defection (TFT retaliates, not a sucker)
    tft, alld, _ = stationary_payoff(NAMED["TFT"], NAMED["ALLD"])
    assert tft > S + 0.3 and abs(tft - alld) < 0.3


def test_noise_breaks_tft_not_wsls():
    # under implementation error, TFT-TFT cooperation collapses; WSLS-WSLS stays high
    ct = stationary_payoff(NAMED["TFT"], NAMED["TFT"], eps=0.05)[2]
    cw = stationary_payoff(NAMED["WSLS"], NAMED["WSLS"], eps=0.05)[2]
    assert ct < 0.6 and cw > 0.8


def test_wsls_self_corrects_vs_tft_self_play():
    # across error rates, WSLS keeps more cooperation than TFT in self-play
    for e in (0.01, 0.05, 0.1):
        assert (stationary_payoff(NAMED["WSLS"], NAMED["WSLS"], e)[2]
                > stationary_payoff(NAMED["TFT"], NAMED["TFT"], e)[2])


def test_tournament_reciprocators_beat_allc():
    names, score, mean = tournament(NAMED)
    m = dict(zip(names, mean))
    assert m["ALLC"] == min(mean)                     # unconditional cooperation is exploited worst
    assert m["WSLS"] > m["ALLC"] and m["TFT"] > m["ALLC"] and m["GRIM"] > m["ALLC"]


def test_classify():
    assert classify(NAMED["ALLD"]) == "ALLD"
    assert classify(NAMED["WSLS"]) == "WSLS"
    assert classify(NAMED["TFT"]) == "TFT"


def test_evolution_runs_and_is_contingent():
    # the well-mixed outcome varies by seed (bistable) — at least it runs and stays in range
    finals = [evolve(pop_size=80, gens=60, seed=s)["coop"][-1] for s in range(4)]
    assert all(0.0 <= f <= 1.0 for f in finals)
    assert max(finals) - min(finals) > 0.05          # outcomes genuinely differ across seeds


def test_reproducible():
    a = evolve(pop_size=60, gens=30, seed=1)["coop"]
    b = evolve(pop_size=60, gens=30, seed=1)["coop"]
    assert np.allclose(a, b)
