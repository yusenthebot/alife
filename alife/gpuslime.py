"""R55 — a million minds with no brains: GPU Physarum (slime-mold) on the substrate.

Built on R54's GPU compute substrate. A million agents wander a 2D field; each drops
a chemical trail and steers toward stronger trail it senses just ahead (three
sensors: left, centre, right). The field diffuses and decays. No agent senses
another agent directly — they couple only through the shared trail (stigmergy) — yet
the swarm self-organises into the dynamic, branching transport networks of
Physarum polycephalum, the slime mould famous for solving mazes and re-deriving the
Tokyo rail map. Emergent computation from a million memoryless wanderers, running
entirely on the GPU (Jones 2010).

Two compute passes per step: agents sense/steer/move/deposit (atomic), then the
trail field is blurred + decayed. Ping-pong trail buffers, memory_barrier between.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

_AGENT_SRC = """
#version 460
layout(local_size_x = 256) in;
layout(std430, binding = 0) buffer Agents { float ag[]; };   // x, y, heading per agent
layout(std430, binding = 1) buffer Trail  { uint trail[]; };
uniform int W, H, NA, frame;
uniform float speed, sensor_dist, sensor_ang, turn_ang, deposit;
uint ti(int x, int y) { x = (x % W + W) % W; y = (y % H + H) % H; return uint(y * W + x); }
float sense(float x, float y, float a) {
    int sx = int(x + cos(a) * sensor_dist);
    int sy = int(y + sin(a) * sensor_dist);
    return float(trail[ti(sx, sy)]);
}
float hash(uint n) { n = (n << 13) ^ n; n = n * (n * n * 15731u + 789221u) + 1376312589u;
                     return float(n & 0x7fffffffu) / float(0x7fffffff); }
void main() {
    uint i = gl_GlobalInvocationID.x;
    if (i >= uint(NA)) return;
    float x = ag[i*3+0], y = ag[i*3+1], h = ag[i*3+2];
    float fc = sense(x, y, h), fl = sense(x, y, h + sensor_ang), fr = sense(x, y, h - sensor_ang);
    if (fc > fl && fc > fr) {                       // straight
    } else if (fl > fr) { h += turn_ang;            // turn left
    } else if (fr > fl) { h -= turn_ang;            // turn right
    } else { h += (hash(i + uint(frame) * 2654435761u) - 0.5) * 2.0 * turn_ang; }  // random
    x = mod(x + cos(h) * speed, float(W));
    y = mod(y + sin(h) * speed, float(H));
    ag[i*3+0] = x; ag[i*3+1] = y; ag[i*3+2] = h;
    atomicAdd(trail[ti(int(x), int(y))], uint(deposit));
}
"""

_DIFFUSE_SRC = """
#version 460
layout(local_size_x = 16, local_size_y = 16) in;
layout(std430, binding = 0) readonly buffer TIn  { uint tin[]; };
layout(std430, binding = 1) writeonly buffer TOut { uint tout[]; };
uniform int W, H; uniform float decay;
uint ti(int x, int y) { x = (x % W + W) % W; y = (y % H + H) % H; return uint(y * W + x); }
void main() {
    int x = int(gl_GlobalInvocationID.x), y = int(gl_GlobalInvocationID.y);
    if (x >= W || y >= H) return;
    float s = 0.0;
    for (int dy = -1; dy <= 1; dy++)
        for (int dx = -1; dx <= 1; dx++)
            s += float(tin[ti(x+dx, y+dy)]);
    tout[ti(x, y)] = uint((s / 9.0) * decay);       // 3x3 blur then decay
}
"""


@dataclass(frozen=True)
class SlimeConfig:
    width: int = 1024
    height: int = 1024
    n_agents: int = 1_000_000
    speed: float = 1.0
    sensor_dist: float = 9.0
    sensor_ang: float = 0.4       # radians between sensors
    turn_ang: float = 0.35
    deposit: float = 32.0
    decay: float = 0.92


def run(cfg: SlimeConfig, steps: int, seed: int = 0, measure: bool = False, record_every: int = 0):
    import time
    import moderngl
    ctx = moderngl.create_standalone_context(require=460)
    agent_cs = ctx.compute_shader(_AGENT_SRC)
    diff_cs = ctx.compute_shader(_DIFFUSE_SRC)
    W, H, NA = cfg.width, cfg.height, cfg.n_agents

    rng = np.random.default_rng(seed)
    ag = np.empty((NA, 3), dtype=np.float32)
    # seed agents uniformly across the whole field -> a space-filling network forms
    ag[:, 0] = rng.random(NA) * W
    ag[:, 1] = rng.random(NA) * H
    ag[:, 2] = rng.random(NA) * 2 * np.pi
    abuf = ctx.buffer(ag.tobytes())
    ta = ctx.buffer(reserve=W * H * 4); tb = ctx.buffer(reserve=W * H * 4)
    ta.write(np.zeros(W * H, dtype=np.uint32).tobytes())

    for cs in (agent_cs,):
        cs["W"] = W; cs["H"] = H; cs["NA"] = NA; cs["speed"] = cfg.speed
        cs["sensor_dist"] = cfg.sensor_dist; cs["sensor_ang"] = cfg.sensor_ang
        cs["turn_ang"] = cfg.turn_ang; cs["deposit"] = cfg.deposit
    diff_cs["W"] = W; diff_cs["H"] = H; diff_cs["decay"] = cfg.decay

    gA = (NA + 255) // 256
    gx = (W + 15) // 16; gy = (H + 15) // 16
    snaps = {}
    structure = []
    ctx.finish()
    t0 = time.time()
    for f in range(steps):
        agent_cs["frame"] = f
        abuf.bind_to_storage_buffer(0); ta.bind_to_storage_buffer(1)
        agent_cs.run(group_x=gA)
        ctx.memory_barrier()
        ta.bind_to_storage_buffer(0); tb.bind_to_storage_buffer(1)
        diff_cs.run(group_x=gx, group_y=gy)
        ctx.memory_barrier()
        ta, tb = tb, ta
        if record_every and (f % record_every == 0 or f == steps - 1):
            tr = np.frombuffer(ta.read(), dtype=np.uint32).reshape(H, W).astype(np.float32)
            structure.append((f, float(tr.std() / max(tr.mean(), 1e-6))))
            snaps[f] = tr
    ctx.finish()
    dt = time.time() - t0
    trail = np.frombuffer(ta.read(), dtype=np.uint32).reshape(H, W).astype(np.float32)
    for b in (abuf, ta, tb):
        b.release()
    ctx.release()
    out = {"trail": trail, "steps_per_s": steps / dt, "snaps": snaps,
           "structure": np.array(structure, dtype=float)}
    if measure:
        return trail, steps / dt
    if record_every:
        return out
    return trail
