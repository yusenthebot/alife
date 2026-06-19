import numpy as np

from alife.somitogenesis import (
    SomiteConfig, frequencies, run, predict_somite_size, somite_sizes,
    mean_somite_size, n_somites, somite_boundaries,
)


def test_somite_size_matches_clock_and_wavefront_law():
    # the headline: somite size = wavefront speed x clock period = 2*pi*v/omega
    for v, om in [(1.5, 1.0), (2.5, 1.0), (4.0, 2.0)]:
        cfg = SomiteConfig(N=320, v=v, omega=om, dt=0.01)
        measured = mean_somite_size(run(cfg)["frozen_phase"])
        assert abs(measured - predict_somite_size(cfg)) / predict_somite_size(cfg) < 0.05


def test_faster_front_makes_bigger_somites():
    slow = mean_somite_size(run(SomiteConfig(N=320, v=1.5, omega=1.0, dt=0.01))["frozen_phase"])
    fast = mean_somite_size(run(SomiteConfig(N=320, v=3.5, omega=1.0, dt=0.01))["frozen_phase"])
    assert fast > 1.8 * slow                                    # size proportional to v


def test_faster_clock_makes_smaller_somites():
    slow = mean_somite_size(run(SomiteConfig(N=320, v=2.5, omega=1.0, dt=0.01))["frozen_phase"])
    fast = mean_somite_size(run(SomiteConfig(N=320, v=2.5, omega=2.0, dt=0.01))["frozen_phase"])
    assert fast < 0.6 * slow                                    # size inversely proportional to omega


def test_no_clock_no_segments():
    r = run(SomiteConfig(N=300, v=2.5, omega=0.0, dt=0.01))
    assert n_somites(r["frozen_phase"]) == 1                    # no oscillator -> no pattern


def test_instant_front_no_pattern():
    # if the front sweeps the axis essentially at once, every cell freezes at the same phase
    r = run(SomiteConfig(N=300, v=1e5, omega=1.0, dt=0.01))
    assert n_somites(r["frozen_phase"]) <= 2


def test_somites_tile_the_axis():
    r = run(SomiteConfig(N=257, v=2.5, omega=1.0, dt=0.01))
    assert somite_sizes(r["frozen_phase"]).sum() == 257


def test_frequency_gradient_grades_somite_sizes():
    # a posterior frequency gradient -> somites shrink along the axis (graded, as in real embryos);
    # a uniform clock -> equal-sized somites
    flat = somite_sizes(run(SomiteConfig(N=400, v=2.5, omega=1.0, grad=0.0, dt=0.01))["frozen_phase"])
    grad = somite_sizes(run(SomiteConfig(N=400, v=2.5, omega=1.0, grad=2.0, dt=0.01))["frozen_phase"])
    assert grad[1:-1].std() > 3.0 * max(flat[1:-1].std(), 1e-6)


def test_frequencies_increase_posteriorly():
    om = frequencies(SomiteConfig(N=100, omega=1.0, grad=1.0))
    assert om[0] < om[-1] and np.all(np.diff(om) >= 0)


def test_reproducible():
    a = run(SomiteConfig(N=120, v=2.5, omega=1.0, noise=0.1, seed=4))["frozen_phase"]
    b = run(SomiteConfig(N=120, v=2.5, omega=1.0, noise=0.1, seed=4))["frozen_phase"]
    assert np.array_equal(a, b)
