import numpy as np

from alife.snowflake import (
    SnowflakeConfig, grow, frozen_mask, crystal_mass, crystal_radius, compactness,
    is_symmetric, to_cartesian, NEIGHBORS,
)
from dataclasses import replace

CFG = SnowflakeConfig(L=151, alpha=1.0, beta=0.5, gamma=0.001, steps=200)


def test_seed_grows_into_a_crystal():
    s = grow(CFG)
    assert crystal_mass(s) > 20                            # grew well beyond the single seed
    assert crystal_radius(s) > 3


def test_six_fold_lattice_symmetry():
    # the crystal inherits the hexagonal lattice's symmetry (mirror + central inversion are exact)
    assert is_symmetric(grow(CFG))


def test_neighbor_set_is_symmetric():
    # the rule is invariant under transpose and negation -> guarantees the crystal symmetry
    nb = set(NEIGHBORS)
    assert {(d1, d0) for d0, d1 in NEIGHBORS} == nb
    assert {(-d0, -d1) for d0, d1 in NEIGHBORS} == nb


def test_morphology_changes_with_humidity():
    # Nakaya knob: higher background vapour beta -> bigger, more dendritic (less compact) crystal
    lo = grow(replace(CFG, beta=0.4))
    hi = grow(replace(CFG, beta=0.62))
    assert crystal_mass(hi) > crystal_mass(lo)             # more vapour -> more growth
    assert compactness(lo) > compactness(hi)               # low beta = more compact, high = dendrite


def test_crystal_grows_with_time():
    early = crystal_radius(grow(replace(CFG, steps=80)))
    late = crystal_radius(grow(replace(CFG, steps=200)))
    assert late > early


def test_compactness_bounded():
    c = compactness(grow(CFG))
    assert 0.0 < c <= 1.2


def test_to_cartesian_shape():
    X, Y = to_cartesian(31)
    assert X.shape == (31, 31) and Y.shape == (31, 31)


def test_reproducible():
    assert np.array_equal(grow(replace(CFG, steps=120)), grow(replace(CFG, steps=120)))
