# STATUS — main
updated: 2026-06-18T19:05 · loop 72
goal:     keep going divergently until Yusen orders stop (发散思维). Fresh ALife frontiers, push each round.
phase:    review
owns:     all of ~/alife (single session)
doing:    R72 done + PUSHED (ee2e1a2) — GENETIC PROGRAMMING / Koza symbolic regression (genprog.py). NEW evolutionary substrate: evolve variable-structure PROGRAM TREES (operators + - * / sin cos over x + consts) vs all prior fixed-genome GAs. Tree-GA (tournament + subtree crossover/mutation + parsimony). From (x,y) data alone rediscovers the hidden formula: x²+sin(2x) recovered EXACTLY as sin(x+x)+(x*x) RMSE 0.000; cubic x³-x²+x RMSE 0.001; x³/3-x RMSE 0.067. Error falls over gens, parsimony curbs bloat. Trees = immutable nested tuples, protected division, vectorized eval. Fast (~1-2s/run). 7 tests, 357 total.
blocked:  none. Order: keep going, never stop until ordered, divergent, push each round.
next:     R73 — fresh divergent BUILD round. Not yet done: abelian SANDPILE (canonical BTW SOC + fractal patterns), swarm CONSTRUCTION/termite morphogenesis, Tierra parasites (fragile), evolved Particle Life, GPU megascale predator-prey, Boltzmann machine (stochastic Hopfield), Langton self-reproducing loop, reservoir computing / echo state. Cold-start ORIENT. Run via env -u PYTHONPATH .venv/bin/python. scipy avail. numpy2: np.ptp() not ndarray.ptp(). LESSON: verify metric direction+scale empirically; pivot within ~2 attempts. FULL-SUITE BACKSTOP DUE (last full 344@R70; R71+R72 +13 -> 357 new-files-only) — run at R73 start.
