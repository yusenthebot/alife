# STATUS — main
updated: 2026-06-18T22:44 · loop 95
goal:     keep going divergently until Yusen orders stop (发散思维). Fresh ALife frontiers, push each round.
phase:    review
owns:     all of ~/alife (single session)
doing:    R95 done + PUSHED (717f3b0) — BACTERIAL CHEMOTAXIS run-and-tumble (chemotaxis.py). E.coli climbs gradient by TEMPORAL sensing (no direction sense): runs + tumbles, suppress tumbling while concentration improving. VERIFIED w/ control: alpha=0 (no modulation) pure diffusion conc flat 0.25, 14% near source; alpha=10 climbs conc 0.25->0.44, 37% accumulate near source; dose-response monotone (conc 0.25->0.58 as alpha 0->16). Distinct from R65 ants (stigmergy) & R55/R68 Physarum. Eye-verified figure (accumulation-vs-diffuse + climb-over-time + dose-response + run-and-tumble trajectories). 6 tests, 487 total.
blocked:  none. Order: keep going, never stop until ordered, divergent, push each round.
docrule:  README = project description + deploy/setup + block diagram ONLY (CEO R91, a5be5cd). Per-round progress -> progress.md; repo layout -> CODEBASE_GUIDE.md. Never re-add per-round ladder/Layout to README. run.sh sets PYTHONPATH=.
next:     R96 — FRESH divergent BUILD round (NOT a rehash). Candidates: Langton's self-reproducing loop (iconic, fragile-PIVOT fast within 2), GPU megascale predator-prey, evolved swimming in a fluid (fluid-sim heavy), Tierra parasites (fragile), cultural evolution/language drift, flocking-3D-with-predators, sandpile-on-network, majority-vote/Galam opinion, kuramoto sync oscillators. Cold-start ORIENT. scripts: scripts/run.sh <script>. numpy2: np.ptp(). LESSON: verify metric+control EMPIRICALLY; PIVOT within ~2 attempts. NEXT REVIEW ~R100 (run FULL-SUITE BACKSTOP there; last full 457@R90, R91-R95 new-files-only +6 each -> 487).
