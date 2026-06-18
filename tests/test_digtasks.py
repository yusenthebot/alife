import numpy as np

from alife.digavida import is_replicator
from alife.digtasks import (
    TASK_DOER,
    compete_compute,
    does_task,
    pure_copier,
    run_denovo,
)


def test_task_doer_replicates_and_computes():
    assert is_replicator(TASK_DOER)
    assert "NAND" in does_task(TASK_DOER, seed=0)


def test_pure_copier_does_no_task():
    assert does_task(pure_copier(len(TASK_DOER)), seed=0) == set()


def test_computation_pays():
    """A computing replicator out-reproduces an equal-length pure copier via merit."""
    c = compete_compute(sweeps=2000, seed=0)
    tot = c["computers"][-1] + c["copiers"][-1]
    assert c["computers"][-1] / tot > 0.85
    assert c["copiers"][-1] < c["copiers"][0]


def test_computation_pays_across_seeds():
    for seed in range(3):
        c = compete_compute(sweeps=2000, seed=seed)
        tot = c["computers"][-1] + c["copiers"][-1]
        assert c["computers"][-1] / tot > 0.8


def test_denovo_computation_emerges():
    """From pure copiers, NAND computation arises de novo by mutation."""
    r = run_denovo(sweeps=8000, mut=0.04, seed=0)
    assert "NAND" in r["cum_tasks"]            # at least one de-novo discovery


def test_reproducible():
    a = compete_compute(sweeps=600, seed=1)["computers"]
    b = compete_compute(sweeps=600, seed=1)["computers"]
    assert np.array_equal(a, b)
