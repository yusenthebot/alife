# STATUS — main
updated: 2026-06-16T22:10 · loop 6
goal:     evolving artificial-life ecosystem in ~/alife — Boids → genome/selection → NN brains → predator-prey → 3D (frontier mode, floor≠ceiling)
phase:    review
owns:     all of ~/alife (single session)
doing:    R6 done — recurrent (memory) brains (brain.py RecurrentSpec + memory.py tasks). HONEST finding: evolved memory did NOT robustly beat memoryless control (occlusion: sweep wins; nest task: seed/param-dependent, ~parity with more GA power). Real infra + tests (58 pass), negative result documented.
blocked:  none
next:     R7 — PIVOT TO 3D ecosystem viewer (moderngl/raylib offscreen) = the goal's visual summit; carry R1-R5 stack into 3D. (Alt: earn memory win via delayed-response/curriculum.)
