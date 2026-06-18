import numpy as np
import pytest

from dataclasses import replace

from alife.gpuevo import PEAKS, GpuEvoConfig, run


def _gpu_or_skip():
    try:
        import moderngl
        ctx = moderngl.create_standalone_context(require=460)
        ctx.compute_shader("#version 460\nlayout(local_size_x=1) in;\n"
                           "layout(std430,binding=0) buffer B{float v[];};\nvoid main(){v[0]=1.0;}")
        ctx.release()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"no GL4.6 compute context: {e}")


def test_selection_raises_fitness():
    _gpu_or_skip()
    r = run(GpuEvoConfig(n_agents=200_000, generations=60), seed=0)
    assert r["mean_fit"][-1] > r["mean_fit"][0] + 0.5


def test_finds_global_optimum():
    _gpu_or_skip()
    r = run(GpuEvoConfig(n_agents=200_000, generations=80), seed=0)
    global_h = max(p[2] for p in PEAKS)
    assert r["mean_fit"][-1] > 0.9 * global_h     # converged near the global peak height
    assert r["frac_global"][-1] > 0.8             # most of the population on the global optimum


def test_no_selection_no_progress():
    """Tournament size 1 = neutral copying (no selection): fitness must not climb."""
    _gpu_or_skip()
    r = run(replace(GpuEvoConfig(n_agents=200_000, generations=60), tournament=1), seed=0)
    assert r["mean_fit"][-1] < r["mean_fit"][0] + 0.25


def test_runs_at_million():
    _gpu_or_skip()
    r = run(GpuEvoConfig(n_agents=1_000_000, generations=30), seed=0)
    assert r["final"].shape == (1_000_000, 3)
    assert np.all(np.isfinite(r["final"]))
