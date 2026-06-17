# alife — progress

## Current state (Round 11 complete — 2026-06-17)

**Beauty pass.** The 3D world is now genuinely atmospheric — the goal's "画面迷人". Every 3D scene
(flocking, foraging, predator–prey, the living world) gets it for free, since it's all one renderer.

### Stack of rounds
- **R1–R6** 2D: flocking · selection · evolved foraging brains · predator–prey co-evolution ·
  predator–prey ecology · recurrent brains (honest negative).
- **R7** 3D flocking (GPU) · **R8** evolution in 3D · **R9** predator–prey in 3D ·
  **R10** continuous self-sustaining 3D living world.
- **R11** GPU renderer beauty pass. `render3d.py`.

### R11 — what works (REAL-VERIFIED: eyes on rendered frames)
- `render3d.py` beauty upgrade (API unchanged — every 3D script benefits):
  - **Depth fog** → atmospheric perspective; distant creatures and the arena fade into the sky.
  - **Graded sky** background (fullscreen quad) instead of flat black.
  - **Key + fill + rim lighting** on creatures → dimensional, glowing edges.
  - **Soft ground shadows** (projected, blended) → spatial grounding.
  - **Glowing additive food** (halo + core) → food reads as luminous motes.
- 79 tests pass (render test confirms the new shaders; sim logic untouched).

**Verified** (`runs/r11_world3d`, `runs/beauty_test.png`): the living 3D world now has atmospheric
depth — a dense cyan prey swarm + red predators fading into fog under a graded sky, glowing food.
Clearly more captivating than the flat R7–R10 look.

### What worked / notes
- All effects are camera-orbit-safe (per-frame shader passes, no frame accumulation) — robust for
  the screenshot-verify discipline. Motion trails were considered but skipped (incompatible with an
  orbiting camera; would smear the static arena). A fixed-camera trail showcase is a future option.
- moderngl passes: sky quad (depth off) → fogged lines → blended ground shadows (depth-mask off) →
  lit opaque creatures → additive glowing food (depth-mask off).

### Next-round seed (R12 — unify + polish + first public release)
The whole vision is built and now looks good. Strong R12 options:
1. **Unified showcase + docs polish**: a `QUICKSTART.md` / gallery tying R1→R11 together, regenerate
   headline artifacts, de-sloppify, ensure root ≤3 doc files. Then **first `git push`** to GitHub
   (origin still only has R1) — a CEO gate (needs an executive summary before pushing).
2. **Livelier dynamics**: food-limited prey / sustained 3D cycles (carefully, past the knife-edge).
3. **Scale**: spatial hashing / numba for much larger swarms (then the 3D vistas get truly dense).
Lean R12 = unify + polish + present the first-push executive summary (the natural milestone), since
the core arc is complete and a public release is the obvious next gate.

## Frontier
- **Current ceiling:** complete 2D→3D evolutionary stack + self-sustaining 3D world + atmospheric
  rendering. Remaining: it's never been pushed public (origin = R1 only); populations cap-bound;
  swarms limited to ~2k by O(N²) numpy.
- **Next frontiers (ambition × feasibility):**
  1. Unify + polish + first public push (CEO gate) → R12.
  2. Livelier dynamics (food-limited / cycles); bigger swarms (numba/C++/GPU-compute).
  3. Earn the memory win (R6 carryover); speciation; communication; real creature meshes.
- **Fidelity/stack ladder:** numpy 3D + moderngl GPU w/ fog+glow+shadows (now) → instanced trails +
  shadow maps → numba/C++/GPU-compute for huge N.
- **Radical ideas weighed:** fixed-camera motion-trail showcase; post-process bloom; one always-on
  combined world (flock + forage + predate + breed) as the definitive watchable artifact.
