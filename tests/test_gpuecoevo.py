import numpy as np
import pytest

from dataclasses import replace

from alife.gpuecoevo import EcoEvoConfig, _Tfield_at, run


def _gpu_or_skip():
    try:
        import moderngl
        ctx = moderngl.create_standalone_context(require=460)
        ctx.compute_shader("#version 460\nlayout(local_size_x=1) in;\n"
                           "layout(std430,binding=0) buffer B{uint v[];};\nvoid main(){atomicMax(v[0],1u);}")
        ctx.release()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"no GL4.6 compute context: {e}")


def test_local_adaptation_emerges():
    _gpu_or_skip()
    r = run(EcoEvoConfig(n_agents=400_000, generations=100), seed=0)
    assert r["corr"][0] < 0.2                  # starts uncorrelated
    assert r["corr"][-1] > 0.85                 # genetic map mirrors environment


def test_genes_match_local_biome():
    _gpu_or_skip()
    r = run(EcoEvoConfig(n_agents=400_000, generations=100), seed=0)
    arr = r["final"]; T = _Tfield_at(arr[:, 0], arr[:, 1], 1024.0)
    assert arr[T > 0.7, 2].mean() > 0.65       # high-T biome -> high gene
    assert arr[T < 0.3, 2].mean() < 0.35       # low-T biome -> low gene


def test_high_diffusion_weakens_local_adaptation():
    """Locality matters: heavy mixing blurs genes across biomes -> weaker correlation."""
    _gpu_or_skip()
    local = run(EcoEvoConfig(n_agents=300_000, generations=100, diffuse=4.0), seed=0)
    mixed = run(EcoEvoConfig(n_agents=300_000, generations=100, diffuse=120.0), seed=0)
    assert local["corr"][-1] > mixed["corr"][-1] + 0.1


def test_runs_at_million():
    _gpu_or_skip()
    r = run(EcoEvoConfig(n_agents=1_000_000, generations=40), seed=0)
    assert r["final"].shape == (1_000_000, 3)
    assert np.all(np.isfinite(r["final"]))
