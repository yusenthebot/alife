import numpy as np
import pytest

from dataclasses import replace

from alife.gpulenia import LeniaConfig, _ring_kernel, persistent, run


def _gpu_or_skip():
    try:
        import moderngl
        ctx = moderngl.create_standalone_context(require=460)
        ctx.compute_shader("#version 460\nlayout(local_size_x=1) in;\n"
                           "layout(std430,binding=0) buffer B{float v[];};\nvoid main(){v[0]=1.0;}")
        ctx.release()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"no GL4.6 compute context: {e}")


def test_ring_kernel_normalized():
    k = _ring_kernel(13)
    assert abs(k.sum() - 1.0) < 1e-5
    assert k[13, 13] < 1e-3                 # near-hollow centre (ring peaks at r=0.5)
    assert k[13, 13] < k[13, 13 + 6]        # center weaker than the ring


def test_persistent_structured_pattern():
    _gpu_or_skip()
    m, s = persistent(LeniaConfig(size=256), steps=300, seed=0)
    assert 0.02 < m < 0.6                    # alive but not saturated
    assert s > 0.15                          # structured (not uniform)


def test_field_stays_bounded():
    _gpu_or_skip()
    r = run(LeniaConfig(size=256), steps=200, seed=0)
    assert np.all(r["field"] >= 0) and np.all(r["field"] <= 1)
    assert np.all(np.isfinite(r["field"]))


def test_wrong_regime_dies():
    """A growth peak the soup never reaches -> pattern dies out (control)."""
    _gpu_or_skip()
    m, s = persistent(replace(LeniaConfig(size=256), mu=0.6, sigma=0.01), steps=200, seed=0)
    assert m < 0.02


def test_reproducible():
    _gpu_or_skip()
    a = run(LeniaConfig(size=128), steps=120, seed=2)["field"]
    b = run(LeniaConfig(size=128), steps=120, seed=2)["field"]
    assert np.allclose(a, b, atol=1e-4)
