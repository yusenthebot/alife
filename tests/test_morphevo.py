import numpy as np

from alife.morphevo import (
    GENOME,
    MorphConfig,
    N_NODES,
    _decode,
    evolve,
    fitness,
    random_genomes,
    simulate,
)


def test_physics_is_stable():
    """Random creatures must not blow up (finite, bounded motion)."""
    cfg = MorphConfig()
    rng = np.random.default_rng(0)
    g = random_genomes(128, rng)
    disp = simulate(g, cfg)
    assert np.all(np.isfinite(disp))
    assert np.abs(disp).max() < 200      # nobody launches to infinity


def test_decode_lifts_body_above_ground():
    cfg = MorphConfig()
    rng = np.random.default_rng(1)
    pos, amp, phase = _decode(random_genomes(32, rng), cfg)
    assert pos.shape == (32, N_NODES, 2)
    assert np.all(pos[:, :, 1] >= 0)     # starts on/above the ground
    assert amp.shape[1] == (N_NODES * (N_NODES - 1)) // 2


def test_genome_size():
    assert GENOME == 2 * N_NODES + 2 * (N_NODES * (N_NODES - 1)) // 2


def test_evolution_improves_locomotion():
    cfg = MorphConfig(generations=60)
    res = evolve(cfg, seed=0)
    assert res["best"][-1] > 2.5 * res["best"][0]   # learns to travel much farther
    assert res["best"][-1] > 25


def test_evolved_gait_is_progressive_not_a_lurch():
    """The evolved creature travels via a sustained gait: COM moves consistently."""
    cfg = MorphConfig(generations=60)
    res = evolve(cfg, seed=0)
    _, frames, _ = simulate(res["best_genome"][None, :], cfg, record=True)
    com_x = np.array([f[:, 0].mean() for f in frames])
    direction = np.sign(com_x[-1] - com_x[0])
    monotone = np.mean(np.diff(com_x) * direction > 0)
    assert abs(com_x[-1] - com_x[0]) > 20
    assert monotone > 0.8            # most steps progress the same way = a gait


def test_robust_across_seeds():
    cfg = MorphConfig(generations=60)
    finals = [evolve(cfg, seed=s)["best"][-1] for s in range(3)]
    assert np.mean(finals) > 25
    assert min(finals) > 15


def test_fitness_is_absolute_displacement():
    cfg = MorphConfig()
    rng = np.random.default_rng(2)
    g = random_genomes(16, rng)
    assert np.allclose(fitness(g, cfg), np.abs(simulate(g, cfg)))


def test_reproducible():
    cfg = MorphConfig(generations=30)
    a = evolve(cfg, seed=4)["best"]
    b = evolve(cfg, seed=4)["best"]
    assert np.array_equal(a, b)
