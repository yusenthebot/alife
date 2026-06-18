"""R59 — local adaptation at a million-genome scale (GPU spatial evolution).

The synthesis of the GPU arc with the project's evolutionary heart, made spatial.
A million agents live across a world of distinct "biomes" — a static field T(x,y)
giving the locally-favoured trait value (different regions reward different
genotypes). Each agent carries a heritable trait g and is fitter the better g
matches its local T. Selection is LOCAL: each generation an agent adopts (with
mutation) the best-matching genotype found in its own neighbourhood (a per-cell
fitness-packed atomicMax). With agents barely diffusing, every region's population
converges on its local optimum — and the genetic map comes to MIRROR the
environmental map. Local adaptation and the formation of clines, a million genomes
at a time, entirely on the GPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# biomes: Gaussian regions imposing distinct favoured trait values on a 0.5 baseline
_T_GLSL = """
float Tfield(float x, float y, float W) {
    float t = 0.5;
    t += 0.45 * exp(-(pow(x-0.25*W,2.0)+pow(y-0.25*W,2.0))/(2.0*pow(0.13*W,2.0)));   // high-trait biome
    t -= 0.45 * exp(-(pow(x-0.75*W,2.0)+pow(y-0.30*W,2.0))/(2.0*pow(0.13*W,2.0)));   // low-trait biome
    t += 0.30 * exp(-(pow(x-0.70*W,2.0)+pow(y-0.75*W,2.0))/(2.0*pow(0.12*W,2.0)));
    t -= 0.30 * exp(-(pow(x-0.25*W,2.0)+pow(y-0.78*W,2.0))/(2.0*pow(0.12*W,2.0)));
    return clamp(t, 0.0, 1.0);
}
"""

_DEPOSIT_SRC = """
#version 460
layout(local_size_x = 256) in;
layout(std430, binding = 0) buffer Agents { float ag[]; };   // x, y, g
layout(std430, binding = 1) buffer Grid { uint best[]; };    // packed (fitness<<10 | gene)
uniform int NA, GW; uniform float W, sigma;
%T%
void main() {
    uint i = gl_GlobalInvocationID.x; if (i >= uint(NA)) return;
    float x=ag[i*3+0], y=ag[i*3+1], g=ag[i*3+2];
    float f = exp(-pow(g - Tfield(x,y,W),2.0)/(2.0*sigma*sigma));
    int cx=int(x/W*float(GW))%GW, cy=int(y/W*float(GW))%GW; int c=cy*GW+cx;
    uint pk = (uint(f*1023.0) << 10) | uint(g*1023.0);
    atomicMax(best[c], pk);
}
"""

_SELECT_SRC = """
#version 460
layout(local_size_x = 256) in;
layout(std430, binding = 0) buffer Agents { float ag[]; };
layout(std430, binding = 1) buffer Grid { uint best[]; };
uniform int NA, GW, gen; uniform float W, sigma, mut, diffuse;
%T%
uint h(uint x){ x^=x>>16; x*=0x7feb352du; x^=x>>15; x*=0x846ca68bu; x^=x>>16; return x; }
float rnd(uint s){ return float(h(s)&0x7fffffffu)/float(0x7fffffff); }
void main() {
    uint i = gl_GlobalInvocationID.x; if (i >= uint(NA)) return;
    float x=ag[i*3+0], y=ag[i*3+1], g=ag[i*3+2];
    int cx=int(x/W*float(GW)), cy=int(y/W*float(GW));
    uint bestp = 0u;
    for (int dy=-1; dy<=1; dy++) for (int dx=-1; dx<=1; dx++) {
        int nx=((cx+dx)%GW+GW)%GW, ny=((cy+dy)%GW+GW)%GW;
        bestp = max(bestp, best[ny*GW+nx]);
    }
    float bf = float(bestp >> 10) / 1023.0;
    float bg = float(bestp & 1023u) / 1023.0;
    float myf = exp(-pow(g - Tfield(x,y,W),2.0)/(2.0*sigma*sigma));
    uint seed = i*747796405u + uint(gen)*2891336453u;
    if (bf > myf) g = bg + (rnd(seed)+rnd(seed+7u)-1.0)*mut;   // adopt local-best genotype + mutation
    g = clamp(g, 0.0, 1.0);
    x = mod(x + (rnd(seed+11u)-0.5)*2.0*diffuse, W);          // small diffusion
    y = mod(y + (rnd(seed+23u)-0.5)*2.0*diffuse, W);
    ag[i*3+0]=x; ag[i*3+1]=y; ag[i*3+2]=g;
}
"""


@dataclass(frozen=True)
class EcoEvoConfig:
    world: float = 1024.0
    n_agents: int = 1_000_000
    grid: int = 128
    sigma: float = 0.12       # fitness match width
    mut: float = 0.03
    diffuse: float = 4.0      # agent random-walk per generation (small => local adaptation)
    generations: int = 120


def _T_numpy(W, n=256):
    g = np.linspace(0, W, n); X, Y = np.meshgrid(g, g)
    t = np.full_like(X, 0.5)
    t += 0.45*np.exp(-((X-0.25*W)**2+(Y-0.25*W)**2)/(2*(0.13*W)**2))
    t -= 0.45*np.exp(-((X-0.75*W)**2+(Y-0.30*W)**2)/(2*(0.13*W)**2))
    t += 0.30*np.exp(-((X-0.70*W)**2+(Y-0.75*W)**2)/(2*(0.12*W)**2))
    t -= 0.30*np.exp(-((X-0.25*W)**2+(Y-0.78*W)**2)/(2*(0.12*W)**2))
    return np.clip(t, 0, 1)


def _Tfield_at(x, y, W):
    t = np.full(x.shape, 0.5)
    t += 0.45*np.exp(-((x-0.25*W)**2+(y-0.25*W)**2)/(2*(0.13*W)**2))
    t -= 0.45*np.exp(-((x-0.75*W)**2+(y-0.30*W)**2)/(2*(0.13*W)**2))
    t += 0.30*np.exp(-((x-0.70*W)**2+(y-0.75*W)**2)/(2*(0.12*W)**2))
    t -= 0.30*np.exp(-((x-0.25*W)**2+(y-0.78*W)**2)/(2*(0.12*W)**2))
    return np.clip(t, 0, 1)


def run(cfg: EcoEvoConfig, seed: int = 0, record_every: int = 0):
    import moderngl
    ctx = moderngl.create_standalone_context(require=460)
    dep = ctx.compute_shader(_DEPOSIT_SRC.replace("%T%", _T_GLSL))
    sel = ctx.compute_shader(_SELECT_SRC.replace("%T%", _T_GLSL))
    NA, GW = cfg.n_agents, cfg.grid
    rng = np.random.default_rng(seed)
    ag = np.empty((NA, 3), dtype=np.float32)
    ag[:, 0] = rng.random(NA) * cfg.world
    ag[:, 1] = rng.random(NA) * cfg.world
    ag[:, 2] = rng.random(NA)
    abuf = ctx.buffer(ag.tobytes())
    grid = ctx.buffer(reserve=GW*GW*4)
    for cs in (dep, sel):
        cs["NA"] = NA; cs["GW"] = GW; cs["W"] = cfg.world; cs["sigma"] = cfg.sigma
    sel["mut"] = cfg.mut; sel["diffuse"] = cfg.diffuse
    gA = (NA + 255) // 256
    hist = {"gen": [], "corr": []}
    snaps = {}

    def corr_and_snap(g):
        arr = np.frombuffer(abuf.read(), dtype=np.float32).reshape(NA, 3)
        T = _Tfield_at(arr[:, 0], arr[:, 1], cfg.world)
        c = np.corrcoef(arr[:, 2], T)[0, 1]
        hist["gen"].append(g); hist["corr"].append(float(c if np.isfinite(c) else 0.0))
        if record_every and (g % record_every == 0 or g == cfg.generations - 1):
            snaps[g] = arr.copy()

    metric_every = max(1, cfg.generations // 30)
    ctx.finish()
    for g in range(cfg.generations):
        if g % metric_every == 0 or g == cfg.generations - 1:
            corr_and_snap(g)
        grid.clear()
        abuf.bind_to_storage_buffer(0); grid.bind_to_storage_buffer(1)
        dep.run(group_x=gA); ctx.memory_barrier()
        sel["gen"] = g; sel.run(group_x=gA); ctx.memory_barrier()
    corr_and_snap(cfg.generations)
    ctx.finish()
    arr = np.frombuffer(abuf.read(), dtype=np.float32).reshape(NA, 3).copy()
    for b in (abuf, grid):
        b.release()
    ctx.release()
    out = {k: np.array(v, dtype=float) for k, v in hist.items()}
    out["final"] = arr; out["snaps"] = snaps
    return out
