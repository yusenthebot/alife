import numpy as np
import pytest

from alife.gpuboids import BoidsConfig, order_vs_noise, run


def _gpu_or_skip():
    try:
        import moderngl
        ctx = moderngl.create_standalone_context(require=460)
        ctx.compute_shader("#version 460\nlayout(local_size_x=1) in;\n"
                           "layout(std430,binding=0) buffer B{int v[];};\nvoid main(){atomicAdd(v[0],1);}")
        ctx.release()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"no GL4.6 compute context: {e}")


def test_flocking_emerges_at_low_noise():
    _gpu_or_skip()
    cfg = BoidsConfig(n_agents=300_000, world=512, grid=48, noise=0.08)
    r = run(cfg, steps=500, seed=0, record_every=100)
    oh = r["order_hist"]
    assert oh[0, 1] < 0.3                  # starts disordered
    assert oh[-1, 1] > 0.7                  # ends flocked


def test_disorder_at_high_noise():
    _gpu_or_skip()
    cfg = BoidsConfig(n_agents=300_000, world=512, grid=48, noise=0.95)
    r = run(cfg, steps=400, seed=0)
    assert r["order"] < 0.35               # noise destroys order


def test_phase_transition():
    _gpu_or_skip()
    cfg = BoidsConfig(n_agents=250_000, world=512, grid=48)
    ov = order_vs_noise(cfg, [0.05, 0.9], steps=500)
    assert ov[0] > ov[1] + 0.4             # low-noise order >> high-noise order


def test_runs_at_million():
    _gpu_or_skip()
    r = run(BoidsConfig(n_agents=1_000_000, grid=64), steps=120, seed=0)
    assert r["agents"].shape == (1_000_000, 3)
    assert np.all(np.isfinite(r["agents"]))
