# alife — progress

## Current state (Round 5 complete — 2026-06-16)

A continuous **two-species ecosystem**: predators and prey live, hunt, flee, breed and
die in one world — and **coexist** rather than one wiping out the other.

### Stack of rounds
- **R1** emergent Boids flocking (φ 0.08→0.92).
- **R2** natural selection — genome/energy/food/reproduction/death (skeptic + replicate verified).
- **R3** evolved NN foraging brains via generational GA (13–22× held-out). `brain/sensors/neuro/evolve.py`.
- **R4** predator–prey co-evolution arms race (de-confounded, both escalate). `coevo.py`.
- **R5** continuous predator–prey ecology with full lifecycles. `predprey.py`.

### R5 — what works (REAL-VERIFIED: eyes on populations + phase plane + living world)
- `predprey.py` — `PredPreyEcosystem`: prey graze plants + flee + breed + die; predators hunt
  prey + breed + starve. Seeded with R4-evolved brains so hunt/flee is real evolved behavior.
  Key stabilizer: **Type-II functional response** (predator digestion `cooldown` caps intake).
- `render.two_species_frame`; `scripts/run_predprey.py` (populations.png, phase_plane.png, mp4).
- 51 tests pass.

**Verified run** (`runs/r5_predprey`, 5000 steps, no extinction):
- Classic dynamics: prey boom (→2000) → **lagged** predator boom (→600) → prey crash → stable
  coexistence (prey ~400–500, predators sustained). Plants oscillate ~150–300.
- Phase trajectory spirals from the boom corner into a stable coexistence point.

### What did NOT work / the honest balance story (recorded — predator-prey is famously finicky)
- Strong predators (big catch radius / high energy-per-catch / fast breeding) → over-predation →
  prey extinct (collapsed at step 106, then 389). Predator-prey is a narrow stability window.
- Stabilizers that worked: **handling-time cooldown** (Type-II), bigger world (spatial refuge),
  abundant fast-regrowing plants (prey recover), low energy-per-catch, fast predator starvation.
- Two real bugs fixed: velocity from wrapped position-diff was wrong (now `_move` returns true
  pre-wrap velocity); `pred_e_max < pred_e_repro` made predator reproduction impossible.
- **Result is stable COEXISTENCE with one boom-bust transient, NOT sustained limit cycles.**
  Sustained cycles need predators uncapped-but-self-limiting — a narrow window that, every variant
  I tried, tipped into prey extinction. Carried to R5-frontier, not faked.

### Next-round seed (R6 — richer brains: memory / recurrence)
Current brains are feedforward (reflex agents — no memory). Give them **recurrence** (a small
CTRNN/GRU hidden state) so behavior can depend on history: pursuit that anticipates, prey that
remember a predator just behind them, area-restricted search. Evolve via the same GA; REAL-VERIFY
that recurrent brains beat feedforward on a task needing memory (e.g. food that must be returned
to a nest, or tracking a target through an occlusion). Reuse evolve.py; add hidden-state carry.

## Frontier
- **Current ceiling:** two species coexist with evolved reflex (feedforward) brains; ecology is
  stable but damped (not cycling), still 2D.
- **Next frontiers (ambition × feasibility):**
  1. Recurrent/memory brains (CTRNN/GRU) → qualitatively new behavior → R6.
  2. Sustained limit cycles (tune the narrow window, or add explicit spatial structure / patchy
     food / predator territoriality) → R6–R7.
  3. Speciation / niches; spatial hashing or C++/numba for N≫2k → R7.
  4. 3D ecosystem (moderngl/raylib) once memory + ecology proven in 2D → R7–R8.
- **Fidelity/stack ladder:** numpy 2D (now) → numba/C++ for big N → recurrent torch brains → 3D.
- **Radical ideas weighed:** Rosenzweig–MacArthur tuning for true limit cycles (R6); jump to 3D
  (deferred — prove memory first); communication/signalling between agents (R7).
