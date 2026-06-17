# STATUS — main
updated: 2026-06-17T00:10 · loop 7
goal:     evolving artificial-life ecosystem in ~/alife — Boids → genome/selection → NN brains → predator-prey → 3D (frontier mode, floor≠ceiling)
phase:    review
owns:     all of ~/alife (single session)
doing:    R7 done — PIVOT TO 3D succeeded. 3D Boids (world3d/boids3d) + moderngl GPU offscreen renderer (render3d.py): perspective orbiting camera, lit instanced cones, ground grid. Verified on RTX 5080: order 0.045->0.936, frames show scatter->cohesive 3D flock. 66 tests pass.
blocked:  none
next:     R8 — lift EVOLUTION into 3D: 3D genome/energy/food/reproduction (R2 in 3D) and/or evolved 3D foraging brains (R3 in 3D, 3D sensors); render evolving 3D ecosystem
