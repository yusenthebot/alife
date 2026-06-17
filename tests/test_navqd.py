import numpy as np

from alife.brain import BrainSpec, random_brains
from alife.navqd import (
    N_IN,
    NavConfig,
    archive_trajectory,
    map_elites,
    objective_ga,
    reachable_mask,
    simulate,
)


def _inside_any_obstacle(pts, cfg, tol=1e-3):
    for cx, cy, r in cfg.obstacles:
        if np.any((pts[:, 0] - cx) ** 2 + (pts[:, 1] - cy) ** 2 < (r - tol) ** 2):
            return True
    return False


def test_origin_is_clear():
    cfg = NavConfig()
    for cx, cy, r in cfg.obstacles:
        assert np.hypot(cx, cy) > r        # creatures don't spawn inside a wall


def test_collisions_keep_creatures_out_of_obstacles():
    cfg = NavConfig()
    rng = np.random.default_rng(0)
    w = random_brains(64, BrainSpec(N_IN, cfg.n_hidden, 2), rng)
    pos, _, _ = simulate(w, cfg)
    assert not _inside_any_obstacle(pos, cfg)


def test_map_elites_fills_navigable_space():
    cfg = NavConfig(iters=300)
    archive, cov = map_elites(cfg, seed=0)
    nfree = int(reachable_mask(cfg).sum())
    assert cov[-1] > 0.7 * nfree            # weaves around walls to fill the arena
    assert cov[-1] >= cov[0]


def test_qd_beats_objective_coverage():
    cfg = NavConfig(iters=300)
    _, cov_me = map_elites(cfg, seed=0)
    _, cov_obj = objective_ga(cfg, seed=0)
    assert cov_me[-1] > 3 * cov_obj[-1]


def test_objective_competent_but_narrow():
    cfg = NavConfig(iters=300)
    pos, cov_obj = objective_ga(cfg, seed=0)
    nfree = int(reachable_mask(cfg).sum())
    assert np.linalg.norm(pos, axis=1).max() > 0.6 * cfg.reach   # it does reach far
    assert cov_obj[-1] < 0.45 * nfree                            # but narrow


def test_trajectory_avoids_obstacles_and_starts_at_origin():
    cfg = NavConfig(iters=250)
    archive, _ = map_elites(cfg, seed=0)
    # pick a far-out elite (most likely to have navigated around something)
    cell = max(archive, key=lambda c: np.linalg.norm(archive[c][2]))
    traj = archive_trajectory(archive[cell][1], cfg)
    assert np.allclose(traj[0], [0, 0])
    assert not _inside_any_obstacle(traj, cfg)


def test_reachable_mask_excludes_obstacles():
    cfg = NavConfig()
    free = reachable_mask(cfg)
    assert free.sum() < cfg.grid * cfg.grid       # some cells blocked
    assert free.sum() > 0.7 * cfg.grid * cfg.grid  # most navigable


def test_reproducible():
    cfg = NavConfig(iters=120)
    a, ca = map_elites(cfg, seed=4)
    b, cb = map_elites(cfg, seed=4)
    assert np.array_equal(ca, cb)
