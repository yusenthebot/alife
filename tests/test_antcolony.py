import numpy as np

from alife.antcolony import AntConfig, simulate, trail_strength, deneubourg_bridge


def test_double_bridge_picks_short():
    # branch A is shorter -> P(A) must rise to near 1 across seeds
    for s in range(6):
        pa = deneubourg_bridge(len_a=1.0, len_b=2.0, steps=400, seed=s)
        assert pa[0] == 0.5                      # starts unbiased
        assert pa[-1] > 0.9                       # locks onto the short arm


def test_double_bridge_symmetry_breaking():
    # equal arms -> each run fixates on ONE arm (not stuck at 0.5), and not always the same
    ends = [deneubourg_bridge(1.0, 1.0, steps=400, seed=s)[-1] for s in range(16)]
    assert all(e > 0.85 or e < 0.15 for e in ends)     # fixates, never stuck at the unstable 0.5
    assert any(e > 0.85 for e in ends) and any(e < 0.15 for e in ends)   # both arms win across seeds


def test_more_asymmetric_converges_at_least_as_fast():
    slow = deneubourg_bridge(1.0, 1.25, steps=400, seed=0)
    fast = deneubourg_bridge(1.0, 3.0, steps=400, seed=0)
    # a sharper length difference reaches high confidence no later than a shallow one
    def first_above(p, th=0.9):
        idx = np.argmax(p > th)
        return idx if p[idx] > th else len(p)
    assert first_above(fast) <= first_above(slow)


def test_spatial_trail_forms():
    cfg = AntConfig(size=160, n_ants=400)
    r = simulate(cfg, steps=900, seed=0)
    on = trail_strength(r["trail"], r["nest"], r["foods"][0])
    off = trail_strength(r["trail"], r["nest"], np.array([20.0, 80.0]))
    assert on > 5 * off                          # a real corridor, not diffuse background
    assert r["delivered"][-1] > 0                 # food is actually being delivered


def test_foraging_accelerates():
    cfg = AntConfig(size=160, n_ants=400)
    r = simulate(cfg, steps=1000, seed=1)
    d = r["delivered"]
    first_half = d[len(d) // 2]
    second_half = d[-1] - d[len(d) // 2]
    assert second_half > first_half              # rate rises once the trail exists


def test_reproducible():
    cfg = AntConfig(size=120, n_ants=200)
    a = simulate(cfg, steps=300, seed=3)["delivered"][-1]
    b = simulate(cfg, steps=300, seed=3)["delivered"][-1]
    assert a == b
