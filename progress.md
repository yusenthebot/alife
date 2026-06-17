# alife — progress

## Current state (Round 8 complete — 2026-06-17)

**Evolution now happens in 3D.** Random 3D neural brains evolve into competent 3D foragers, and
the evolved swarm is flown through the GPU renderer as a living 3D ecosystem with food. The two
biggest threads of the project — *evolved intelligence* and *3D* — are now joined.

### Stack of rounds
- **R1** 2D flocking. **R2** natural selection. **R3** evolved 2D NN foraging brains.
  **R4** predator–prey co-evolution. **R5** predator–prey ecology. **R6** recurrent brains
  (honest negative). **R7** 3D flocking on the GPU.
- **R8** evolution lifted into 3D: `evolve3d.py` (3D sensors + 3D forage GA + shared-world rollout).

### R8 — what works (REAL-VERIFIED: GPU 3D frames + held-out data)
- `evolve3d.py` — body-frame 3D sensing (nearest food as left/right · up/down · ahead/behind ×
  proximity, + energy → 5 inputs) → MLP → 3D body-frame acceleration (3 outputs). Generational GA
  (truncation + elitism). `rollout3d_shared` runs the evolved swarm in one shared 3D world.
- `render3d.py` — added GPU food rendering (round green points).
- `scripts/run_evolve3d.py`; 5 new tests (71 total) pass.

**Verified run** (`runs/r8_evolve3d`, 45 generations, 320-agent rollout):
- 3D foraging fitness **0.9 → 49**; held-out (unseen food field) random **0.5** → evolved **52.6**
  (~100×, robust across 2 seeds — random 3D brains are hopeless, evolved are competent).
- Frames: evolved forager cones distributed through the 3D volume, hued by heading, clustered on
  green food points — visibly foraging in 3D under an orbiting camera.

### What worked / notes
- The R3 generational GA transfers cleanly to 3D — body-frame sensing + body-frame acceleration is
  a learnable, rotation-invariant control. 3D advantage is even larger than 2D (random baseline ≈0).
- moderngl point rendering (PROGRAM_POINT_SIZE + round-point discard in the fragment shader) for food.

### Next-round seed (R9 — predator–prey in 3D, OR full 3D living ecosystem)
Two strong options:
1. **Predator–prey in 3D** (R4/R5 → 3D): two species, aerial pursuit/evasion + co-evolution arms
   race in the volume, rendered with the GPU renderer (prey cyan, predators red). The most dramatic
   3D spectacle. Reuse coevo's structure + evolve3d's 3D sensing/movement.
2. **Full continuous 3D ecosystem** (R5 → 3D): energy + reproduction + death in 3D for foragers
   (and predators), Lotka–Volterra-style dynamics in the volume.
Lean R9 = predator–prey in 3D (visual drama + co-evolution, building on R4 + R8).

## Frontier
- **Current ceiling:** 3D flocking + 3D evolved foraging on GPU; predator–prey still 2D.
- **Next frontiers (ambition × feasibility):**
  1. Predator–prey in 3D (aerial arms race) → R9.
  2. Continuous 3D ecology (energy/repro/death in volume) → R9–R10.
  3. Prettier rendering: shadows, glowing food, motion trails, bloom; bigger swarms (numba/C++) → ongoing.
  4. Earn the memory win (R6 carryover); speciation.
- **Fidelity/stack ladder:** numpy 3D + moderngl GPU (now) → numba/C++ for scale → shadows/trails for beauty.
- **Radical ideas weighed:** GPU-compute the sim for huge N; real creature meshes; 3D recurrent
  brains for aerial pursuit memory.
