# alife — progress

## Current state (Round 3 complete — 2026-06-16)

Creatures now have **evolved neural-network brains**. From random networks, natural
selection produces competent foragers — generation by generation, no backprop, no
hand-coded rules.

### Stack of rounds
- **R1** emergent Boids flocking + metrics + headless render (φ 0.08→0.92). `boids.py`, `world.py`, `metrics.py`, `render.py`, `sim.py`.
- **R2** evolution by natural selection — genome/energy/food/reproduction/death; directional + stabilizing selection, verified by eyes+data+skeptics+6/6 replicates. `genome.py`, `ecosystem.py`.
- **R3** neural-network brains evolved by a generational GA. `brain.py`, `sensors.py`, `neuro.py`, `evolve.py`.

### R3 — what works (REAL-VERIFIED: eyes on plots/behavior + held-out generalization)
- `brain.py` — tiny MLP (13→8 tanh→2), weights ARE the genome (~130). Batched forward, mutate, clip.
- `sensors.py` — egocentric retina: K=6 angular sectors of nearest-food + nearest-neighbor proximity + own energy = 13 inputs, all relative to heading.
- `neuro.py` — `NeuroEcosystem` (R2 lifecycle, brain-driven movement: turn+thrust), `solo_run` (trace one brain), `forage_assay`. Body params FIXED so only the brain evolves.
- `evolve.py` — generational neuroevolution: batched solo fitness (food foraged) + truncation selection + elitism. `scripts/run_evolve.py`.
- 40 tests pass.

**Verified run** (`runs/r3_evolve`):
- GA fitness: gen0 mean 4.6 → final mean 83.6 (best 101) over 45 generations — clean S-curve.
- Behavior (solo, identical field): random brain eaten=0 align=-0.06 (sits still); evolved eaten=114 align=+0.52 (sweeps the whole map through the food). Decisive visual.
- Held-out generalization (assay seed 9999 ≠ training seeds 1000+g), 3 seeds: evolved forages 13–22× better than random. Real skill, not memorization.

### What did NOT work — the honest pivot (recorded so R4 doesn't repeat it)
- **In-situ continuous-ecosystem selection on brains is too noisy.** Across many regimes
  (dense/sparse, cheap/expensive movement, scarce/abundant food) the assay ratio was
  inconsistent across seeds (0.7×–2.8×): in a crowd, food is grabbed opportunistically by
  whoever is nearest, so reproductive success only weakly tracks individual navigation skill,
  and the population pins at pop_cap which throttles selection. Evolved brains even moved at
  ~2/3 speed (not "sit still"), yet didn't reliably out-forage random ones.
- **Fix = generational GA** with clean solo fitness (no crowding) + truncation selection.
  Robust across all seeds, and literally "一代代进化出行为". The continuous ecosystem is kept
  as the *living-world viewer* (seeded with evolved brains), not as the selector.
- Latent bug fixed: `np.full(n, e_start)` made an int array when e_start was an int → energy
  subtraction cast error. Now `float(e_start)` in both ecosystems.

### Next-round seed (R4 — predator–prey co-evolution)
Two evolving species sharing the world: prey (forage plants, flee) and predators (hunt prey
for energy). Both have evolved NN brains via the GA; fitness couples them — predator fitness =
prey caught, prey fitness = survival/foraging. An evolutionary arms race: faster/smarter prey
↔ better hunters. REAL-VERIFY: co-evolution dynamics (predator/prey population cycles,
behavioral escalation), watch + measure. Reuse brain/sensors/evolve; add a species tag, a
prey-sensing channel for predators, and catch mechanics.

## Frontier
- **Current ceiling:** single-species evolved foraging brains. Behavior = forage. No
  inter-species dynamics, no arms race, still 2D.
- **Next frontiers (ambition × feasibility):**
  1. Predator–prey co-evolution (arms race, Lotka–Volterra cycles) → R4.
  2. Richer brains/senses: recurrent (CTRNN/GRU) memory, vision rays, communication → R4–R5.
  3. Speciation / niches; spatial hashing or C++/numba for N≫1k → R5.
  4. 3D ecosystem (moderngl/raylib) once co-evolution proven in 2D → R5–R6.
- **Fidelity/stack ladder:** numpy 2D (now) → numba/C++ for big N → recurrent torch brains →
  moderngl/3D.
- **Radical ideas weighed:** make in-situ selection work via territory/individual food claims
  (deferred — GA is robust and sufficient); jump to 3D (deferred — prove co-evolution in 2D
  first); RL instead of GA (deferred — GA = truer "natural selection").
