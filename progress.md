# alife — progress

## Current state (Round 20 — evolution of aging — 2026-06-17)

**Senescence evolves (Medawar/Williams).** `aging.py`: age-specific intrinsic survival evolves under
mutation pressure + declining force of selection with age. Survival stays high young and collapses
old (senescence), and the collapse comes EARLIER under higher extrinsic mortality (onset age 15 at
m=0.05 → 9 at m=0.35) — Williams' prediction. 104 tests pass. **Push gate still pending** Yusen's
approval (20 local commits; origin=R1).

### Round 19 — evolution of cooperation
`cooperation.py`: a donation game with tunable assortment; cooperation switches on right at the
Hamilton threshold (assortment = c/b), ~0.1 below to ~0.88 above. Altruism by Hamilton's rule.

### Round 18 — evolution of evolvability
`evolvability.py` ((μ,λ)-ES self-adaptation): mutation rate collapses to the floor in a static
environment (fitness 1.0) but stays high under a moving optimum (~0.21) — a ~100× divergence.

### Round 17 — evolution of communication
`signals.py` (Lewis signalling game): random sender/receiver maps evolve a shared convention —
success 0.25→0.92, mutual info 0→~1.7 bits, evolved code is a permutation. Signals acquire meaning.

### Round 16 — speciation
`speciation.py`: frequency-dependent disruptive selection + assortative mating splits one population
into two stable species (2 species 4/4 seeds, BC 0.96); random-mating control stays one species.

### Round 15 — sustained cycles
`cycles.py`: a Huffaker **prey refuge floor** + food-limited prey + uncapped Type-II predators yield
genuine predator-prey limit cycles (5+ boom-bust cycles/7000 steps, phase-plane loop) — resolving
the R5/R10 stable-coexistence gap.

### Round 14 — the large-scale living world
A KD-tree-accelerated continuous ecosystem (`bigworld3d.py`) puts ~10,600 evolved-brain creatures
into ONE 3D volume at ~20 ms/step (2200 steps, no extinction). Ecology + atmosphere + scale.

### Round 13 — vast swarms
A KD-tree spatial index breaks the O(N²) ceiling: 12,000+ creatures flock in 3D (~146 ms/step),
multiple coherent sub-flocks. `swarm3d.py` (scipy cKDTree). order 0.005 → 0.65.

### Round 12 — milestone review + first-push gate
Health-checked (tests green), hygiene-checked (no slop/secrets; root docs = README + QUICKSTART +
state), added `QUICKSTART.md`, reached the first public-push CEO gate. Push awaits approval; loop
continues frontier work meanwhile.

### Round 11 — Beauty pass
The 3D world is now genuinely atmospheric — the goal's "画面迷人". Every 3D scene
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
