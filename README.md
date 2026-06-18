# alife — an evolving artificial-life ecosystem

Watch a pool of simple creatures go from blind flocking to evolved "intelligence",
one generation at a time. The floor is the simplest possible swarm; there is no
ceiling — the project escalates through genetic selection, neural-network brains,
predator–prey dynamics, energy and reproduction, toward a 3D ecosystem you can
watch evolve behavior on its own.

This repository is built in autonomous **evolving rounds**: each round clears the
current bar, then researches the frontier and raises it. Every round is *really*
run — frames rendered, screenshots inspected, metrics plotted — never faked.

## Current state — Round 69: a full artificial-life ecosystem and a tour of the field's great ideas

The pool has climbed sixty-nine rungs, each really run and verified by eye + data.
The original goal is long met — flocking → selection → neural-network brains →
predator–prey → energy/reproduction → a 3D ecosystem you watch evolve — and the
project has gone well past it across several arcs:

- **Evolution & open-endedness** (R1–R49): an open-endedness trilogy (quality-diversity,
  novelty search), evolving morphology (virtual creatures), a **capstone** where foraging
  behaviour evolves *in situ* in one living world with no GA, and a dozen-plus classic
  phenomena (speciation, communication, aging, cooperation, sexual selection, Muller's
  ratchet, group selection, the Baldwin effect, Daisyworld, …).
- **Digital Genesis** (R51–R53): self-replicating *programs* evolve in an Avida-style VM —
  executable genomes, computation that pays, a tree of life.
- **GPU substrate** (R54–R60): 1M-agent worlds on compute shaders — Gray-Scott, Physarum,
  Vicsek flocking, megascale evolution, local adaptation, Lenia — all correctness-gated.
- **The field's great ideas** (R61–R69): Particle Life, autocatalytic sets (origin of
  metabolism), hypercycles, L-system development, ant-colony stigmergy, the edge of chaos,
  evolving cellular automata to compute, Physarum transport networks, and Hopfield memory.

The early rungs are narrated below; the full ladder is the checklist further down.
**344 tests pass.** Every figure is reproducible from `scripts/`.

- **R1 — emergent flocking.** Vectorized Reynolds Boids; collective order emerges
  with no leader (order parameter φ 0.08 → 0.92).
- **R2 — natural selection.** Genome + energy + feeding + reproduction + death.
  From random genomes, traits are selected: food-attraction ↑, metabolism ↓,
  cohesion ↓ (flocking turns out to be costly under food competition). Confirmed
  by adversarial skeptics + 6/6-seed replicates; a neutral trait stays flat as a
  drift control.
- **R3 — evolved brains.** Each creature is driven by a small neural network whose
  weights are its genome. A generational GA (fitness = food foraged) turns random
  networks into competent foragers: mean fitness 4.6 → 84 over 45 generations, and
  on a **held-out** food field evolved brains forage **13–22× better than random**.
  A random brain sits still and eats 0; an evolved brain sweeps the whole map and
  eats 114 — pure evolved weights, no hand-coded rules.

- **R4 — predator–prey co-evolution.** Two brain populations evolve at once: prey
  forage and flee, predators hunt. Measured against the *final* evolved opponent
  (de-confounded), both escalate over generations — predator catches 44 → 170,
  prey survival 0.04 → 0.15 (Red-Queen oscillation). Predators even evolve a
  circling search; prey learn to juke.

- **R5 — predator–prey ecology.** A continuous two-species world with full
  lifecycles (energy, reproduction, death) seeded with the evolved brains. The
  classic dynamics emerge: prey boom → *lagged* predator boom → prey crash →
  stable coexistence (5000 steps, no extinction). A Type-II functional response
  (predator digestion cooldown) is the key stabilizer.

- **R6 — recurrent (memory) brains + an honest test.** Added brains with a
  persistent hidden state and a controlled comparison framework (identical
  architecture; only difference = whether memory persists). The finding, reported
  as-is: across two memory tasks (occluded foraging; central-place/nest foraging)
  evolved memory did **not** robustly beat the memoryless control — reactive
  "sweep" strategies stay competitive and the small GA rarely discovers genuine
  memory use. A real, known frontier difficulty, not a faked win.

