# alife — progress

## Current state (Round 60 — 2026-06-18)

An evolving artificial-life ecosystem built from zero over 60 autonomous rounds. The full stated
goal is realized — **Boids flocking → natural selection → neural-network brains → predator–prey →
energy/reproduction → a 3D ecosystem you watch evolve** — plus deep stretch work: ~10k-creature
scale, atmospheric GPU rendering, a dozen+ classic evolutionary phenomena, an open-endedness
trilogy (R28–R30), evolving morphology (R31), the **capstone (R33): in-situ foraging evolution
(no GA)**, R34 in-situ predator–prey, R35 environmental tracking, R37 the evolution of sex,
R38 spatial reciprocity, and **R39: rock-paper-scissors (local dispersal preserves biodiversity)**.
**281 tests pass.** PUBLISHED: R2–R50 live on public github.com/yusenthebot/alife.

Status: feature-complete and well past the stated goal (genuine diminishing returns on new
capabilities). **First public push is pending CEO approval** — 49 commits are local; `origin` (public
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
| R30 | novelty search — beats objective on a deceptive maze (8/8 vs 2/8; Lehman-Stanley) |
| R31 | evolving morphology — mass-spring virtual creatures evolve a body + gait (dist 14→49; Karl Sims) |
| R32 | milestone review — adversarially verified R28–R31 (all hold); honest R31 gait caveat recorded |
| R33 | capstone — foraging behavior evolves IN SITU (no GA); directedness 0.08→0.33, food-limited pop |
| R34 | in-situ predator–prey — refuge-stabilized coexistence, boom-bust, prey evolve evasion (no GA) |
| R35 | evolution in a changing world — population tracks a flipping food valence (sawtooth re-adaptation) |
| R36 | review — red-team R33/R34/R35 (mutation-off controls), architecture/hygiene audit |
| R37 | evolution of sex — Muller's ratchet: asexual load ratchets up (→73), sex holds balance (~12) |
| R38 | spatial reciprocity — cooperation persists by clustering on a lattice (0.42) vs well-mixed (0) |
| R39 | rock-paper-scissors — local dispersal preserves all 3 species (~0.33) vs well-mixed fixation |
| R40 | review + phenomena-wall poster (R25–R39 montage); README roadmap refreshed; 193 tests green |
| R41 | the Baldwin effect — learning finds & assimilates a needle (Hinton-Nowlan); blind without it |
| R42 | group selection — Simpson's paradox: cooperation up in the whole, down in every group |
| R43 | animation showcase — the in-situ ecosystem as a GIF (watch foraging evolve; the "迷人" goal) |
| R44 | error threshold — Eigen's quasispecies: master sequence collapses above μc≈ln(σ)/L |
| R45 | morphogenesis — Gray-Scott reaction-diffusion: Turing patterns (spots/stripes/waves) |
| R46 | Conway's Game of Life — Gosper gun (unbounded growth) + soup→ash; the CA root of ALife |
| R47 | review — refreshed phenomena gallery (R25–R46, 17 panels); architecture/hygiene; 225 green |
| R48 | Daisyworld — life regulates planetary temperature (Gaia/homeostasis); std 1.7 vs 12.6 bare |
| R49 | evolutionary branching — one lineage splits under disruptive competition (adaptive dynamics) |
| R50 | release-readiness — README tells full R1–R49 story; roadmap to R49; docs-hygiene; 237 green |
| —  | **FIRST PUSH (Yusen approved): R2–R50 published to public github.com/yusenthebot/alife** |
| R51 | Digital Genesis — self-replicating PROGRAMS evolve (Avida/Tierra); a substrate leap (executable genome) |
| R52 | Digital Genesis II — computation PAYS: NAND computer outcompetes copier; de-novo NAND emerges (fragile) |
| R53 | Digital Genesis III — phylogeny: clades rise/fall, 24 lineages coalesce to 1 common ancestor |
| R54 | GPU substrate leap — 1.05M-cell Gray-Scott on compute shaders (GPU=CPU to 1e-7; ~100x faster) |
| R55 | GPU Physarum — 1,000,000 slime-mold agents self-organize into transport networks (stigmergy) |
| R56 | a million boids — GPU Vicsek flocking (order φ→0.98) + phase transition; full-circle to R1 |
| R57 | natural selection at a million-genome scale — GPU tournament evolution finds the global optimum |
| R58 | review — frontier gallery (R51–R57 Digital Genesis + GPU); architecture clean; full suite 272 |
| R59 | local adaptation @1M — GPU spatial evolution: the genetic map evolves to mirror the environment (corr→0.99) |
| R60 | Lenia — continuous-CA creatures self-organize on the GPU (deferred R47, resolved at scale) |

## Honest notes (what did NOT work, recorded so they aren't re-tried blindly)
- **In-situ ecosystem selection on brains (R3 negative — RESOLVED in R33).** R3 found in-situ
  selection too noisy *in a cap-limited, food-dense regime* (population pins at the cap, eating is
  opportunistic, skill stops mattering). R33's capstone (alife/ecosim.py) shows it works once the
  ecology is strictly **energy-limited**: a generous pop cap so food is the real limiter, scarce food,
  movement costs energy, expensive reproduction. Directed foraging then evolves with no GA at all —
  directedness 0.08→0.33, population self-regulates well below the cap, lineages 25 generations deep.
  The R3 negative was about the *regime*, not in-situ selection per se.
- **R31 morphology — locomotion is mostly but not purely gait-driven.** Muscle-ablation (R32 review):
  an evolved creature travels 48.7 with muscles vs 11.6 with muscles zeroed, so ~24% of the distance
  is passive (largely the initial fall/settle, plus some asymmetric-body creep). The gait dominates
  (2nd-half-of-rollout movement of ~26 units can't be passive), but the headline distance is not 100%
  gait. Reported as-is; a cleaner metric would subtract a passive-body baseline.
- **R6 memory (resolved in R26):** evolved recurrence did not beat a memoryless control on the R6
  *foraging* tasks because those tasks didn't *require* memory — reactive policies stayed competitive.
  R26 settles it with a task that provably requires memory (delayed-cue latch, alife/memory_task.py):
  RNN reaches 1.0 held-out, FF is pinned at exactly 0.5 by construction. The R6 negative was about
  the task, not the architecture.
- **Predator–prey balance is a knife-edge** (R5/R10/R14): max predator intake
  (energy_per_catch / handling) must exceed upkeep; predators capped/limited below prey. Stable
  coexistence is easy; sustained cycles needed the R15 refuge-floor mechanism.

## Frontier / next
- **The capstone (R33) ties the project together:** brains + sensing + energy + reproduction +
  in-situ natural selection in one living world, behavior evolving as you watch — the original vision
  realized as ONE system, not a collection of demos. Both big ambition-critic leaps (open-endedness
  R28–R30, morphology R31) and the longest-standing open problem (R3 in-situ selection) are now done.
- Ways to push the capstone further: **(a) put evolved MORPHOLOGY creatures in the living world**
  (body+brain+ecology in one); **(b) in-situ speciation / niches**; **(c) sexual reproduction +
  recombination**. (R34 added in-situ predators — coexistence + prey evasion robust; a clean
  two-sided arms race resisted tuning, see honest note.)
- **R33 red-team nuance (R36):** the in-situ directedness gain is genuine natural selection (a no-mutation
  run still rises by *sorting the initial random brains'* standing variation; R35's tracking, by contrast,
  fully collapses with mutation off — confirming that one needs heritable innovation). Over ~5k steps
  mutation adds little to R33 beyond selecting standing variation (and carries slight load). So R33 is
  honestly "selection acting in situ," with cumulative mutation-driven innovation a smaller effect on
  that horizon. Not an artifact — directedness depends on the energy-based life/death regime.
- **R34 honest note:** in-situ predator–prey coexists robustly via a Huffaker refuge and prey reliably
  evolve evasion, but a clean *two-sided* arms race (pursuit ALSO rising) did not materialize — the
  predator population pins at its cap and prey are abundant, so pursuit selection is weak; predators
  also get pursuit "for free" from a sensor that points at prey. Reported as the data shows it; this
  is the same R5/R10/R14 knife-edge the project has hit before.
- Remaining heavy leap: a **GPU-compute scale jump** (JAX/taichi → 1e5–1e6 agents / faster physics).
  Scripted-phenomenon modules are at deep diminishing returns; the live frontier is the integrated world.
- **R25 note:** pure-zero-start Fisher sits on the unstable equilibrium and does not bootstrap;
  a small seeded preference (the sensory-bias origin of ornaments) is needed to trigger runaway —
  this is the correct theoretical result, not a hack. Per-generation genetic correlation is small
  but persistently positive; the runaway and the dose-response are the robust signatures.
- **Fidelity/stack ladder:** numpy 2D → numpy 3D + moderngl GPU (fog/glow/shadows) → KD-tree scale
  (~10k+) → (future) numba/C++/GPU-compute for far larger N, instanced trails, shadow maps.
- **Decision pending from Yusen:** publish (push) and/or stop the loop.
