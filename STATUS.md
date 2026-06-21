# STATUS — main
updated: 2026-06-20T40:30 · loop 162
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R162 RESOLVED R161's frontier option (1): a CLEAN, ROBUST ground-truthed phylogeny.
          Cultural cladistics RECOVERS the true descent under VERTICAL transmission; HORIZONTAL does not.
doing:    R162 DONE. Removed R161's two confounds: spatial_tiers=False (NEUTRAL lineage drift, no ecological
          homoplasy) + tier0_frac=0.80 lifeline (vertical-only no longer starves demes → full 27-deme Mantel
          power). New genealogy.partial_mantel_corr/partial_mantel_test (control inter-deme SPATIAL distance →
          isolation-by-distance red-team); genealogy_phylogeny_test now returns d_spatial + partial_mantel_*.
          HEADLINE (POSITIVE, robust): in a neutral world, VERTICAL transmission makes cultural distance RECOVER
          the true genealogical (patristic) distance — Mantel mean 0.366 (per seed .349/.344/.423/.348), sig 3/4
          (seed1 fails only from 12-deme low power, same effect size); HORIZONTAL/oblique copying does NOT —
          mean 0.054, sig 0/4 ≈ label-null — EVEN THOUGH horizontal copying is also spatially local. PARTIAL
          Mantel (control space) stays ~0.34 sig 3/4 → NOT isolation-by-distance. VERT>HORIZ 4/4. 禁止造假.
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_neutral_phylo.py 450 (runs/r162_neutral_phylo/panel.png EYE-VERIFIED: green
          vertical bars >> red horizontal bars 4/4; Mantel≈partial bars 4/4 → IBD ruled out; positive recovery
          scatter; TRUE vs reconstructed distance heatmaps both structured; deme-coloured 3D world n=1484).
          168 genesis tests (+2: partial-Mantel confound-removal + phylogeny_test partial/spatial fields).
redteam:  ROBUST POSITIVE. Load-bearing NEGATIVE CONTROL = the horizontal arm (same substrate+geometry, only
          transmission differs) ≈ null 4/4 → the positive is CAUSED by vertical transmission, not the test/
          geometry/deme-count (seeds 0,2 full 27 demes both arms, opposite results). +partial Mantel (IBD ruled
          out) +label-permutation null. HONEST: magnitude MODEST (~0.37, homoplasy from parallel innovation +
          movement mixing); seed-1 sig fails on low power only. Clean upgrade of R161's noisy 0.16-0.94.
blocked:  none
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife only, NOT torch/CUDA). MEMORY: ONE sim/pytest at a time; GENESIS is KD-tree + fixed-pool + bool repertoire (<100MB); genealogy log append-only (analysis-only, bounded runs); close GL ctx (r.ctx.release()).
next:     R163 PIVOT to frontier option (2): TEMPORAL phylogeny / open-ended complexity — snapshot the
          repertoire over a LONG run, reconstruct the time-ladder of cumulative descent against the logged
          genealogy, define an open-ended complexity metric that keeps CLIMBING vs an asocial null (Stage-5
          rung). The descent-recovery rung (R160→R161→R162) is now CLOSED with a clean positive. 禁止造假.
