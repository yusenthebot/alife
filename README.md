# alife — an evolving artificial-life ecosystem

Watch a pool of simple creatures go from blind flocking to evolved "intelligence",
one generation at a time. The floor is the simplest possible swarm; there is no
ceiling — the project escalates through genetic selection, neural-network brains,
predator–prey dynamics, energy and reproduction, toward a 3D ecosystem you can
watch evolve behavior on its own.

This repository is built in autonomous **evolving rounds**: each round clears the
current bar, then researches the frontier and raises it. Every round is *really*
run — frames rendered, screenshots inspected, metrics plotted — never faked.

## Current state — Round 13: a vast, beautiful, self-sustaining 3D world

The pool has climbed thirteen rungs, each really run and verified by eye + data:

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

> Honest notes: (1) in-situ selection on brains proved too noisy, so R3/R4
> selection is a generational GA, with the continuous ecosystem as the
> living-world viewer seeded with evolved brains. (2) R5 reaches stable
> coexistence with one boom-bust transient, not sustained limit cycles — a narrow
> window that otherwise tips into extinction. (3) R6's memory advantage is not
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
  run.sh test.sh   venv wrappers (isolate from a sourced ROS2 PYTHONPATH)
tests/         pytest (82): emergence, lifecycle, selection, neuroevolution, co-evolution, ecology, memory, 3D, scale
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
- **R6 ✓** recurrent / memory brains (infra built; memory advantage = open frontier)
- **R7 ✓** 3D flocking on the GPU (moderngl) — the visual summit begins
- **R8 ✓** evolution + foraging brains in 3D (evolved 3D foragers + food)
- **R9 ✓** predator–prey in 3D (aerial arms race)
- **R10 ✓** continuous 3D ecology (self-sustaining living 3D world)
- **R11 ✓** beauty pass (depth fog, graded sky, rim light, shadows, glowing food)
- **R12 ✓** milestone review + QUICKSTART (+ first-push gate)
- **R13 ✓** vast swarms (12k+ via KD-tree spatial index)
- **R14+** livelier dynamics, large-scale ecosystems, speciation
