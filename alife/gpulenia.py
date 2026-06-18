"""R60 — Lenia: continuous cellular automata "creatures" on the GPU.

Lenia (Bert Chan 2019) generalises Conway's Life to continuous states, space-time
and a smooth ring-shaped neighbourhood kernel: a cell's next value is its current
value nudged by a bell-shaped growth function of the kernel-weighted average of its
neighbours. From smooth random soup, the right parameter regime self-organises into
soft, life-like blobs that persist, pulse, glide and split — the most organism-like
patterns in cellular automata. Deferred at R47 (the exact Orbium glider needs its
published seed and dies from random init); the GPU substrate makes it cheap to scan
parameter space and run a persistent-structure regime at scale.

Direct GPU convolution (ring kernel, radius R) + bell growth, ping-pong buffers.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

_SRC = """
#version 460
layout(local_size_x = 16, local_size_y = 16) in;
layout(std430, binding = 0) readonly buffer AIn  { float a_in[]; };
layout(std430, binding = 1) writeonly buffer AOut { float a_out[]; };
layout(std430, binding = 2) readonly buffer Kern { float kern[]; };
uniform int N, R; uniform float mu, sigma, T;
int idx(int x, int y) { x = (x + N) % N; y = (y + N) % N; return y * N + x; }
float bell(float u, float m, float s) { float d = (u - m) / s; return exp(-0.5 * d * d); }
void main() {
    int x = int(gl_GlobalInvocationID.x), y = int(gl_GlobalInvocationID.y);
    if (x >= N || y >= N) return;
    int K = 2 * R + 1;
    float u = 0.0;
    for (int dy = -R; dy <= R; dy++)
        for (int dx = -R; dx <= R; dx++)
            u += kern[(dy + R) * K + (dx + R)] * a_in[idx(x + dx, y + dy)];
    float g = 2.0 * bell(u, mu, sigma) - 1.0;        // growth in [-1, 1]
    float v = a_in[idx(x, y)] + (1.0 / T) * g;
    a_out[idx(x, y)] = clamp(v, 0.0, 1.0);
}
"""


@dataclass(frozen=True)
class LeniaConfig:
    size: int = 256
    R: int = 13
    T: float = 10.0
    mu: float = 0.15
    sigma: float = 0.018      # persistent, structured regime (scanned)


def _ring_kernel(R: int) -> np.ndarray:
    y, x = np.ogrid[-R:R + 1, -R:R + 1]
    r = np.sqrt(x * x + y * y) / R
    k = np.where(r < 1.0, np.exp(-0.5 * ((r - 0.5) / 0.15) ** 2), 0.0)
    return (k / k.sum()).astype(np.float32)


def _smooth_seed(N, R, rng, patches=18):
    """Smooth random soup of overlapping blobs (white noise dies in Lenia)."""
    A = np.zeros((N, N), dtype=np.float32)
    yy, xx = np.mgrid[0:N, 0:N]
    for _ in range(patches):
        cx, cy = rng.integers(0, N, 2); rad = rng.integers(R, 3 * R)
        d2 = (xx - cx) ** 2 + (yy - cy) ** 2
        A += (rng.random() * np.exp(-d2 / (2 * rad * rad))).astype(np.float32)
    return np.clip(A, 0, 1).astype(np.float32)


def run(cfg: LeniaConfig, steps: int, seed: int = 0, measure: bool = False, record_every: int = 0):
    import time
    import moderngl
    ctx = moderngl.create_standalone_context(require=460)
    cs = ctx.compute_shader(_SRC)
    N, R = cfg.size, cfg.R
    cs["N"] = N; cs["R"] = R; cs["T"] = cfg.T; cs["mu"] = cfg.mu; cs["sigma"] = cfg.sigma
    rng = np.random.default_rng(seed)
    A = _smooth_seed(N, R, rng)
    ker = _ring_kernel(R)
    aa = ctx.buffer(A.tobytes()); ab = ctx.buffer(reserve=A.nbytes)
    kb = ctx.buffer(ker.tobytes()); kb.bind_to_storage_buffer(2)
    gx = (N + 15) // 16
    mass = []; snaps = {}
    ctx.finish(); t0 = time.time()
    for f in range(steps):
        aa.bind_to_storage_buffer(0); ab.bind_to_storage_buffer(1)
        cs.run(group_x=gx, group_y=gx); ctx.memory_barrier()
        aa, ab = ab, aa
        if record_every and (f % record_every == 0 or f == steps - 1):
            fld = np.frombuffer(aa.read(), dtype=np.float32).reshape(N, N)
            mass.append((f, float(fld.sum()), float(fld.std())))
            snaps[f] = fld.copy()
    ctx.finish(); dt = time.time() - t0
    fld = np.frombuffer(aa.read(), dtype=np.float32).reshape(N, N).copy()
    for b in (aa, ab, kb):
        b.release()
    ctx.release()
    out = {"field": fld, "mass": np.array(mass, dtype=float), "snaps": snaps, "steps_per_s": steps / dt}
    if measure:
        return fld, steps / dt
    return out


def persistent(cfg: LeniaConfig, steps: int = 300, seed: int = 0) -> tuple:
    """(final mass fraction, structure std) — alive & structured if mass in (0.01,0.6) and std high."""
    fld = run(cfg, steps, seed)["field"]
    return float(fld.mean()), float(fld.std())
