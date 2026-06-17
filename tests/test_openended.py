import numpy as np

from alife.brain import BrainSpec, random_brains
from alife.openended import (
    OpenEndedConfig,
    archive_trajectory,
    map_elites,
    objective_ga,
    simulate,
)


def test_simulate_shapes_and_curviness():
    cfg = OpenEndedConfig()
    rng = np.random.default_rng(0)
    w = random_brains(50, BrainSpec(4, cfg.n_hidden, 2), rng)
    pos, disp, curv = simulate(w, cfg)
    assert pos.shape == (50, 2)
    assert disp.shape == (50,) and curv.shape == (50,)
    assert np.all(disp >= 0) and np.all(curv >= 0)
    assert np.all(disp <= cfg.reach + 1e-6)   # can't travel faster than max_speed*steps


def test_map_elites_illuminates_the_space():
    """Quality-diversity fills most of the behavior grid."""
    cfg = OpenEndedConfig(iters=300)
    archive, cov = map_elites(cfg, seed=0)
    total = cfg.grid * cfg.grid
    assert cov[-1] > 0.6 * total          # broad coverage
    assert cov[-1] >= cov[0]              # coverage grows monotonically


def test_qd_beats_objective_coverage():
    """MAP-Elites covers far more behavior than objective-only search."""
    cfg = OpenEndedConfig(iters=300)
    _, cov_me = map_elites(cfg, seed=0)
    _, _, cov_obj = objective_ga(cfg, seed=0)
    assert cov_me[-1] > 3 * cov_obj[-1]


def test_objective_reaches_far_but_narrow():
    """Objective-only should find high displacement (good optimizer) but low diversity."""
    cfg = OpenEndedConfig(iters=300)
    pos, curv, cov_obj = objective_ga(cfg, seed=0)
    disp = np.linalg.norm(pos, axis=1)
    assert disp.max() > 0.7 * cfg.reach          # it IS a competent optimizer
    total = cfg.grid * cfg.grid
    assert cov_obj[-1] < 0.4 * total             # but narrow


def test_archive_has_diverse_curviness():
    """The discovered repertoire spans styles, not just straight lines."""
    cfg = OpenEndedConfig(iters=300)
    archive, _ = map_elites(cfg, seed=0)
    ci = np.array([c % cfg.grid for c in archive])
    assert ci.min() < cfg.grid * 0.2          # near-straight styles present
    assert ci.max() > cfg.grid * 0.7          # loopy styles present


def test_archive_trajectory_replays():
    cfg = OpenEndedConfig(iters=200)
    archive, _ = map_elites(cfg, seed=0)
    genome = next(iter(archive.values()))[1]
    traj = archive_trajectory(genome, cfg)
    assert traj.shape == (cfg.steps + 1, 2)
    assert np.allclose(traj[0], [0, 0])       # starts at origin


def test_reproducible():
    cfg = OpenEndedConfig(iters=120)
    a, ca = map_elites(cfg, seed=3)
    b, cb = map_elites(cfg, seed=3)
    assert np.array_equal(ca, cb)
