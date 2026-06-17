import numpy as np

from alife.brain import BrainSpec, random_brains
from alife.noveltymaze import (
    N_IN,
    MazeConfig,
    novelty_search,
    objective_search,
    reached,
    simulate,
    trajectory,
)


def _in_wall(pts, cfg, tol=1e-3):
    for cx, cy, hw, hh in cfg.walls:
        if np.any((np.abs(pts[:, 0] - cx) < hw - tol) & (np.abs(pts[:, 1] - cy) < hh - tol)):
            return True
    return False


def test_collisions_keep_out_of_walls():
    cfg = MazeConfig()
    rng = np.random.default_rng(0)
    w = random_brains(64, BrainSpec(N_IN, cfg.n_hidden, 2), rng)
    pos, _ = simulate(w, cfg)
    assert not _in_wall(pos, cfg)


def test_novelty_reaches_goal():
    cfg = MazeConfig()
    res = novelty_search(cfg, seed=1)
    assert reached(res, cfg)
    assert res["best_dist"].min() <= cfg.goal_radius


def test_objective_gets_trapped():
    """The deceptive trap: objective search ends pinned well short of the goal."""
    cfg = MazeConfig()
    res = objective_search(cfg, seed=1)
    assert not reached(res, cfg)
    # it plateaus at the dead-end wall (~11 away), well short of the goal
    assert res["best_dist"][-1] > cfg.goal_radius + 3


def test_novelty_beats_objective_success_rate():
    cfg = MazeConfig()
    seeds = range(5)
    nv = sum(reached(novelty_search(cfg, s), cfg) for s in seeds)
    ob = sum(reached(objective_search(cfg, s), cfg) for s in seeds)
    assert nv >= 4          # novelty reliably solves it
    assert nv > ob          # and beats the objective

def test_novelty_explores_more_widely():
    """Novelty's behavior archive spreads much wider than the objective's final pop."""
    cfg = MazeConfig()
    nv = novelty_search(cfg, seed=1)
    ob = objective_search(cfg, seed=1)
    obp, _ = simulate(ob["final_pop"], cfg)
    nv_spread = nv["archive"].std(axis=0).mean()
    ob_spread = obp.std(axis=0).mean()
    assert nv_spread > 2 * ob_spread


def test_trajectory_starts_at_start_and_avoids_walls():
    cfg = MazeConfig()
    res = novelty_search(cfg, seed=1)
    pos, _ = simulate(res["final_pop"], cfg)
    g = res["final_pop"][int(np.argmin(np.linalg.norm(pos - np.array(cfg.goal), axis=1)))]
    tr = trajectory(g, cfg)
    assert np.allclose(tr[0], cfg.start)
    assert not _in_wall(tr, cfg)


def test_reproducible():
    cfg = MazeConfig(generations=60)
    a = novelty_search(cfg, seed=3)["best_dist"]
    b = novelty_search(cfg, seed=3)["best_dist"]
    assert np.array_equal(a, b)
