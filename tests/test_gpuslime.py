import numpy as np
import pytest

from alife.gpuslime import SlimeConfig, run


def _gpu_or_skip():
    try:
        import moderngl
        ctx = moderngl.create_standalone_context(require=460)
        ctx.compute_shader("#version 460\nlayout(local_size_x=1) in;\n"
                           "layout(std430,binding=0) buffer B{uint v[];};\nvoid main(){atomicAdd(v[0],1u);}")
        ctx.release()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"no GL4.6 compute context: {e}")


def test_runs_at_scale():
    _gpu_or_skip()
    cfg = SlimeConfig(n_agents=300_000, width=512, height=512)
    trail = run(cfg, steps=200, seed=0)
    assert trail.shape == (512, 512)
    assert np.all(np.isfinite(trail))
    assert trail.max() > 0


def test_networks_self_organize():
    """Stigmergy alone produces filament structure: high std/mean, sparse occupancy."""
    _gpu_or_skip()
    cfg = SlimeConfig(n_agents=400_000, width=512, height=512)
    trail = run(cfg, steps=300, seed=0)
    structure = trail.std() / max(trail.mean(), 1e-6)
    assert structure > 3.0                      # filaments, not a uniform wash
    assert np.mean(trail > 0) < 0.6             # agents concentrate into channels


def test_structure_rises_over_time():
    _gpu_or_skip()
    cfg = SlimeConfig(n_agents=400_000, width=512, height=512)
    r = run(cfg, steps=300, seed=0, record_every=60)
    s = r["structure"][:, 1]
    assert s[-1] > s[0] + 1.0                    # organization increases


def test_robust_across_seeds():
    _gpu_or_skip()
    cfg = SlimeConfig(n_agents=300_000, width=512, height=512)
    for seed in (0, 1):
        trail = run(cfg, steps=280, seed=seed)
        assert trail.std() / max(trail.mean(), 1e-6) > 2.5   # clearly filamentous, robust across seeds
