"""R54 — the GPU substrate leap: million-cell morphogenesis on compute shaders.

The runner-up frontier from the divergence study: move the simulation itself onto
the GPU. This ports R45's Gray-Scott reaction-diffusion to a GLSL compute shader on
the RTX 5080, so the whole field updates in parallel. It lets the living patterns
run at 1024x1024 = 1.05 MILLION cells (~26x the CPU round's 200x200) at hundreds of
steps per second — the 100-1000x substrate every future round can stand on.

Correctness is gated, not assumed: the shader is verified step-for-step against a
float32 numpy reference of the identical update before any claim about scale.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

_COMPUTE_SRC = """
#version 460
layout(local_size_x = 16, local_size_y = 16) in;
layout(std430, binding = 0) readonly buffer UIn  { float u_in[]; };
layout(std430, binding = 1) readonly buffer VIn  { float v_in[]; };
layout(std430, binding = 2) writeonly buffer UOut { float u_out[]; };
layout(std430, binding = 3) writeonly buffer VOut { float v_out[]; };
uniform int N;
uniform float Du, Dv, F, K, dt;
int idx(int x, int y) { x = (x + N) % N; y = (y + N) % N; return y * N + x; }
void main() {
    int x = int(gl_GlobalInvocationID.x);
    int y = int(gl_GlobalInvocationID.y);
    if (x >= N || y >= N) return;
    int c = idx(x, y);
    float lu = 0.20 * (u_in[idx(x-1,y)] + u_in[idx(x+1,y)] + u_in[idx(x,y-1)] + u_in[idx(x,y+1)])
             + 0.05 * (u_in[idx(x-1,y-1)] + u_in[idx(x+1,y-1)] + u_in[idx(x-1,y+1)] + u_in[idx(x+1,y+1)])
             - u_in[c];
    float lv = 0.20 * (v_in[idx(x-1,y)] + v_in[idx(x+1,y)] + v_in[idx(x,y-1)] + v_in[idx(x,y+1)])
             + 0.05 * (v_in[idx(x-1,y-1)] + v_in[idx(x+1,y-1)] + v_in[idx(x-1,y+1)] + v_in[idx(x+1,y+1)])
             - v_in[c];
    float u = u_in[c], v = v_in[c];
    float uvv = u * v * v;
    u_out[c] = clamp(u + (Du * lu - uvv + F * (1.0 - u)) * dt, 0.0, 1.0);
    v_out[c] = clamp(v + (Dv * lv + uvv - (F + K) * v) * dt, 0.0, 1.0);
}
"""


@dataclass(frozen=True)
class GpuRDConfig:
    size: int = 1024
    du: float = 0.16
    dv: float = 0.08
    dt: float = 1.0
    seed_blocks: int = 60


def _seed(N, blocks, seed):
    rng = np.random.default_rng(seed)
    U = np.ones((N, N), dtype=np.float32)
    V = np.zeros((N, N), dtype=np.float32)
    b = max(3, N // 64)
    for _ in range(blocks):
        x, y = rng.integers(0, N - b, 2)
        U[x:x+b, y:y+b] = 0.5
        V[x:x+b, y:y+b] = 0.25
    return U, V


def run_gpu(F, k, cfg: GpuRDConfig, steps: int, seed: int = 0, measure: bool = False):
    import time
    import moderngl
    N = cfg.size
    ctx = moderngl.create_standalone_context(require=460)
    cs = ctx.compute_shader(_COMPUTE_SRC)
    cs["N"] = N; cs["Du"] = cfg.du; cs["Dv"] = cfg.dv
    cs["F"] = float(F); cs["K"] = float(k); cs["dt"] = cfg.dt
    U, V = _seed(N, cfg.seed_blocks, seed)
    ua = ctx.buffer(U.tobytes()); va = ctx.buffer(V.tobytes())
    ub = ctx.buffer(reserve=U.nbytes); vb = ctx.buffer(reserve=V.nbytes)
    gx = (N + 15) // 16
    ctx.finish()
    t0 = time.time()
    for _ in range(steps):
        ua.bind_to_storage_buffer(0); va.bind_to_storage_buffer(1)
        ub.bind_to_storage_buffer(2); vb.bind_to_storage_buffer(3)
        cs.run(group_x=gx, group_y=gx)
        ctx.memory_barrier()                  # ensure this step's writes are visible to the next
        ua, ub = ub, ua; va, vb = vb, va     # ping-pong
    ctx.finish()
    dt = time.time() - t0
    Vout = np.frombuffer(va.read(), dtype=np.float32).reshape(N, N)
    for b_ in (ua, va, ub, vb):
        b_.release()
    ctx.release()
    if measure:
        return Vout, steps / dt
    return Vout


def _laplacian32(a):
    return (0.20 * (np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1))
            + 0.05 * (np.roll(np.roll(a, 1, 0), 1, 1) + np.roll(np.roll(a, 1, 0), -1, 1)
                      + np.roll(np.roll(a, -1, 0), 1, 1) + np.roll(np.roll(a, -1, 0), -1, 1))
            - a).astype(np.float32)


def run_cpu_ref(F, k, cfg: GpuRDConfig, steps: int, seed: int = 0):
    """Identical update in float32 numpy — the equivalence reference for the shader."""
    U, V = _seed(cfg.size, cfg.seed_blocks, seed)
    for _ in range(steps):
        uvv = U * V * V
        U = np.clip(U + (cfg.du * _laplacian32(U) - uvv + F * (1 - U)) * cfg.dt, 0, 1).astype(np.float32)
        V = np.clip(V + (cfg.dv * _laplacian32(V) + uvv - (F + k) * V) * cfg.dt, 0, 1).astype(np.float32)
    return V
