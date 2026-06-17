# alife — progress

## Current state (Round 9 complete — 2026-06-17)

**Predator and prey now co-evolve in 3D** — an aerial arms race, GPU-rendered. The ecosystem's
hardest dynamic (two species shaping each other) joins the 3D summit.

### Stack of rounds
- **R1** 2D flocking · **R2** selection · **R3** evolved 2D foraging brains · **R4** predator–prey
  co-evolution · **R5** predator–prey ecology · **R6** recurrent brains (honest negative) ·
  **R7** 3D flocking (GPU) · **R8** evolution in 3D.
- **R9** predator–prey co-evolution in 3D. `coevo3d.py`.

### R9 — what works (REAL-VERIFIED: GPU 3D frames + de-confounded arms-race data)
- `coevo3d.py` — two brain populations in a 3D volume: prey sense food + predators (body-frame)
  and flee/forage; predators sense prey and pursue in 3D. Body-frame sensing + 3D acceleration
  (from R8), R4's co-evolution structure (dense pursuit reward, vs-final-opponent metric, prey
  more agile than predators). `episode3d(record=True)` rolls out for rendering.
- Render: prey (cyan) + predators (red) + food (green points) drawn together via `render3d`.
- `scripts/run_coevo3d.py`; 4 new tests (75 total) pass.

**Verified run** (`runs/r9_coevo3d`, 55 generations):
- De-confounded arms race (each species vs the FINAL evolved opponent): predator hunting
  4 → 164 catches; prey evasion (survival) 0.08 → 0.18. Both escalate (also confirmed at a 2nd
  seed: 10 → 154 / 0.08 → 0.22). Predators win the balance — a legitimate Red-Queen outcome.
- Frames: cyan prey foraging green food + red predators hunting through the 3D volume; over a
  600-step rollout predators catch all prey (166 → 0).

### What worked / notes
- R4's co-evolution lessons transferred to 3D intact: catches-only fitness is too sparse (kept the
  dense pursuit reward); naive-opponent metrics saturate (measure vs the final evolved opponent).
- Rendering two species = concatenate prey+predator arrays with per-agent colors into one
  `render3d.render` call (uniform scale; red vs cyan distinguishes them).

### Next-round seed (R10 — choose the next ambition)
The full arc (Boids → selection → NN brains → predator-prey → 3D) is now realized end-to-end.
Strong options for R10:
1. **Continuous 3D ecology** (R5 → 3D): energy + reproduction + death in the volume → Lotka–Volterra
   population dynamics in 3D (a self-sustaining living 3D world, not fixed-population episodes).
2. **Beauty pass**: shadows, glowing food, motion trails, bloom, bigger swarms — make the 3D
   visuals truly mesmerizing (the goal's "画面迷人").
3. **Unified showcase**: one `run_alife.py` that renders the whole evolved 3D ecosystem (foragers +
   predators + food + reproduction) as a single continuous, watchable world.
Lean R10 = continuous 3D ecology (self-sustaining 3D living world) — the natural capstone.

## Frontier
- **Current ceiling:** flocking, evolved foraging, and predator–prey co-evolution all in 3D on GPU;
  but 3D runs are fixed-population GA episodes, not a continuous self-sustaining living world.
- **Next frontiers (ambition × feasibility):**
  1. Continuous 3D ecology (energy/repro/death in volume) → self-sustaining 3D world → R10.
  2. Beauty pass (shadows/trails/bloom/glowing food); larger swarms (numba/C++) → R10–R11.
  3. Earn the memory win (R6 carryover); speciation; communication.
- **Fidelity/stack ladder:** numpy 3D + moderngl GPU (now) → numba/C++ for scale → shadows/trails.
- **Radical ideas weighed:** GPU-compute the sim for huge N; real creature meshes; a single
  always-on continuous 3D world combining every species (the ultimate "watch it evolve" artifact).
