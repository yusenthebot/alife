# STATUS — main
updated: 2026-06-18T19:35 · loop 73
goal:     keep going divergently until Yusen orders stop (发散思维). Fresh ALife frontiers, push each round.
phase:    review
owns:     all of ~/alife (single session)
doing:    R73 done + PUSHED (35c3ecf) — RESERVOIR COMPUTING / Echo State Network (reservoir.py). New paradigm: fixed RANDOM sparse recurrent reservoir (spectral radius 1.2 = edge of stability, leaky-integrator tanh) + trained-only linear readout (ridge). Driven by Lorenz (RK4) to predict 1 step, then CLOSED-LOOP on its own output -> autonomously regenerates chaos: tracks ~4.6 Lyapunov times before chaos separates them (error grows exponentially), reconstructs the butterfly 'climate' (gen std [8.3,9.3,9.8] vs true [7.7,8.8,8.7]; x-z + 3D butterfly). Best cfg n_res=800 sr=1.2 leak=0.6 ridge=1e-6. 5 tests, 362 total. (Jaeger/Pathak.)
blocked:  none. Order: keep going, never stop until ordered, divergent, push each round.
next:     R74 — fresh divergent BUILD round. Not yet done: abelian SANDPILE (canonical BTW SOC + fractal patterns), swarm CONSTRUCTION/termite, Tierra parasites (fragile), evolved Particle Life, GPU megascale predator-prey, Boltzmann machine, Langton self-reproducing loop, flocking-with-leadership/collective decision. Cold-start ORIENT. Run via env -u PYTHONPATH .venv/bin/python. scipy avail. numpy2: np.ptp(). LESSON: verify metric direction+scale empirically; pivot within ~2 attempts. Backstop ran @R73 start (verifying 357@R72); R73 +5 -> 362. Due again in ~2-3 rounds.
