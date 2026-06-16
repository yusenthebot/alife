# alife — an evolving artificial-life ecosystem

Watch a pool of simple creatures go from blind flocking to evolved "intelligence",
one generation at a time. The floor is the simplest possible swarm; there is no
ceiling — the project escalates through genetic selection, neural-network brains,
predator–prey dynamics, energy and reproduction, toward a 3D ecosystem you can
watch evolve behavior on its own.

This repository is built in autonomous **evolving rounds**: each round clears the
current bar, then researches the frontier and raises it. Every round is *really*
run — frames rendered, screenshots inspected, metrics plotted — never faked.

## Current state — Round 1: emergent flocking

A fully vectorized Reynolds Boids swarm (separation · alignment · cohesion) on a
toroidal world, with quantitative emergence metrics and a headless renderer.

From a random start, collective order **emerges**: the Vicsek order parameter
climbs from ≈0.08 to ≈0.95 with no leader and no central control.

| | start | end |
|---|---|---|
| order parameter φ | 0.08 (disordered) | 0.92–0.95 (aligned) |
| nearest-neighbor distance | 4.4 | ≈2.5 (cohesion vs separation balance) |
| clusters | scattered | 1–3 coherent flocks |

## Layout

```
alife/
  world.py     toroidal/bounded space: wrap, minimum-image distance
  boids.py     vectorized Reynolds step (pure function of state + params)
  metrics.py   order parameter, milling, packing, cluster count
  render.py    headless Pillow renderer: heading-colored boids + motion trails
  sim.py       simulation driver — steps, measures, optionally renders
scripts/
  run_boids.py CLI: run a sim, emit mp4 + key frames + metrics csv/plot
  run.sh test.sh  venv wrappers (isolate from a sourced ROS2 PYTHONPATH)
tests/         pytest: emergence + invariants + metric unit tests
```

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
scripts/run.sh scripts/run_boids.py --n 700 --steps 450 --name demo
scripts/test.sh
```

Artifacts land in `runs/<name>/` (gitignored): `flock.mp4`, `frame_*.png`,
`metrics.csv`, `metrics.png`.

## Roadmap (the floor is not the ceiling)

- **R1 ✓** emergent flocking + metrics + headless rendering
- **R2** genome + mutation + natural selection + energy/reproduction
- **R3** neural-network brains with sensors (evolved, not hand-coded rules)
- **R4** predator–prey co-evolution
- **R5+** spatial scaling, speciation, and a 3D ecosystem
