# alife — progress

## Current state (Round 7 complete — 2026-06-17)

**The pivot to 3D succeeded.** Flocking now happens in a real 3D arena, rendered on the GPU —
the project's stated visual summit ("一个能看着它一代代进化出行为的 3D 生态") is reached for the
foundational behavior; the rest of the stack gets lifted into 3D in following rounds.

### Stack of rounds
- **R1** emergent 2D Boids flocking. **R2** natural selection. **R3** evolved NN foraging brains
  (generational GA). **R4** predator–prey co-evolution. **R5** continuous predator–prey ecology.
  **R6** recurrent brains (honest negative: memory not robustly better).
- **R7** 3D flocking on the GPU. `world3d.py`, `boids3d.py`, `render3d.py` (moderngl).

### R7 — what works (REAL-VERIFIED: eyes on GPU-rendered 3D frames + data)
- `world3d.py` — bounded 3D box with boundary-push steering (keeps the flock whole and on-camera).
- `boids3d.py` — vectorized 3D Reynolds Boids (sep/ali/coh in 3D) + boundary avoidance.
- `render3d.py` — **moderngl offscreen GPU renderer**: perspective orbiting camera, lit instanced
  3D cones oriented along velocity, ground grid + wireframe arena, depth test. Standalone GL
  context works headless on the RTX 5080.
- `scripts/run_boids3d.py`; 8 new tests (66 total) pass, incl. a GPU render smoke test.

**Verified run** (`runs/r7_flock3d`, 900 boids × 600 steps):
- 3D order parameter **0.045 → 0.936** — flocking emerges in 3D.
- Frames: start = scattered rainbow cloud of random-oriented cones; end = one cohesive flock,
  cones aligned and moving together, viewed through an orbiting camera. Clearly 3D, mesmerizing.

### What worked / notes
- moderngl `create_standalone_context()` renders headless on the GPU — no display needed, so the
  screenshot-verify discipline holds for 3D. (matplotlib was broken; the venv + moderngl path is clean.)
- Matrix math hand-rolled in numpy (perspective / look_at), uploaded transposed (GL column-major);
  `look_at` guards the view-parallel-to-up degenerate case.
- Bounded box (not toroidal) for 3D so the flock doesn't teleport across wrap seams on camera.

### Next-round seed (R8 — lift EVOLUTION into 3D)
3D rendering + 3D flocking are proven. Next: carry the evolutionary stack into 3D —
3D genome/energy/food/reproduction/death (R2 in 3D) and/or evolved 3D foraging brains (R3 in 3D,
sensors over 3D angular sectors / spherical bins). Render the evolving 3D ecosystem with the new
GPU renderer (color by trait/energy). REAL-VERIFY: watch selection in the 3D world + the data.
Reuse render3d.py (add food spheres + per-agent color); generalize sensors to 3D.

## Frontier
- **Current ceiling:** 3D flocking on GPU; the evolution/brains/ecology stack is still 2D.
- **Next frontiers (ambition × feasibility):**
  1. Lift evolution + foraging brains into 3D (3D sensors, 3D ecosystem) → R8.
  2. Lift predator–prey into 3D (3D pursuit/evasion, aerial hunting) → R9.
  3. Prettier GPU rendering: shadows, food as glowing spheres, trails, bloom → ongoing.
  4. Scale: spatial hashing / numba / C++ for N≫2k; speciation. Earn the memory win (R6 carryover).
- **Fidelity/stack ladder:** numpy 2D → numpy 3D + moderngl GPU (now) → numba/C++ for scale →
  shadows/instanced trails for beauty.
- **Radical ideas weighed:** full 3D sensors via spherical harmonics or ray casts (R8); GPU compute
  for the sim itself (later, if N grows); import real 3D creature meshes (polish).
