import numpy as np

from alife.flowforage import (
    ForageConfig, run, vortex_flow, patchiness, _grad,
)
from dataclasses import replace

CFG = ForageConfig(L=110, n0=350, steps=280, seed=1)


def test_chemotaxis_is_selected_with_a_gradient():
    # heritable chemotactic sensitivity rises over generations when food is worth chasing
    r = run(CFG)
    assert r["chi"][-1] > r["chi"][0] + 0.4
    assert r["pop"][-1] > 0                                 # population persists


def test_neutral_tag_merely_drifts():
    # control: if chi does not affect movement it is neutral -> no directional selection
    c = run(replace(CFG, chemotaxis=False))
    assert abs(c["chi"][-1] - c["chi"][0]) < 0.2


def test_selection_beats_drift():
    rise = run(CFG)["chi"]
    drift = run(replace(CFG, chemotaxis=False))["chi"]
    assert (rise[-1] - rise[0]) > 3 * abs(drift[-1] - drift[0])


def test_flow_reduces_selected_chemotaxis():
    # the composition result: stirring does some foraging, so less chemotaxis is selected
    def chi(amp, seed):
        fl = None if amp == 0 else vortex_flow(CFG.L, amp=amp, k=2)
        return run(replace(CFG, seed=seed), flow=fl)["chi"][-5:].mean()
    noflow = np.mean([chi(0.0, s) for s in (1, 2)])
    flow = np.mean([chi(1.2, s) for s in (1, 2)])
    assert noflow > flow


def test_vortex_flow_is_divergence_free():
    ux, uy = vortex_flow(80, amp=0.7, k=2)
    div = _grad(ux)[0] + _grad(uy)[1]                      # d(ux)/dx + d(uy)/dy
    assert np.abs(div).max() < 1e-2


def test_patchiness_metric():
    rng = np.random.default_rng(0)
    rand = patchiness(rng.uniform(0, 100, 4000), rng.uniform(0, 100, 4000), 100)
    cx = np.r_[rng.normal(25, 3, 2000), rng.normal(75, 3, 2000)]
    cy = np.r_[rng.normal(25, 3, 2000), rng.normal(75, 3, 2000)]
    clustered = patchiness(cx % 100, cy % 100, 100)
    assert 0.5 < rand < 2.0                                 # Poisson baseline ~1
    assert clustered > 5 * rand                             # real clumps -> high dispersion index


def test_nutrient_stays_bounded():
    r = run(replace(CFG, steps=150))
    assert r["N"].min() >= -1e-9 and r["N"].max() <= 1.05


def test_reproducible():
    a = run(replace(CFG, steps=120))["chi"]
    b = run(replace(CFG, steps=120))["chi"]
    assert np.array_equal(a, b)