- **R7 — 3D, on the GPU.** Flocking lifted into a real 3D arena and rendered with
  moderngl (offscreen, on the RTX 5080): a perspective orbiting camera, lit
  instanced 3D cones, a ground grid and wireframe box. Order parameter 0.045 →
  0.936 — a 3D murmuration consolidating from a random cloud. The project's stated
  visual summit, reached for the foundational behavior; the rest of the stack
  lifts into 3D next.
- **R8 — evolution in 3D.** R3's generational GA lifted into the volume: body-frame
  3D sensing → MLP → 3D acceleration. Random 3D brains forage hopelessly (≈0.5
  food); evolved ones reach ≈52 on a held-out field (~100×). The evolved swarm
  flies through the GPU renderer chasing green food — a living 3D ecosystem.
- **R9 — predator–prey in 3D.** R4's co-evolution on R8's 3D substrate: prey forage
  and flee, predators pursue, all in the volume. Vs the final evolved opponent,
  predator hunting climbs 4 → 164 and prey evasion 0.08 → 0.18 — an aerial arms
  race, rendered with cyan prey, red predators and green food.
- **R10 — a self-sustaining 3D world.** R5's continuous lifecycle (energy,
  reproduction, death, Type-II digestion) on the 3D substrate, seeded with the
  evolved hunt/flee brains. It runs 4000+ steps with no extinction: prey and
  predators coexist (≈1500 / ≈320), breeding and dying in the volume — the whole
  vision as one living, watchable 3D artifact.
