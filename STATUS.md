# STATUS — main
updated: 2026-06-19T00:55 · loop 84
goal:     keep going divergently until Yusen orders stop (发散思维). Fresh ALife frontiers, push each round.
phase:    review
owns:     all of ~/alife (single session)
doing:    R84 done + PUSHED (bd721f1) — EPIDEMICS ON NETWORKS / SIR (epidemic.py, builds on R83 BA/ER). Vectorized SIR over edge list (infect neighbours w/ prob beta, recover gamma). Results (Pastor-Satorras-Vespignani): VANISHING THRESHOLD — scale-free BA ignites epidemics at beta~0.05-0.08 where ER fizzles (gamma=0.3); HUBS super-spreaders (P_inf rises w/ degree 0.06->0.22); TARGETED hub immunization crushes epidemic (5%->0.005) vs random barely helps (0.37); classic SIR epidemic curve. Used gamma=0.3 for clear outbreaks (gamma=1.0 too harsh). 6 tests, 427 total.
blocked:  none. Order: keep going, never stop until ordered, divergent, push each round.
next:     R85 — fresh divergent BUILD round. Not yet done: Turing animal-coat patterns (Gierer-Meinhardt), Ising/spin-glass phase transition, major transition/division-of-labor, Tierra parasites (fragile), evolved Particle Life (sim-cost risk), GPU megascale pred-prey, Langton self-repro loop, evolved swimming, small-world (Watts-Strogatz). Cold-start ORIENT. Run via env -u PYTHONPATH .venv/bin/python. scipy avail. numpy2: np.ptp(). LESSON: verify metrics empirically; report honest nuances; pivot within ~2 attempts. FULL-SUITE BACKSTOP DUE (last full 421@R84-start; R84 +6 -> 427) — run at R85 start. REVIEW round DUE ~R90 (last review R80).
