# STATUS — main
updated: 2026-06-18T22:35 · loop 79
goal:     keep going divergently until Yusen orders stop (发散思维). Fresh ALife frontiers, push each round.
phase:    review
owns:     all of ~/alife (single session)
doing:    R79 done + PUSHED (2404f24) — CELLULAR POTTS MODEL / Graner-Glazier (cellsort.py). Tissue-level morphogenesis: cells = connected lattice domains, flow by Metropolis copy-attempts on adhesion (unlike-cell contact cost J per type-pair) + area constraint. Differential adhesion (like-like cheaper) -> salt-and-pepper mix of 2 cell types SORTS into separate tissues (Steinberg differential adhesion hypothesis); heterotypic A-B boundary 345->181 (48%). EQUAL-adhesion control does NOT sort (345->750, mixes) = mechanism proven. Area constraint keeps cells alive. Eye-verified (mixed->sorted). 6 tests, 402 total.
blocked:  none. Order: keep going, never stop until ordered, divergent, push each round.
next:     R80 = REVIEW ROUND (last review R70, 10 rounds ago): full-suite backstop (expect 402), adversarial re-verify R71-R79 headline metrics, frontier gallery R70-R79, docs-hygiene (README refresh through R79), milestone summary. Cold-start ORIENT. Run via env -u PYTHONPATH .venv/bin/python. scipy avail. numpy2: np.ptp(). After R80, R81+ fresh frontiers (Boltzmann machine, Tierra parasites, evolved Particle Life, GPU megascale pred-prey, major transition, voter model, Turing animal-coats).
