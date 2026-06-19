import numpy as np

from alife.chemotaxis import simulate, chemotactic_index, gaussian_field, ChemoConfig


def test_control_does_not_climb():
    # alpha=0: no temporal modulation -> pure random walk, mean concentration stays ~flat
    r = simulate(ChemoConfig(alpha=0.0), n=500, seed=1)
    assert abs(r["mean_c"][-1] - r["mean_c"][0]) < 0.03


def test_chemotaxis_climbs_the_gradient():
    r = simulate(ChemoConfig(alpha=10.0), n=500, seed=1)
    assert r["mean_c"][-1] > r["mean_c"][0] + 0.05        # concentration rises
    assert r["mean_d"][-1] < r["mean_d"][0] - 2.0         # cells get closer to the source


def test_chemotaxis_beats_control_accumulation():
    chemo = simulate(ChemoConfig(alpha=10.0), n=600, seed=2)
    ctrl = simulate(ChemoConfig(alpha=0.0), n=600, seed=2)
    assert chemotactic_index(chemo) > chemotactic_index(ctrl) + 0.1


def test_dose_response_monotone_direction():
    lo = simulate(ChemoConfig(alpha=1.0), n=400, seed=3)["mean_c"][-1]
    hi = simulate(ChemoConfig(alpha=16.0), n=400, seed=3)["mean_c"][-1]
    assert hi > lo + 0.1                                  # stronger memory -> better climbing


def test_field_peaks_at_centre():
    conc, (cx, cy) = gaussian_field(100.0, 20.0)
    c = conc(np.array([[50.0, 50.0], [0.0, 0.0]]))
    assert c[0] > 0.99 and c[1] < 0.1                     # peak at centre, low at corner


def test_cells_stay_in_bounds_and_reproducible():
    a = simulate(ChemoConfig(alpha=6.0, steps=120), n=200, seed=7)
    b = simulate(ChemoConfig(alpha=6.0, steps=120), n=200, seed=7)
    assert np.array_equal(a["pos"], b["pos"])
    assert a["pos"].min() >= 0 and a["pos"].max() <= 100.0
