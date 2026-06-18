"""R56 — a million boids: field-mediated flocking at megascale on the GPU.

Full circle. The project opened (R1) with ~700 Reynolds boids on the CPU; this
closes the loop with a MILLION agents flocking on the R54/R55 GPU substrate. To
scale past per-agent neighbour lists, alignment is mediated through a coarse grid
(stigmergy again): every agent deposits its heading into its grid cell, then reads
the average heading of its 3x3 neighbourhood and turns toward it, plus noise — the
Vicsek model (1995). It shows the famous order-disorder phase transition: below a
critical noise the million agents spontaneously align into one flock (order
parameter phi -> 1); above it, disorder (phi -> 0). Collective order with no
leader, at a scale the CPU rounds could never reach.

Three GPU passes/step: clear grid, deposit heading (atomic), align+move.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

_SCALE = 10000.0   # fixed-point scale for atomic int sums of cos/sin

_DEPOSIT_SRC = """
#version 460
layout(local_size_x = 256) in;
layout(std430, binding = 0) buffer Agents { float ag[]; };   // x, y, heading
layout(std430, binding = 1) buffer Gcos { int gcos[]; };
layout(std430, binding = 2) buffer Gsin { int gsin[]; };
layout(std430, binding = 3) buffer Gcnt { int gcnt[]; };
uniform int NA, GW, GH; uniform float cell, SCALE;
void main() {
    uint i = gl_GlobalInvocationID.x; if (i >= uint(NA)) return;
    int cx = int(ag[i*3+0] / cell) % GW;
    int cy = int(ag[i*3+1] / cell) % GH;
    int c = cy * GW + cx;
    float h = ag[i*3+2];
    atomicAdd(gcos[c], int(cos(h) * SCALE));
    atomicAdd(gsin[c], int(sin(h) * SCALE));
    atomicAdd(gcnt[c], 1);
}
"""

_UPDATE_SRC = """
#version 460
layout(local_size_x = 256) in;
layout(std430, binding = 0) buffer Agents { float ag[]; };
layout(std430, binding = 1) buffer Gcos { int gcos[]; };
layout(std430, binding = 2) buffer Gsin { int gsin[]; };
layout(std430, binding = 3) buffer Gcnt { int gcnt[]; };
uniform int NA, GW, GH, frame; uniform float cell, v0, noise, W, H;
float hash(uint n){ n=(n<<13)^n; n=n*(n*n*15731u+789221u)+1376312589u; return float(n&0x7fffffffu)/float(0x7fffffff); }
void main() {
    uint i = gl_GlobalInvocationID.x; if (i >= uint(NA)) return;
    float x = ag[i*3+0], y = ag[i*3+1];
    int cx = int(x / cell), cy = int(y / cell);
    float sc = 0.0, ss = 0.0;
    for (int dy=-1; dy<=1; dy++) for (int dx=-1; dx<=1; dx++) {
        int nx=((cx+dx)%GW+GW)%GW, ny=((cy+dy)%GH+GH)%GH; int c=ny*GW+nx;
        sc += float(gcos[c]); ss += float(gsin[c]);
    }
    float h = atan(ss, sc);                                  // average neighbourhood heading
    h += (hash(i + uint(frame)*2654435761u) - 0.5) * 2.0 * noise * 3.14159265;
    x = mod(x + cos(h)*v0, W); y = mod(y + sin(h)*v0, H);
    ag[i*3+0]=x; ag[i*3+1]=y; ag[i*3+2]=h;
}
"""


@dataclass(frozen=True)
class BoidsConfig:
    world: float = 1024.0
    n_agents: int = 1_000_000
    grid: int = 64            # coarse interaction grid (cell = world/grid); larger cell = longer-range alignment
    v0: float = 2.0
    noise: float = 0.10       # fraction of pi of random turning


def _order(headings: np.ndarray) -> float:
    return float(np.hypot(np.cos(headings).mean(), np.sin(headings).mean()))


def run(cfg: BoidsConfig, steps: int, seed: int = 0, measure: bool = False, record_every: int = 0):
    import time
    import moderngl
    ctx = moderngl.create_standalone_context(require=460)
    dep = ctx.compute_shader(_DEPOSIT_SRC)
    upd = ctx.compute_shader(_UPDATE_SRC)
    NA, GW = cfg.n_agents, cfg.grid
    cell = cfg.world / GW
    rng = np.random.default_rng(seed)
    ag = np.empty((NA, 3), dtype=np.float32)
    ag[:, 0] = rng.random(NA) * cfg.world
    ag[:, 1] = rng.random(NA) * cfg.world
    ag[:, 2] = rng.random(NA) * 2 * np.pi
    abuf = ctx.buffer(ag.tobytes())
    gcos = ctx.buffer(reserve=GW*GW*4); gsin = ctx.buffer(reserve=GW*GW*4); gcnt = ctx.buffer(reserve=GW*GW*4)
    for cs in (dep, upd):
        cs["NA"] = NA; cs["GW"] = GW; cs["GH"] = GW; cs["cell"] = cell
    dep["SCALE"] = _SCALE
    upd["v0"] = cfg.v0; upd["noise"] = cfg.noise; upd["W"] = cfg.world; upd["H"] = cfg.world
    gA = (NA + 255) // 256
    order_hist = []

    def read_order():
        h = np.frombuffer(abuf.read(), dtype=np.float32).reshape(NA, 3)[:, 2]
        return _order(h)

    ctx.finish(); t0 = time.time()
    for f in range(steps):
        gcos.clear(); gsin.clear(); gcnt.clear()
        abuf.bind_to_storage_buffer(0); gcos.bind_to_storage_buffer(1)
        gsin.bind_to_storage_buffer(2); gcnt.bind_to_storage_buffer(3)
        dep.run(group_x=gA); ctx.memory_barrier()
        upd["frame"] = f
        upd.run(group_x=gA); ctx.memory_barrier()
        if record_every and (f % record_every == 0 or f == steps - 1):
            order_hist.append((f, read_order()))
    ctx.finish(); dt = time.time() - t0
    ag_out = np.frombuffer(abuf.read(), dtype=np.float32).reshape(NA, 3).copy()
    for b in (abuf, gcos, gsin, gcnt):
        b.release()
    ctx.release()
    out = {"agents": ag_out, "order": _order(ag_out[:, 2]),
           "order_hist": np.array(order_hist, dtype=float), "steps_per_s": steps / dt}
    if measure:
        return out["order"], out["steps_per_s"]
    return out


def order_vs_noise(cfg: BoidsConfig, noises, steps: int = 200, seed: int = 0) -> np.ndarray:
    out = []
    for nz in noises:
        c = BoidsConfig(world=cfg.world, n_agents=cfg.n_agents, grid=cfg.grid, v0=cfg.v0, noise=float(nz))
        out.append(run(c, steps, seed=seed)["order"])
    return np.array(out)
