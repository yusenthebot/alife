import numpy as np
import pytest

from alife.gpurd import GpuRDConfig, run_cpu_ref, run_gpu


def _gpu_or_skip():
    try:
        import moderngl
        ctx = moderngl.create_standalone_context(require=460)
        ctx.compute_shader("#version 460\nlayout(local_size_x=1) in;\nvoid main(){}")
        ctx.release()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"no GL4.6 compute context: {e}")


def test_gpu_matches_cpu_reference():
    """The correctness gate: the compute shader matches a float32 numpy reference."""
    _gpu_or_skip()
    cfg = GpuRDConfig(size=64, seed_blocks=6)
    F, k = 0.0545, 0.062
    g = run_gpu(F, k, cfg, steps=60, seed=0)
    c = run_cpu_ref(F, k, cfg, steps=60, seed=0)
    assert np.allclose(g, c, atol=1e-4)


def test_runs_at_megascale():
    _gpu_or_skip()
    V = run_gpu(0.0367, 0.0649, GpuRDConfig(size=1024), steps=500, seed=0)
    assert V.shape == (1024, 1024)
    assert V.std() > 0.005                 # a real pattern formed
    assert np.all(np.isfinite(V))


def test_gpu_faster_than_cpu():
    _gpu_or_skip()
    import time
    cfg = GpuRDConfig(size=256)
    _, gpu_sps = run_gpu(0.0367, 0.0649, cfg, steps=200, seed=0, measure=True)
    t0 = time.time(); run_cpu_ref(0.0367, 0.0649, cfg, steps=100, seed=0)
    cpu_sps = 100 / (time.time() - t0)
    assert gpu_sps > cpu_sps                # GPU wins at scale


def test_reproducible():
    _gpu_or_skip()
    cfg = GpuRDConfig(size=64, seed_blocks=6)
    a = run_gpu(0.0367, 0.0649, cfg, steps=50, seed=1)
    b = run_gpu(0.0367, 0.0649, cfg, steps=50, seed=1)
    assert np.allclose(a, b, atol=1e-5)
