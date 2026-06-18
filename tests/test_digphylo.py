import numpy as np

from dataclasses import replace

from alife.digphylo import PhyloConfig, run


def test_coalescence_to_common_ancestor():
    """Many founding lineages collapse to one — all survivors share an ancestor."""
    r = run(PhyloConfig(), seed=0)
    assert r["n_lineages"][0] >= 20
    assert r["n_lineages"][-1] <= 3            # coalesced to ~one lineage
    assert r["top_lineage"][-1] > 0.8


def test_lineages_only_decrease_overall():
    """Neutral founding tags can't be re-created, so their count trends down."""
    r = run(PhyloConfig(), seed=0)
    assert r["n_lineages"][-1] < r["n_lineages"][0]


def test_ongoing_evolutionary_activity():
    """New genotypes keep appearing throughout the run (cumulative count climbs)."""
    r = run(PhyloConfig(), seed=0)
    cg = r["cum_genotypes"]
    assert cg[-1] > 500
    assert cg[-1] > cg[len(cg) // 2]           # still rising in the second half


def test_population_persists():
    r = run(replace(PhyloConfig(), sweeps=3000), seed=0)
    assert r["n_genotypes"][-1] > 5            # a living, diverse population


def test_reproducible():
    a = run(replace(PhyloConfig(), sweeps=1500), seed=2)["n_lineages"]
    b = run(replace(PhyloConfig(), sweeps=1500), seed=2)["n_lineages"]
    assert np.array_equal(a, b)
