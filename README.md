# alife — an evolving artificial-life ecosystem

Watch a pool of simple creatures go from blind flocking to evolved "intelligence",
one generation at a time. The floor is the simplest possible swarm; there is no
ceiling — the project escalates through genetic selection, neural-network brains,
predator–prey dynamics, energy and reproduction, toward a 3D ecosystem you can
watch evolve behavior on its own.

This repository is built in autonomous **evolving rounds**: each round clears the
current bar, then researches the frontier and raises it. Every round is *really*
run — frames rendered, screenshots inspected, metrics plotted — never faked.

## Current state — Round 3: evolved neural-network brains

The pool has climbed three rungs, each really run and verified by eye + data:

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

> Honest note: in-situ continuous-ecosystem selection on brains proved too noisy
> (crowding lets food be grabbed opportunistically, diluting the skill signal), so
> R3's selection is a generational GA. The continuous ecosystem remains as the
> living-world viewer, seeded with evolved brains.

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
scripts/
  run_boids.py     R1: flocking mp4 + metrics
  run_evolution.py R2: selection trajectories + trait histograms + replicates
  run_evolve.py    R3: GA fitness curve + behavior comparison + living world
  run.sh test.sh   venv wrappers (isolate from a sourced ROS2 PYTHONPATH)
tests/         pytest (40): emergence, lifecycle, selection, neuroevolution
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

## Roadmap (the floor is not the ceiling)

- **R1 ✓** emergent flocking + metrics + headless rendering
- **R2 ✓** genome + mutation + natural selection + energy/reproduction
- **R3 ✓** evolved neural-network brains (foraging emerges from weights)
- **R4** predator–prey co-evolution (an arms race)
- **R5+** recurrent brains, speciation, spatial scaling, and a 3D ecosystem
