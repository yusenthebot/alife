import numpy as np

from alife.nklandscape import (
    make_landscape, fitness, fitness_batch, adaptive_walk, global_optimum,
    count_local_optima, all_genomes, survey,
)


def test_landscape_shapes():
    L = make_landscape(10, 3, seed=0)
    assert L.deps.shape == (10, 4)                    # K+1 dependencies per locus
    assert L.contrib.shape == (10, 16)               # 2^(K+1) contributions
    assert np.all(L.deps[:, 0] == np.arange(10))     # each locus depends on itself first


def test_k0_global_is_mean_of_maxes():
    L = make_landscape(14, 0, seed=1)
    assert abs(global_optimum(L) - np.mean(np.max(L.contrib, axis=1))) < 1e-9


def test_fitness_deterministic_and_in_range():
    L = make_landscape(12, 4, seed=2)
    g = np.random.default_rng(0).integers(0, 2, 12).astype(np.int8)
    assert fitness(L, g) == fitness(L, g)
    assert 0.0 <= fitness(L, g) <= 1.0


def test_adaptive_walk_reaches_local_optimum():
    L = make_landscape(14, 4, seed=3)
    opt, tr = adaptive_walk(L, np.random.default_rng(0).integers(0, 2, 14).astype(np.int8))
    # no single flip improves the returned optimum
    nbrs = np.tile(opt, (14, 1)); nbrs[np.arange(14), np.arange(14)] ^= 1
    assert fitness_batch(L, nbrs).max() <= fitness(L, opt) + 1e-12
    assert np.all(np.diff(tr) > 0)                    # steepest ascent strictly increases


def test_k0_single_peak_reaches_global():
    L = make_landscape(14, 0, seed=4)
    assert count_local_optima(L) == 1                 # smooth landscape: one optimum
    g = global_optimum(L)
    _, tr = adaptive_walk(L, np.zeros(14, np.int8))
    assert abs(tr[-1] - g) < 1e-9                     # hill-climb finds the global optimum


def test_ruggedness_and_catastrophe_increase_with_K():
    rows = survey(14, [0, 2, 8, 13], walks=60, instances=3, seed=5)
    nopt = [r["n_optima"] for r in rows]
    gap = [r["global"] - r["mean_opt"] for r in rows]
    fg = [r["frac_global"] for r in rows]
    assert nopt[0] < nopt[1] < nopt[-1]               # more epistasis -> more local optima
    assert gap[-1] > gap[0] + 0.02                    # complexity catastrophe: reachable falls short
    assert fg[0] > fg[-1]                             # walks reach the global far less often at high K


def test_reproducible():
    L = make_landscape(12, 3, seed=9)
    a = fitness_batch(L, all_genomes(12))
    L2 = make_landscape(12, 3, seed=9)
    assert np.allclose(a, fitness_batch(L2, all_genomes(12)))
