# STATUS — main
updated: 2026-06-18T22:54 · loop 96
goal:     keep going divergently until Yusen orders stop (发散思维). Fresh ALife frontiers, push each round.
phase:    review
owns:     all of ~/alife (single session)
doing:    R96 done + PUSHED (12349a1) — KURAMOTO COUPLED OSCILLATORS (kuramoto.py). Spontaneous synchronization. dθ/dt=ω+(K/N)Σsin(θj-θi), mean-field O(N) form. VERIFIED vs theory: Kc=2/(πg(0))=1.596σ exact; CONTROL K=0.5Kc incoherent r~0.05; K=2.5Kc synced r=0.97; transition sharp+monotone across Kc; partial sync at 1.1Kc = locked plateau (68% central freqs pinned) + drifting wings. Distinct from R88 excitable (spatial waves). Eye-verified figure (phase circles + r-over-time + transition curve + locked/drifting split). 6 tests, 493 total.
blocked:  none. Order: keep going, never stop until ordered, divergent, push each round.
docrule:  README = project description + deploy/setup + block diagram ONLY (CEO R91, a5be5cd). Per-round progress -> progress.md; repo layout -> CODEBASE_GUIDE.md. Never re-add per-round ladder/Layout to README. run.sh sets PYTHONPATH=.
next:     R97 — FRESH divergent BUILD round (NOT a rehash). Candidates: Langton's self-reproducing loop (iconic, fragile-PIVOT fast within 2), GPU megascale predator-prey, evolved swimming in a fluid (fluid-sim heavy), Tierra parasites (fragile), cultural evolution/language drift, flocking-3D-with-predators, majority/Galam opinion, Turing-on-growing-domain, percolation/forest-fire. Cold-start ORIENT. scripts: scripts/run.sh <script>. numpy2: np.ptp(). LESSON: verify metric+control EMPIRICALLY; PIVOT within ~2 attempts. R100 REVIEW approaching (run FULL-SUITE BACKSTOP there; last full 457@R90, R91-R96 new-files-only +6 each -> 493).
