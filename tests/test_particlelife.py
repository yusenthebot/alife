import numpy as np

from alife.particlelife import (
    ParticleLifeConfig, run, random_matrix, aggregation, _profile,
)


def _uniform_expectation(cfg):
    dens = cfg.n / cfg.world ** 2
    return dens * np.pi * (cfg.r_inner * 1.5) ** 2


def test_profile_hard_repulsion_inside_inner():
    # below r_inner the force is always negative (apart) regardless of matrix sign
    d = np.array([2.0, 6.0])
    f_attract = _profile(d, np.array([1.0, 1.0]), 12.0, 42.0)
    f_repel = _profile(d, np.array([-1.0, -1.0]), 12.0, 42.0)
    assert np.all(f_attract < 0) and np.allclose(f_attract, f_repel)  # matrix ignored inside core


def test_profile_zero_beyond_rmax():
    d = np.array([50.0, 100.0])
    f = _profile(d, np.array([1.0, 1.0]), 12.0, 42.0)
    assert np.allclose(f, 0.0)


def test_matrix_is_asymmetric():
    M = random_matrix(5, np.random.default_rng(0))
    assert M.shape == (5, 5)
    assert not np.allclose(M, M.T)               # genuinely asymmetric (red chases green != vice versa)


def test_structures_self_assemble():
    cfg = ParticleLifeConfig(n=4000, steps=250)
    M = random_matrix(cfg.types, np.random.default_rng(3))
    r = run(cfg, M, seed=0)
    agg = aggregation(cfg, r)
    assert agg > 2.5 * _uniform_expectation(cfg)  # clumped well above a uniform gas


def test_all_repulsive_stays_gas():
    """Control: a fully repulsive matrix cannot aggregate."""
    cfg = ParticleLifeConfig(n=4000, steps=250)
    Mg = -np.abs(random_matrix(cfg.types, np.random.default_rng(1)))
    r = run(cfg, Mg, seed=0)
    agg = aggregation(cfg, r)
    assert agg < 1.8 * _uniform_expectation(cfg)  # no structure


def test_periodic_and_finite():
    cfg = ParticleLifeConfig(n=2000, steps=80)
    M = random_matrix(cfg.types, np.random.default_rng(5))
    r = run(cfg, M, seed=0)
    assert np.all(r["pos"] >= 0) and np.all(r["pos"] < cfg.world)   # wrapped into box
    assert np.all(np.isfinite(r["pos"]))


def test_reproducible():
    cfg = ParticleLifeConfig(n=1500, steps=60)
    M = random_matrix(cfg.types, np.random.default_rng(2))
    a = run(cfg, M, seed=4)["pos"]
    b = run(cfg, M, seed=4)["pos"]
    assert np.allclose(a, b)
