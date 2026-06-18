"""R57 — natural selection at a million-genome scale (GPU evolution).

The project's beating heart — selection on heritable variation — fused with the
R54-R56 GPU substrate. A MILLION genomes live on the GPU as points on a rugged,
multi-peak fitness landscape (the "phenotype" is a 2D trait; the landscape is a sum
of Gaussian peaks of differing height — niches of differing quality). Each
generation, every genome is replaced by a mutated copy of the fittest among a few
randomly sampled rivals (tournament selection — embarrassingly parallel, no sorting,
no birth races). With no gradient information, the population discovers the peaks,
abandons the poor niches, and concentrates on the global optimum: evolution by
natural selection, a million genomes at a time, entirely on the GPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# rugged landscape: (cx, cy, height, width) peaks; the tallest is the global optimum
PEAKS = [(-3.0, -3.0, 0.6, 1.1), (3.5, -2.0, 0.75, 1.0), (-2.0, 3.5, 0.85, 0.9), (2.5, 3.0, 1.0, 0.8)]
GLOBAL = (2.5, 3.0)

_EVAL_SRC = """
#version 460
layout(local_size_x = 256) in;
layout(std430, binding = 0) buffer Pop { float p[]; };   // gx, gy, fitness per genome
uniform int NA;
float fit(float x, float y) {
    float f = 0.0;
    %PEAKS%
    return f;
}
void main() {
    uint i = gl_GlobalInvocationID.x; if (i >= uint(NA)) return;
    p[i*3+2] = fit(p[i*3+0], p[i*3+1]);
}
"""

_SELECT_SRC = """
#version 460
layout(local_size_x = 256) in;
layout(std430, binding = 0) buffer Old { float o[]; };
layout(std430, binding = 1) buffer New { float n[]; };
uniform int NA, K, gen; uniform float mut;
uint h(uint x){ x^=x>>16; x*=0x7feb352du; x^=x>>15; x*=0x846ca68bu; x^=x>>16; return x; }
float rnd(uint s){ return float(h(s) & 0x7fffffffu) / float(0x7fffffff); }
void main() {
    uint i = gl_GlobalInvocationID.x; if (i >= uint(NA)) return;
    uint seed = i * 747796405u + uint(gen) * 2891336453u;
    uint best = i; float bf = -1e9;
    for (int t = 0; t < K; t++) {
        uint r = h(seed + uint(t) * 0x9e3779b9u) % uint(NA);
        if (o[r*3+2] > bf) { bf = o[r*3+2]; best = r; }
    }
    // copy winner's genes + gaussian-ish mutation (sum of two uniforms)
    float m1 = (rnd(seed + 11u) + rnd(seed + 23u) - 1.0) * mut;
    float m2 = (rnd(seed + 31u) + rnd(seed + 47u) - 1.0) * mut;
    n[i*3+0] = o[best*3+0] + m1;
    n[i*3+1] = o[best*3+1] + m2;
    n[i*3+2] = 0.0;
}
"""


def _peaks_glsl() -> str:
    lines = []
    for cx, cy, hgt, w in PEAKS:
        lines.append(f"f += {hgt}*exp(-(pow(x-({cx}),2.0)+pow(y-({cy}),2.0))/(2.0*{w}*{w}));")
    return "\n    ".join(lines)


@dataclass(frozen=True)
class GpuEvoConfig:
    n_agents: int = 1_000_000
    span: float = 6.0        # initial genes uniform in [-span, span]^2
    tournament: int = 4
    mut: float = 0.12
    generations: int = 120


def run(cfg: GpuEvoConfig, seed: int = 0, record_every: int = 0, measure: bool = False):
    import time
    import moderngl
    ctx = moderngl.create_standalone_context(require=460)
    ev = ctx.compute_shader(_EVAL_SRC.replace("%PEAKS%", _peaks_glsl()))
    sel = ctx.compute_shader(_SELECT_SRC)
    NA = cfg.n_agents
    rng = np.random.default_rng(seed)
    pop = np.zeros((NA, 3), dtype=np.float32)
    pop[:, 0] = rng.uniform(-cfg.span, cfg.span, NA)
    pop[:, 1] = rng.uniform(-cfg.span, cfg.span, NA)
    A = ctx.buffer(pop.tobytes()); B = ctx.buffer(reserve=pop.nbytes)
    ev["NA"] = NA; sel["NA"] = NA; sel["K"] = cfg.tournament; sel["mut"] = cfg.mut
    gA = (NA + 255) // 256
    hist = {"gen": [], "mean_fit": [], "max_fit": [], "frac_global": []}
    snaps = {}

    def evaluate(buf):
        buf.bind_to_storage_buffer(0); ev.run(group_x=gA); ctx.memory_barrier()

    metric_every = max(1, cfg.generations // 30)

    def record(g):
        arr = np.frombuffer(A.read(), dtype=np.float32).reshape(NA, 3)
        hist["gen"].append(g); hist["mean_fit"].append(float(arr[:, 2].mean()))
        hist["max_fit"].append(float(arr[:, 2].max()))
        d = np.hypot(arr[:, 0] - GLOBAL[0], arr[:, 1] - GLOBAL[1])
        hist["frac_global"].append(float(np.mean(d < 0.7)))
        if record_every and (g % record_every == 0 or g == cfg.generations - 1):
            snaps[g] = arr[:, :2].copy()

    ctx.finish(); t0 = time.time()
    evaluate(A)
    for g in range(cfg.generations):
        if g % metric_every == 0 or g == cfg.generations - 1:
            record(g)
        A.bind_to_storage_buffer(0); B.bind_to_storage_buffer(1)
        sel["gen"] = g; sel.run(group_x=gA); ctx.memory_barrier()
        A, B = B, A
        evaluate(A)
    ctx.finish(); dt = time.time() - t0
    arr = np.frombuffer(A.read(), dtype=np.float32).reshape(NA, 3).copy()
    for b in (A, B):
        b.release()
    ctx.release()
    out = {k: np.array(v, dtype=float) for k, v in hist.items()}
    out["final"] = arr; out["snaps"] = snaps; out["steps_per_s"] = cfg.generations / dt
    if measure:
        return out["mean_fit"], out["steps_per_s"]
    return out
