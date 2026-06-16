# alife — progress

## Current state (Round 4 complete — 2026-06-16)

Two species now co-evolve: **predators and prey in an evolutionary arms race.**

### Stack of rounds
- **R1** emergent Boids flocking (φ 0.08→0.92). `boids.py`, `world.py`, `metrics.py`, `render.py`, `sim.py`.
- **R2** natural selection — genome/energy/food/reproduction/death; directional + stabilizing selection (skeptic-verified, 6/6 replicates). `genome.py`, `ecosystem.py`.
- **R3** evolved NN foraging brains via generational GA (fitness 4.6→84; 13–22× held-out). `brain.py`, `sensors.py`, `neuro.py`, `evolve.py`.
- **R4** predator–prey co-evolution (arms race) via co-evolutionary GA. `coevo.py`.

### R4 — what works (REAL-VERIFIED: eyes on arms-race plot + behavior frames)
- `coevo.py` — two brain populations: prey (sense food + predators → forage & flee), predators
  (sense prey → hunt). Shared-arena episode evaluates both; truncation+elitism selection each gen.
  Prey fitness = food + survival; predator fitness = catches + dense **pursuit** reward (closing
  distance) that bootstraps hunting out of the sparse catch signal.
- `render.two_species_frame` — prey (cyan), predators (red, larger), food (green), trails.
- `scripts/run_coevo.py` — arms-race curves + behavior video.
- 44 tests pass.

**Verified run** (`runs/r4_coevo`, 55 generations):
- De-confounded arms race (each species vs the FINAL evolved opponent): predator hunting
  44→170 catches/episode; prey evasion (survival vs final predators) 0.04→0.15. Both escalate
  over generations across 2 seeds; prey curve oscillates = Red Queen.
- Behavior: start frame = cyan prey foraging among food + red predators hunting; predators evolve
  a circling/patrolling search; over a 600-step rollout predators catch all prey (166→0).

### What did NOT work / balance lessons (recorded)
- Predator fitness = catches ONLY is too sparse (catching a fleeing prey is rare) → predators
  don't evolve. Fix = dense **pursuit (closing-distance) reward** + catches.
- Balance is delicate: too-strong predators (big catch radius / speed edge) catch everything →
  prey can't evolve evasion (no survival gradient). Tuned to near-equal speed, prey more agile
  (turn 0.6 vs 0.4), small catch radius 2.8 → both sides have room to escalate.
- "Catches vs NAIVE prey" saturates (naive prey are sitting ducks) → measure skill vs the FINAL
  evolved opponent instead (de-confounded, non-saturating).

### Next-round seed (R5 — predator–prey ECOLOGY: Lotka–Volterra)
Co-evolution gives behavior; R5 gives the iconic ecological dynamics. Build a CONTINUOUS
two-species ecosystem (energy + reproduction + death for BOTH species, seeded with the
R4-evolved brains): prey eat plants & reproduce, predators eat prey & reproduce, predators
starve when prey are scarce → **Lotka–Volterra population cycles** (oscillating predator/prey
counts with phase lag). REAL-VERIFY: population time series shows sustained out-of-phase
oscillation + a phase-plane loop; watch it. Reuse coevo sensing + brain/evolve.

## Frontier
- **Current ceiling:** two species co-evolve behavior (hunt/evade), but episodes are fixed-length
  GA tournaments — no continuous ecology, no population dynamics, still 2D.
- **Next frontiers (ambition × feasibility):**
  1. Lotka–Volterra population cycles (continuous two-species ecology) → R5.
  2. Richer brains: recurrent memory (CTRNN/GRU), vision rays, signalling/communication → R5–R6.
  3. Speciation / niches; spatial hashing or C++/numba for N≫1k → R6.
  4. 3D ecosystem (moderngl/raylib) once ecology + richer brains proven in 2D → R6–R7.
- **Fidelity/stack ladder:** numpy 2D (now) → numba/C++ for big N → recurrent torch brains → 3D.
- **Radical ideas weighed:** Hall-of-Fame co-evolution to curb cyclic forgetting (consider R5);
  3D now (deferred — prove ecology first); RL (deferred — GA = truer natural selection).
