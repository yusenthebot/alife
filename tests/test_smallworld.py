import numpy as np

from alife.smallworld import (ring_lattice, watts_strogatz, clustering_coefficient,
                              average_path_length, spread_time)


def test_ring_lattice_structure():
    n, k = 100, 6
    g = ring_lattice(n, k)
    assert all(len(g[i]) == k for i in range(n))            # every node has degree k
    # clustering of a ring lattice matches the closed form 3(k-2)/(4(k-1))
    assert abs(clustering_coefficient(g) - 3 * (k - 2) / (4 * (k - 1))) < 1e-9


def test_rewiring_conserves_edge_count():
    n, k = 300, 6
    base = sum(len(s) for s in ring_lattice(n, k)) // 2
    g = watts_strogatz(n, k, 0.3, seed=1)
    assert sum(len(s) for s in g) // 2 == base             # rewiring moves edges, never adds/removes
    assert all(i not in g[i] for i in range(n))            # no self-loops


def test_ring_long_random_short():
    n, k = 400, 6
    L_ring = average_path_length(ring_lattice(n, k), sources=80, seed=0)
    L_rand = average_path_length(watts_strogatz(n, k, 1.0, seed=0), sources=80, seed=0)
    assert L_ring > 30                                       # ring: paths grow ~n/2k
    assert L_rand < 6                                        # random: paths ~ln n / ln k


def test_small_world_decoupling():
    # the headline: a tiny rewiring collapses path length while clustering barely moves
    n, k = 600, 6
    ring = watts_strogatz(n, k, 0.0, seed=2)
    sw = watts_strogatz(n, k, 0.02, seed=2)
    C0, L0 = clustering_coefficient(ring), average_path_length(ring, sources=120, seed=2)
    C1, L1 = clustering_coefficient(sw), average_path_length(sw, sources=120, seed=2)
    assert L1 / L0 < 0.5                                     # path length more than halved...
    assert C1 / C0 > 0.85                                    # ...while clustering stays high


def test_shortcuts_speed_up_spreading():
    n, k = 500, 6
    s_ring = spread_time(watts_strogatz(n, k, 0.0, seed=4), seeds=8, seed=4)
    s_sw = spread_time(watts_strogatz(n, k, 0.1, seed=4), seeds=8, seed=4)
    assert s_sw < s_ring / 3                                 # shortcuts -> far faster reach


def test_reproducible():
    a = watts_strogatz(120, 4, 0.2, seed=7)
    b = watts_strogatz(120, 4, 0.2, seed=7)
    assert all(a[i] == b[i] for i in range(120))