- **R11 — beauty pass.** The GPU renderer gains atmospheric depth fog, a graded
  sky, key+fill+rim lighting, soft ground shadows and glowing additive food —
  every 3D scene now reads as an atmospheric, living world (the goal's "画面迷人").
- **R13 — vast swarms.** A KD-tree spatial index breaks the O(N²) neighbor
  ceiling: 12,000+ creatures flock in 3D (~146 ms/step), self-organizing into
  many coherent sub-flocks — a dense, atmospheric murmuration at scale.
- **R14 — the large-scale living world.** A KD-tree-accelerated continuous
  ecosystem puts **~10,600 evolved-brain creatures** (thousands of prey +
  predators + food) into one 3D volume — hunting, fleeing, grazing, breeding and
  dying at ~20 ms/step, stable over 2200+ steps. The definitive artifact:
  ecology (R10) + atmosphere (R11) + scale (R13) in one watchable world.
- **R15 — sustained cycles.** The one recurring gap, closed: a prey **refuge
  floor** (Huffaker) + food-limited prey + uncapped Type-II predators yield
  genuine predator–prey *limit cycles* — 5+ boom-bust cycles over 7000 steps, a
  closed phase-plane loop instead of R5/R10's spiral-to-a-point.
- **R16 — speciation.** Frequency-dependent disruptive selection + assortative
  mating splits one population into **two stable species** (diet≈0 and diet≈1, in
  4/4 seeds); the random-mating control stays a single species — reproductive
  isolation is what makes speciation.
- **R17 — evolution of communication.** A Lewis signalling game: from random
  sender/receiver maps, selection evolves a shared convention — success climbs
  from chance (0.25) to ~0.92, mutual information I(state;signal) from 0 to ~1.7
  bits, and the evolved code is a near-perfect permutation. Signals acquire meaning.
- **R18 — evolution of evolvability.** The mutation rate is itself heritable
  ((μ,λ)-ES self-adaptation): it collapses to the floor in a static environment
  (fitness 1.0) but stays high under a moving optimum (~0.21) to keep tracking —
  a ~100× divergence. Evolvability is an evolved property.
- **R19 — evolution of cooperation.** A donation game with tunable assortment:
  cooperation switches on exactly at the Hamilton threshold (assortment = c/b) —
  flat ~0.1 below it, ~0.88 above. Altruism evolves by Hamilton's rule.
- **R20 — evolution of aging.** Age-specific survival evolves under the declining
  force of selection with age: senescence emerges (survival high young, collapsing
  old), and sets in *earlier* under higher extrinsic mortality (onset age 15→9) —
  Medawar/Williams, demonstrated.
- **R21 — a major transition: multicellularity.** With a size-selective predator
  (and a cost of bigness), cells evolve to cluster — reaching ~7 cells, clearing
  the predator's size threshold; without it they stay unicellular. Predation-driven
  multicellularity, an evolutionary major transition.
- **R22 — Red Queen coevolution.** Matching-allele host–parasite dynamics: common
  host types are hunted by their matching parasite, so allele frequencies oscillate
  forever (never converging) with parasites lagging hosts by ~45 generations.

> Honest notes: (1) in-situ selection on brains proved too noisy, so R3/R4
> selection is a generational GA, with the continuous ecosystem as the
> living-world viewer seeded with evolved brains. (2) R5 reaches stable
> coexistence with one boom-bust transient; **sustained limit cycles arrived in
> R15** via a prey refuge floor. (3) R6's memory advantage is not
> robust — documented honestly as a frontier challenge. None of these are faked.

## Layout

```
alife/
  world.py     toroidal/bounded space: wrap, minimum-image, cross-set distance
  boids.py     vectorized Reynolds step (R1)
  metrics.py   order parameter, milling, packing, cluster count
  render.py    headless Pillow renderer: heading/trait-hued agents + food + trails
  sim.py       Boids simulation driver
  genome.py    heritable traits + mutation (R2)
  ecosystem.py energy / feeding / reproduction / death / selection (R2)
  brain.py     MLP whose weights are the genome (R3)
  sensors.py   egocentric angular food/neighbor senses (R3)
  neuro.py     brain-driven ecosystem + solo foraging assay (R3)
  evolve.py    generational neuroevolution GA (R3)
  coevo.py     predator–prey co-evolutionary GA + arms-race analysis (R4)
  predprey.py  continuous two-species ecosystem (energy/repro/death) (R5)
  memory.py    recurrent brains + occluded/nest memory tasks (R6)
  world3d.py boids3d.py render3d.py  3D arena + 3D Boids + moderngl GPU renderer (R7)
  evolve3d.py  evolved 3D foraging brains (3D sensing + GA) (R8)
  coevo3d.py   predator–prey co-evolution in 3D (R9)
  predprey3d.py  continuous self-sustaining 3D ecosystem (R10)
  swarm3d.py   large-scale 3D flocking via KD-tree spatial index (R13)
  bigworld3d.py  KD-tree-accelerated large-scale 3D ecosystem (R14)
  cycles.py    sustained predator-prey limit cycles (refuge floor) (R15)
  speciation.py  sympatric speciation (disruptive selection + assortative mating) (R16)
  signals.py   evolution of communication (Lewis signalling game) (R17)
  evolvability.py  evolution of evolvability (self-adaptive mutation rate) (R18)
  cooperation.py   evolution of cooperation (Hamilton's rule / assortment) (R19)
  aging.py     evolution of aging (Medawar/Williams senescence) (R20)
  multicell.py   evolution of multicellularity (predation-driven) (R21)
  redqueen.py    Red Queen host-parasite coevolution (matching-allele) (R22)
scripts/
  run_boids.py     R1: flocking mp4 + metrics
  run_evolution.py R2: selection trajectories + trait histograms + replicates
  run_evolve.py    R3: GA fitness curve + behavior comparison + living world
  run_coevo.py     R4: arms-race curves + predator/prey hunt video
  run_predprey.py  R5: population dynamics + phase plane + living-world video
  run_memory.py    R6: recurrent vs memoryless comparison (honest)
  run_boids3d.py   R7: 3D flocking on the GPU (orbiting camera, mp4)
  run_evolve3d.py  R8: evolved 3D foragers + living 3D ecosystem render
  run_coevo3d.py   R9: 3D predator-prey arms race + hunt video
  run_predprey3d.py R10: continuous 3D living world (populations + video)
  run_swarm3d.py   R13: vast 12k-agent 3D murmuration
  run_bigworld3d.py R14: ~10k-creature large-scale living 3D world
  run_cycles.py    R15: sustained predator-prey cycles + phase plane
  run_speciation.py R16: one species splitting into two (diet over generations)
  run_signals.py   R17: communication evolving (success + mutual info + convention)
  run_evolvability.py R18: mutation rate evolving (static vs moving environment)
  run_cooperation.py  R19: cooperation vs assortment (Hamilton threshold)
  run_aging.py     R20: evolved survival-by-age curves (senescence)
  run_multicell.py R21: multicellularity (clustering + fitness landscape)
  run_redqueen.py  R22: Red Queen allele oscillations + host-parasite lag
  run_gallery.py   R23: tile every rung's headline frame into one journey poster
  run.sh test.sh   venv wrappers (isolate from a sourced ROS2 PYTHONPATH)
tests/         pytest (111): emergence, lifecycle, selection, neuroevolution, co-evolution, ecology, memory, 3D, scale, cycles, speciation, communication, evolvability, cooperation, aging, multicellularity, redqueen
```

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
scripts/run.sh scripts/run_boids.py --name flock          # R1
scripts/run.sh scripts/run_evolution.py --name evo        # R2
scripts/run.sh scripts/run_evolve.py --name brains        # R3
scripts/test.sh
```

Artifacts land in `runs/<name>/` (gitignored): mp4s, key frames, metric plots.
See `QUICKSTART.md` for a per-stage operator guide (which command shows what).

## Roadmap (the floor is not the ceiling)

- **R1 ✓** emergent flocking + metrics + headless rendering
- **R2 ✓** genome + mutation + natural selection + energy/reproduction
- **R3 ✓** evolved neural-network brains (foraging emerges from weights)
- **R4 ✓** predator–prey co-evolution (an arms race)
- **R5 ✓** continuous predator–prey ecology (two-species coexistence)
- **R6 ✓** recurrent / memory brains (infra built; honest negative — settled later in R26)
- **R7 ✓** 3D flocking on the GPU (moderngl) — the visual summit begins
- **R8 ✓** evolution + foraging brains in 3D (evolved 3D foragers + food)
- **R9 ✓** predator–prey in 3D (aerial arms race)
- **R10 ✓** continuous 3D ecology (self-sustaining living 3D world)
- **R11 ✓** beauty pass (depth fog, graded sky, rim light, shadows, glowing food)
- **R12 ✓** milestone review + QUICKSTART (+ first-push gate)
- **R13 ✓** vast swarms (12k+ via KD-tree spatial index)
- **R14 ✓** large-scale living world (~10k-creature KD-tree ecosystem)
- **R15 ✓** sustained predator–prey limit cycles (prey refuge floor)
- **R16 ✓** sympatric speciation (one species → two)
- **R17 ✓** evolution of communication (signals acquire meaning)
- **R18 ✓** evolution of evolvability (the mutation rate itself evolves)
- **R19 ✓** evolution of cooperation (Hamilton's rule)
- **R20 ✓** evolution of aging (Medawar/Williams senescence)
- **R21 ✓** a major transition: multicellularity (predation-driven)
- **R22 ✓** Red Queen host–parasite coevolution
- **R23 ✓** the gallery — every rung's headline frame in one journey poster
- **R24 ✓** docs-hygiene pass (trimmed progress.md to current-state)
- **R25 ✓** sexual selection — Fisherian runaway (costly ornament dragged past the survival optimum)
- **R26 ✓** the memory win — recurrent brains beat reactive ones on a *provably* memory-requiring task (the R6 rematch)
- **R27 ✓** milestone review (adversarial verification + ambition critic)
- **R28 ✓** open-endedness — MAP-Elites illuminates a behaviour space (quality-diversity)
- **R29 ✓** open-ended navigation — QD discovers routes around an obstacle field
- **R30 ✓** novelty search — beats the objective on a deceptive maze (Lehman-Stanley)
- **R31 ✓** evolving morphology — mass-spring virtual creatures evolve a body + gait (Karl Sims)
- **R32 ✓** milestone review (adversarial verify R28–R31)
- **R33 ✓** the capstone — foraging behaviour evolves IN SITU in one living world (no GA)
- **R34 ✓** in-situ predator–prey — refuge-stabilised coexistence + evolved prey evasion
- **R35 ✓** evolution in a changing world — tracking a flipping environment (sawtooth re-adaptation)
- **R36 ✓** review — red-team R33/R34/R35 (mutation-off controls)
- **R37 ✓** the evolution of sex — Muller's ratchet (recombination purges mutation load)
- **R38 ✓** spatial reciprocity — cooperation survives by clustering (Nowak-May)
- **R39 ✓** rock-paper-scissors — local dispersal preserves biodiversity
- **R40 ✓** review + phenomena-wall poster (R25–R39 montage)
- **R41 ✓** the Baldwin effect — learning guides evolution, then is genetically assimilated
- **R42 ✓** group selection — Simpson's paradox (cooperation up in the whole, down in every part)
- **R43 ✓** animation showcase — the in-situ ecosystem as a GIF (watch foraging evolve)
- **R44 ✓** Eigen's error threshold — quasispecies error catastrophe above μc≈ln(σ)/L
- **R45 ✓** morphogenesis — Gray-Scott reaction-diffusion (Turing patterns)
- **R46 ✓** Conway's Game of Life — Gosper gun + soup→ash (the CA root of ALife)
- **R47 ✓** review — refreshed phenomena gallery (R25–R46)
- **R48 ✓** Daisyworld — life regulates planetary temperature (Gaia / homeostasis)
- **R49 ✓** evolutionary branching — one lineage splits under disruptive competition
- **R50 ✓** release-readiness consolidation — full R1–R49 story, docs-hygiene
- **R51 ✓** Digital Genesis — self-replicating programs evolve (Avida/Tierra VM)
- **R52 ✓** Digital Genesis II — computation pays (NAND merit; de-novo logic emerges)
- **R53 ✓** Digital Genesis III — a tree of life (lineages coalesce to one ancestor)
- **R54 ✓** GPU substrate leap — 1.05M-cell Gray-Scott on compute shaders (≈100×)
- **R55 ✓** GPU Physarum — 1,000,000 slime-mold agents self-organize transport networks
- **R56 ✓** a million boids — GPU Vicsek flocking + phase transition (φ→0.98)
- **R57 ✓** natural selection at a million-genome scale (GPU tournament evolution)
- **R58 ✓** review — frontier gallery (R51–R57)
- **R59 ✓** local adaptation @1M — GPU spatial evolution mirrors the environment (corr→0.99)
- **R60 ✓** GPU Lenia — continuous-CA creatures self-organize from soup
- **R61 ✓** Particle Life — organisms self-assemble from an asymmetric force matrix
- **R62 ✓** autocatalytic sets (RAF) — self-sustaining chemistry at a phase transition (Kauffman)
- **R63 ✓** hypercycles (Eigen-Schuster) — limit cycle, the parasite, spiral waves
- **R64 ✓** L-system development — grammar→plant; MAP-Elites fills a morphospace
- **R65 ✓** ant-colony foraging — stigmergy trails + Deneubourg shortest path
- **R66 ✓** the edge of chaos — searching the CA rule space (Langton's λ)
- **R67 ✓** evolving CA to compute — emergent global synchronization (Mitchell-Crutchfield-Das)
- **R68 ✓** Physarum transport networks (Tero) — maze-solving + efficient networks
- **R69 ✓** Hopfield memory — energy-landscape recall + the 0.138N capacity limit
- **R70 ✓** review — adversarial re-verify R62–R69, frontier gallery (R59–R69), docs-hygiene
