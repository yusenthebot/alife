# STATUS — main
updated: 2026-06-17T02:00 · loop 8
goal:     evolving artificial-life ecosystem in ~/alife — Boids → genome/selection → NN brains → predator-prey → 3D (frontier mode, floor≠ceiling)
phase:    review
owns:     all of ~/alife (single session)
doing:    R8 done — EVOLUTION lifted into 3D (evolve3d.py): body-frame 3D sensing -> MLP -> 3D accel, generational GA. fitness 0.9->49, held-out evolved 52.6 vs random 0.5 (~100x, 2 seeds). render3d food points added. 3D ecosystem GPU-rendered + verified. 71 tests pass.
blocked:  none
next:     R9 — predator-prey in 3D (aerial pursuit/evasion + co-evolution arms race, GPU-rendered prey cyan/predators red); reuse coevo + evolve3d 3D sensing/movement
