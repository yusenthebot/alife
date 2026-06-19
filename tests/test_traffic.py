import numpy as np

from alife.traffic import simulate, fundamental_diagram, jam_fraction, jam_wave_velocity


def test_no_collisions():
    # cars never occupy the same cell; velocities stay within [0, vmax]
    r = simulate(road=300, n_cars=120, vmax=5, p=0.3, steps=200, seed=1)
    sp = r["space"]
    for row in sp:
        cars = row[row >= 0]
        assert np.all((cars >= 0) & (cars <= 5))
    # exactly n_cars present every recorded step (mass conservation)
    assert np.all((sp >= 0).sum(axis=1) == 120)


def test_free_flow_vs_jam():
    free = simulate(road=400, n_cars=int(0.07 * 400), vmax=5, p=0.3, steps=400, seed=2)
    jam = simulate(road=400, n_cars=int(0.45 * 400), vmax=5, p=0.3, steps=400, seed=2)
    assert free["mean_flow"] > 4.0          # near vmax: free flowing
    assert jam["mean_flow"] < 1.5           # crawling: congested
    assert jam_fraction(jam["space"]) > jam_fraction(free["space"]) + 0.3


def test_fundamental_diagram_has_interior_peak():
    d, J = fundamental_diagram(road=300, vmax=5, p=0.3, steps=250, seed=3, reps=4)
    kc = int(np.argmax(J))
    assert 0 < kc < len(J) - 1              # peak is interior (a jamming transition exists)
    assert d[kc] < 0.3                       # critical density is low for vmax=5
    assert J[kc] > J[0] and J[kc] > J[-1]    # triangular: above free-flow start and jammed tail


def test_jams_propagate_backward():
    # the counterintuitive NS signature: jam waves move opposite to the cars
    r = simulate(road=400, n_cars=int(0.28 * 400), vmax=5, p=0.3, steps=500, seed=7)
    v_jam = jam_wave_velocity(r["space"][-250:])
    assert v_jam < -0.3                      # backward
    assert r["mean_flow"] > 0.5              # while cars still move forward


def test_dawdle_is_what_makes_jams():
    # with p=0 (deterministic), dense traffic settles into a smooth jam-free flow;
    # the random slowdown is the ingredient that nucleates phantom jams
    smooth = simulate(road=400, n_cars=int(0.18 * 400), vmax=5, p=0.0, steps=500, seed=4)
    rough = simulate(road=400, n_cars=int(0.18 * 400), vmax=5, p=0.3, steps=500, seed=4)
    assert jam_fraction(smooth["space"]) < jam_fraction(rough["space"])


def test_reproducible():
    a = simulate(road=200, n_cars=60, vmax=5, p=0.3, steps=120, seed=9)["flow"]
    b = simulate(road=200, n_cars=60, vmax=5, p=0.3, steps=120, seed=9)["flow"]
    assert np.array_equal(a, b)
