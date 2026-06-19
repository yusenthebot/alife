import numpy as np

from alife.gierermeinhardt import run, count_spots, stripe_index, gm_step, GMConfig

# fewer steps for fast tests (patterns are well-formed by ~3500 steps)
FAST = GMConfig(steps=3500)


def test_homogeneous_stays_homogeneous_without_noise():
    # exactly uniform a=h=1 is the steady state -> no pattern forms (Turing needs a seed)
    cfg = GMConfig(steps=200)
    a = np.ones((40, 40)); h = np.ones((40, 40))
    for _ in range(cfg.steps):
        a, h = gm_step(a, h, cfg)
    assert np.ptp(a) < 1e-3                       # stays flat


def test_pattern_forms_spots_on_a_square():
    a = run((100, 100), FAST, seed=1)
    assert count_spots(a) > 30                    # a clear spotted pattern emerges
    assert np.ptp(a) > 1.0                        # strong contrast (not homogeneous)
    assert stripe_index(a) < 1.5                  # roundish: spots, not stripes


def test_spot_count_scales_with_area():
    small = count_spots(run((50, 50), FAST, seed=2))
    big = count_spots(run((110, 110), FAST, seed=2))
    # intrinsic wavelength -> count tracks area (110^2/50^2 ~ 4.8x); allow generous slack
    assert big > 2.5 * small


def test_narrow_domain_makes_more_stripes_than_wide():
    wide = stripe_index(run((90, 90), FAST, seed=3))
    narrow = stripe_index(run((8, 170), FAST, seed=3))
    assert narrow > wide + 0.2                    # narrowing elongates spots into stripes


def test_inhibitor_is_broader_than_activator():
    # the GM mechanism: inhibitor h is a smoother/broader field than activator a
    a, h = run((90, 90), FAST, seed=4, return_h=True)
    # spatial roughness (mean |gradient|) is lower for the broader inhibitor
    rough = lambda f: np.abs(np.diff(f, axis=0)).mean() + np.abs(np.diff(f, axis=1)).mean()
    an = a / a.mean(); hn = h / h.mean()
    assert rough(hn) < rough(an)                   # h varies more gently -> long-range


def test_reproducible():
    a = run((40, 40), GMConfig(steps=500), seed=9)
    b = run((40, 40), GMConfig(steps=500), seed=9)
    assert np.array_equal(a, b)
