# alife — progress

## Current state (Round 29 — 2026-06-17)

An evolving artificial-life ecosystem built from zero over 29 autonomous rounds. The full stated
goal is realized — **Boids flocking → natural selection → neural-network brains → predator–prey →
energy/reproduction → a 3D ecosystem you watch evolve** — plus deep stretch work: ~10k-creature
scale, atmospheric GPU rendering, a dozen+ classic evolutionary phenomena, and an open-endedness
line (R28 MAP-Elites; R29 sensed obstacle-navigation quality-diversity). **140 tests pass.**

Status: feature-complete and well past the stated goal (genuine diminishing returns on new
capabilities). **First public push is pending CEO approval** — 23 commits are local; `origin` (public
`github.com/yusenthebot/alife`) still has only R1. To publish: `git push origin master`.

## The rungs (detail in git log + README)

| | |
|---|---|
| R1 | emergent 2D Boids flocking (order φ 0.08→0.92) |
| R2 | natural selection — genome/energy/food/reproduction/death |
| R3 | evolved NN foraging brains (generational GA; 13–22× held-out) |
| R4 | predator–prey co-evolution (arms race) |
| R5 | continuous predator–prey ecology (2D coexistence) |
| R6 | recurrent brains (honest negative: memory not robustly better) |
| R7 | 3D flocking on the GPU (moderngl, headless on RTX 5080) |
| R8 | evolution in 3D (evolved 3D foragers + food) |
| R9 | predator–prey in 3D (aerial arms race) |
| R10 | continuous self-sustaining 3D living world |
| R11 | renderer beauty pass (fog, graded sky, rim light, shadows, glowing food) |
| R12 | milestone review + QUICKSTART + first-push gate |
| R13 | vast swarms (12k+ via KD-tree spatial index) |
| R14 | large-scale living world (~10.6k creatures, KD-tree ecosystem) |
| R15 | sustained predator–prey limit cycles (Huffaker refuge floor) |
| R16 | sympatric speciation (one species → two) |
| R17 | evolution of communication (Lewis signalling game) |
| R18 | evolution of evolvability (self-adaptive mutation rate) |
| R19 | evolution of cooperation (Hamilton's rule) |
| R20 | evolution of aging (Medawar/Williams) |
| R21 | a major transition: multicellularity (predation-driven) |
| R22 | Red Queen host–parasite coevolution |
| R23 | the gallery — every rung's headline frame in one journey poster |
| R24 | docs-hygiene (trimmed progress.md to current-state; no new capability) |
| R25 | sexual selection — Fisherian runaway (costly ornament dragged past survival optimum) |
| R26 | the memory win — RNN beats reactive brain on a provably memory-requiring task (R6 rematch) |
| R27 | milestone review — adversarial verify R25/R26, refresh README, ambition critic |
| R28 | open-endedness — MAP-Elites illuminates a behavior space (100% vs 16% objective-only) |
| R29 | open-ended navigation — sensed obstacle field; QD discovers routes around walls (103% vs 25%) |

## Honest notes (what did NOT work, recorded so they aren't re-tried blindly)
- **In-situ ecosystem selection on brains is too noisy** (crowding dilutes the skill signal) →
  evolve brains with a **generational GA**; keep the continuous ecosystem as the living-world viewer.
- **R6 memory (resolved in R26):** evolved recurrence did not beat a memoryless control on the R6
  *foraging* tasks because those tasks didn't *require* memory — reactive policies stayed competitive.
  R26 settles it with a task that provably requires memory (delayed-cue latch, alife/memory_task.py):
  RNN reaches 1.0 held-out, FF is pinned at exactly 0.5 by construction. The R6 negative was about
  the task, not the architecture.
- **Predator–prey balance is a knife-edge** (R5/R10/R14): max predator intake
  (energy_per_catch / handling) must exceed upkeep; predators capped/limited below prey. Stable
  coexistence is easy; sustained cycles needed the R15 refuge-floor mechanism.

## Frontier / next
- **Open-endedness line** (the live frontier): R28 illuminated movement styles in open space; R29
  added a sensed obstacle field so QD must discover navigation routes (coverage takes the obstacle's
  shape; efficiency map shows detour shadows behind walls). Natural next steps: **(a) novelty search**
  as an alternative driver (no objective at all); **(b) QD on the 3D foragers / living world**
  (illuminate foraging strategies, not just locomotion); **(c) CPPN/indirect encoding** for richer
  controllers; **(d) co-evolving obstacle layouts** (open-ended environment, not just behavior).
- Other heavy leaps still open: **evolving morphology** (Karl Sims: co-evolve body+brain), a
  **GPU-compute scale jump** (JAX/taichi → 1e5–1e6 agents). Small scripted-phenomenon modules are at
  deep diminishing returns; open-endedness and morphology are the real ambition horizon now.
- **R25 note:** pure-zero-start Fisher sits on the unstable equilibrium and does not bootstrap;
  a small seeded preference (the sensory-bias origin of ornaments) is needed to trigger runaway —
  this is the correct theoretical result, not a hack. Per-generation genetic correlation is small
  but persistently positive; the runaway and the dose-response are the robust signatures.
- **Fidelity/stack ladder:** numpy 2D → numpy 3D + moderngl GPU (fog/glow/shadows) → KD-tree scale
  (~10k+) → (future) numba/C++/GPU-compute for far larger N, instanced trails, shadow maps.
- **Decision pending from Yusen:** publish (push) and/or stop the loop.
