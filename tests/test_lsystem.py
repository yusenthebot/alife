import numpy as np

from alife.lsystem import (
    LSConfig, Genome, expand, turtle, phenotype, leaf_tips, total_length,
    descriptors, random_genome, mutate, map_elites, SPECIES,
)


def test_expand_grows_and_caps():
    s = expand("FX", depth=4, max_len=10_000)        # X->FX each step: F,FF,FFF... + trailing X
    assert s.count("F") == 4 and s.endswith("X")
    assert len(expand("F[+X][-X]FX", depth=10, max_len=500)) <= 500   # capped


def test_turtle_segments_and_unbalanced_safe():
    segs = turtle("FF", 25.0)
    assert segs.shape == (2, 4)
    assert np.allclose(segs[0], [0, 0, 0, 1])        # first F goes straight up from origin
    # unbalanced brackets must not crash (pop on empty stack ignored)
    turtle("F]]]F[[F", 20.0)


def test_branching_creates_more_tips_than_a_line():
    line = turtle("F" * 8, 20.0)
    bush = phenotype(Genome("F[+X][-X]FX", 25.0), LSConfig(depth=4))
    assert len(leaf_tips(line)) == 1                 # a straight shoot has exactly one tip
    assert len(leaf_tips(bush)) > 5                  # branching multiplies tips


def test_leaf_tips_hand_example():
    # A->B, A->C from a shared start: two tips (B and C), the start is not a tip
    segs = np.array([[0, 0, 1, 1], [0, 0, -1, 1]], float)
    tips = leaf_tips(segs)
    assert len(tips) == 2


def test_descriptors_ranges():
    d = descriptors(phenotype(SPECIES["tree"], LSConfig(depth=5)))
    assert d is not None
    slender, branchy, tips = d
    assert 0.0 <= slender <= 1.0 and 0.0 <= branchy <= 1.0 and tips > 10


def test_species_all_render():
    cfg = LSConfig(depth=5)
    for g in SPECIES.values():
        segs = phenotype(g, cfg)
        assert len(segs) > 10 and total_length(segs) > 0


def test_map_elites_illuminates_diverse_forms():
    cfg = LSConfig(depth=4)
    r = map_elites(cfg, grid=(8, 8), iters=2500, seed=0)
    assert r["coverage"] > 0.4                        # fills a good fraction of morphospace
    # the discovered plants genuinely differ in slenderness
    slenders = [descriptors(phenotype(g, cfg))[0] for _, g in r["archive"].values()]
    assert max(slenders) - min(slenders) > 0.3


def test_reproducible():
    cfg = LSConfig(depth=4)
    a = map_elites(cfg, grid=(6, 6), iters=800, seed=1)["coverage"]
    b = map_elites(cfg, grid=(6, 6), iters=800, seed=1)["coverage"]
    assert a == b
