# alife — progress

## Current state (Round 10 complete — 2026-06-17)

**A continuous, self-sustaining 3D living world.** Two evolved-brain species — prey and
predators — live, hunt, flee, graze, breed and die in a 3D volume, and the world runs
indefinitely without collapse. The full vision ("一个能看着它一代代进化出行为的 3D 生态") is now
a single runnable artifact.

### Stack of rounds
- **R1** 2D flocking · **R2** selection · **R3** evolved 2D foraging brains · **R4** predator–prey
  co-evolution · **R5** predator–prey ecology · **R6** recurrent brains (honest negative) ·
  **R7** 3D flocking (GPU) · **R8** evolution in 3D · **R9** predator–prey in 3D.
- **R10** continuous 3D ecology. `predprey3d.py`.

### R10 — what works (REAL-VERIFIED: GPU 3D frames + population data)
- `predprey3d.py` — `PredPrey3DEcosystem`: R5's continuous lifecycle (energy · grazing · catching
  with Type-II digestion cooldown · energy-split reproduction with mutation · starvation/age death)
  on the 3D substrate (coevo3d body-frame sensing + 3D acceleration). Seeded with R9-evolved 3D
  hunt/flee brains so behavior is competent from tick 0.
- `scripts/run_predprey3d.py`; 4 new tests (79 total) pass.

**Verified run** (`runs/r10_world3d`, 4000 steps, NO extinction):
- Prey 315 → 1500 (carrying cap), predators 22 → 320 (gradual rise, then hold), food fluctuating
  ~100–200. Stable coexistence over the whole run.
- Frames: a dense cyan prey swarm filling the volume, red predators interspersed and hunting,
  green food motes — a busy, alive 3D world under a slowly orbiting camera.

### What worked / the balance story (the R5 knife-edge, again)
- Predator–prey balance is a narrow window (3 tuning passes): R9-evolved predators are lethal →
  first config over-predated (prey extinct ~865); over-weakening starved the predators (extinct
  ~577). Stable config: **max intake (energy_per_catch / handling) must exceed predator upkeep**,
  predators capped below prey, prey breed fast with abundant food. Carried directly from R5's lessons.
- Result is **stable coexistence (both near carrying caps)**, not sustained Lotka–Volterra cycles —
  same honest outcome as R5; food is the only freely-fluctuating variable. Recorded, not faked.

### Next-round seed (R11 — beauty pass, OR unify into one showcase)
The full arc + a self-sustaining 3D world are done. Highest-value next steps:
1. **Beauty pass** (the goal's "画面迷人"): shadows, glowing/bloomed food, motion trails, nicer
   camera, prettier creature meshes — make the 3D world genuinely mesmerizing to watch.
2. **Unified showcase**: a single `run_alife.py` / README gallery tying R1→R10 into one story with
   regenerated headline artifacts; tidy/dedupe; consider first `git push` (CEO gate — needs summary).
3. **Sustained cycles / food-limited dynamics**: let prey be food-limited below cap for livelier
   population dynamics (carefully, to avoid the collapse knife-edge).
Lean R11 = beauty pass (trails + glow + shadows) — biggest visual payoff per effort.

## Frontier
- **Current ceiling:** complete 2D→3D evolutionary stack + a self-sustaining 3D world; visuals are
  clean but basic (flat-lit cones, point food); populations cap-bound (not cycling).
- **Next frontiers (ambition × feasibility):**
  1. Beauty pass: trails, bloom/glow, soft shadows, depth fog, better meshes → R11.
  2. Livelier dynamics: food-limited prey / sustained cycles in 3D → R11–R12.
  3. Scale (numba/C++/GPU-compute for N≫2k); speciation; earn the memory win (R6).
  4. Unify + polish + first public push (CEO gate).
- **Fidelity/stack ladder:** numpy 3D + moderngl GPU (now) → instanced trails + shadow maps + bloom
  → numba/C++/GPU-compute for huge N.
- **Radical ideas weighed:** one always-on continuous world combining flocking + foraging + predation
  + reproduction as the ultimate watchable artifact; real creature meshes; post-processing bloom.
