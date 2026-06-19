# STATUS — main
updated: 2026-06-19T02:34 · loop 106
goal:     keep going divergently until Yusen orders stop (发散思维). Fresh ALife frontiers, push each round.
phase:    review
owns:     all of ~/alife (single session)
doing:    R106 done + PUSHED (59214fd) — KPZ SURFACE GROWTH (kpz.py), ballistic vs random deposition. VERIFIED w/ control: random deposition (independent columns) w~t^0.5 (beta=0.502, never saturates); BALLISTIC deposition (sticks on first lateral contact -> column correlations) KPZ w~t^beta beta=0.31+-0.09 (seed-averaged ~1/3; single seeds noisy = strong corrections-to-scaling) + SATURATES w_sat~L^alpha alpha=0.47 (KPZ ~1/2); morphology correlated vs spiky. Deep non-eq universality from one sticking rule. Eye-verified figure (beta log-log + interface morphology + alpha scaling). 6 tests, 547 total.
blocked:  none. Order: keep going, never stop until ordered, divergent, push each round.
torchnote: torch NOT installed (numpy/scipy only). alife/nca.py untracked awaiting torch; decide fate at R110.
docrule:  README = description+deploy+block diagram ONLY (CEO R91). Per-round catalog -> progress.md; layout -> CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh sets PYTHONPATH=. Push: retry on TLS errors (for i in 1..5; push && break || sleep).
next:     R107, R108, R109 = FRESH numpy/scipy frontiers, THEN R110 REVIEW. Candidates: spatial predator-prey RD waves / Lotka-Volterra, host-parasite waves, Olami-Feder-Christensen earthquake SOC (Gutenberg-Richter), Turing-on-growing-domain (stripe splitting), evolved foraging (check R33-35), opinion/cultural variant, 3D extension. Cold-start ORIENT. scripts: scripts/run.sh. numpy2: np.ptp(). LESSON: verify EMPIRICALLY w/ control; PIVOT FAST within ~2 attempts; some exponents (KPZ) need seed-averaging — report honestly. R110 REVIEW = FULL-SUITE BACKSTOP (511@R100 -> 547) + adversarial re-verify R101-R109 + gallery R101-R109 + ambition critic + decide nca.py fate.
