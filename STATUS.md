# STATUS — main
updated: 2026-06-19T02:44 · loop 107
goal:     keep going divergently until Yusen orders stop (发散思维). Fresh ALife frontiers, push each round.
phase:    review
owns:     all of ~/alife (single session)
doing:    R107 done + PUSHED (0a56c32) — OLAMI-FEDER-CHRISTENSEN EARTHQUAKES (earthquake.py), non-conservative SOC. Grid of stress loaded to threshold -> site slips (reset 0, give alpha*stress to 4 neighbours) -> avalanche. NON-conservative (4*alpha<1 loses stress) yet SOC survives (vs R74 conservative abelian sandpile). VERIFIED: SOC regime alpha=0.22 -> Gutenberg-Richter power-law tau~1.9 over ~2 decades; strong dissipation alpha=0.10 -> only tiny quakes; conservation tunes catalogue (big-quake fraction 0->0.98 as alpha 0.12->0.25). Open boundaries, zero-velocity loading. Eye-verified figure (GR law + alpha sweep + big-frac control). 6 tests, 553 total.
blocked:  none. Order: keep going, never stop until ordered, divergent, push each round.
torchnote: torch NOT installed (numpy/scipy only). alife/nca.py untracked awaiting torch; decide fate at R110.
docrule:  README = description+deploy+block diagram ONLY (CEO R91). Per-round catalog -> progress.md; layout -> CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh sets PYTHONPATH=. Push: retry on TLS (for i in 1..5; push && break || sleep 4).
next:     R108, R109 = FRESH numpy/scipy frontiers, THEN R110 REVIEW. Candidates: spatial predator-prey RD waves / Lotka-Volterra, host-parasite waves, Turing-on-growing-domain (stripe splitting), evolved foraging (check R33-35), opinion/cultural variant, 3D extension (3D Ising/percolation dimension dependence), Bak-Sneppen variants. Cold-start ORIENT. scripts: scripts/run.sh. numpy2: np.ptp(). LESSON: verify EMPIRICALLY w/ control; PIVOT FAST within ~2 attempts. R110 REVIEW = FULL-SUITE BACKSTOP (511@R100 -> 553) + adversarial re-verify R101-R109 + gallery R101-R109 + ambition critic + decide nca.py fate.
