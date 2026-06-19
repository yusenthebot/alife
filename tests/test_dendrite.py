import numpy as np
from dataclasses import replace

from alife.dendrite import DendriteConfig, run, arm_count, solid_fraction

BASE = DendriteConfig(N=150, steps=1800, seed=2)


def test_six_fold_dendrite():
    r = run(replace(BASE, j=6))
    assert arm_count(r["p"]) == 6          # ice-like hexagonal dendrite


def test_four_fold_dendrite():
    r = run(replace(BASE, j=4))
    assert arm_count(r["p"]) == 4          # cubic-metal-like dendrite


def test_anisotropy_drives_growth():
    fast = solid_fraction(run(replace(BASE, delta=0.04))["p"])
    slow = solid_fraction(run(replace(BASE, delta=0.0))["p"])
    assert fast > 2 * slow                 # anisotropy + Mullins-Sekerka -> fast dendritic growth


def test_crystal_grows():
    r = run(replace(BASE, j=6, steps=1200))
    assert solid_fraction(r["p"]) > 0.02   # seed expands well beyond its tiny start


def test_latent_heat_halo():
    r = run(replace(BASE, j=6, steps=1200))
    c = BASE.N // 2
    near = r["T"][c - 25:c + 25, c - 25:c + 25].mean()
    far = r["T"][:20, :20].mean()
    assert near > far + 0.05               # latent heat reheats the melt around the crystal


def test_field_bounded():
    r = run(replace(BASE, steps=800))
    assert np.isfinite(r["p"]).all() and r["p"].min() >= 0.0 and r["p"].max() <= 1.0


def test_reproducible():
    a = run(replace(BASE, steps=600))["p"]
    b = run(replace(BASE, steps=600))["p"]
    assert np.array_equal(a, b)
