import numpy as np

from alife.transport import (
    grid_graph, braid_maze, make_maze, run, solve_flow, adapt,
    bfs_shortest, path_from_solution,
)


def test_grid_graph_counts():
    g, idx = grid_graph(4, 3)
    assert g.n == 12
    assert len(g.edges) == (4 - 1) * 3 + 4 * (3 - 1)        # horizontals + verticals


def test_flow_conservation():
    g, idx = grid_graph(5, 5)
    src, dst = idx[(0, 0)], idx[(4, 4)]
    D = np.ones(len(g.edges))
    p, Q = solve_flow(g, D, {src: +1.0, dst: -1.0})
    # net flux out of every interior node is ~0 (Kirchhoff); out of source ~ +I0
    net = np.zeros(g.n)
    np.add.at(net, g.edges[:, 0], Q)
    np.add.at(net, g.edges[:, 1], -Q)
    interior = [k for k in range(g.n) if k not in (src, dst)]
    assert np.allclose(net[interior], 0, atol=1e-8)
    assert abs(net[src] - 1.0) < 1e-6 and abs(net[dst] + 1.0) < 1e-6


def test_adapt_grows_and_decays():
    D = np.array([0.5, 0.5])
    grown = adapt(D, np.array([10.0, 0.0]), dt=0.2, gamma=1.0)
    assert grown[0] > 0.5                                   # high flux -> conductivity rises
    assert grown[1] < 0.5                                   # zero flux -> conductivity decays


def test_braid_has_loops():
    wall, W, H = make_maze(8, 8, seed=0)
    g0, _ = grid_graph(W, H, blocked=wall)
    assert len(g0.edges) == g0.n - 1                       # perfect maze is a tree (no loops)
    wallb, W, H = braid_maze(8, 8, seed=0, extra=0.15)
    gb, _ = grid_graph(W, H, blocked=wallb)
    assert len(gb.edges) > gb.n - 1                        # braiding adds loops


def test_physarum_solves_maze():
    wall, W, H = braid_maze(9, 9, seed=2, extra=0.15)
    g, idx = grid_graph(W, H, blocked=wall)
    src, dst = idx[(1, 1)], idx[(W - 2, H - 2)]
    true_len = bfs_shortest(g, src, dst)
    r = run(g, {src: +6.0, dst: -6.0}, steps=700, gamma=1.4, seed=0)
    found = path_from_solution(g, r["D"], src, dst, thresh=0.6)
    assert found == true_len                                # thick tubes trace the SHORTEST path
    assert r["cost"][-1] < r["cost"][0]                    # material is pruned


def test_gamma_controls_redundancy():
    # higher gamma -> leaner network (less total tube material) for the same multi-sink problem;
    # total conductivity Σ D is the clean monotone metric (edge-count-above-threshold is not).
    g, idx = grid_graph(16, 12)
    src = idx[(1, 6)]
    sinks = [idx[(14, 2)], idx[(14, 10)], idx[(8, 1)], idx[(8, 11)]]
    srcs = {src: +6.0}
    for s in sinks:
        srcs[s] = -6.0 / len(sinks)
    lo = run(g, srcs, steps=500, gamma=0.7, seed=0)["D"].sum()
    hi = run(g, srcs, steps=500, gamma=1.7, seed=0)["D"].sum()
    assert lo > hi * 1.3                                    # low gamma keeps substantially more tube


def test_reproducible():
    g, idx = grid_graph(8, 8)
    a = run(g, {idx[(0, 0)]: 4.0, idx[(7, 7)]: -4.0}, steps=50, seed=1)["D"]
    b = run(g, {idx[(0, 0)]: 4.0, idx[(7, 7)]: -4.0}, steps=50, seed=1)["D"]
    assert np.allclose(a, b)
