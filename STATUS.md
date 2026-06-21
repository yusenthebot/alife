# STATUS — main
updated: 2026-06-20T39:00 · loop 161
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R161 GROUND-TRUTHED R160's cladogram: it does NOT recover the true descent under default
          (horizontal) transmission (honest negative); vertical-only raises recovery but not robustly.
doing:    R161 DONE (ground-truth the cladistics). New alife/genesis/genealogy.py (patristic birth-forest
          distance + Mantel test) + World.genealogy_phylogeny_test (Mantel: reconstructed CULTURAL distance vs
          TRUE GENEALOGICAL distance from a logged birth forest, vs a label-permutation null) + vertical_only
          flag (gate oblique transmission). track_genealogy = PASSIVE observer (no RNG, byte-identical off,
          verified). HEADLINE = HONEST NEGATIVE: under default OBLIQUE transmission the R160 tree-shaped
          cladogram does NOT recover the true line of descent (Mantel 0/4 seeds, mean 0.06 ≈ null) — cultural
          similarity tracks shared ENVIRONMENT (ecological convergence/homoplasy), not ANCESTRY. Rigorously
          confirms R160's own panmictic-null caveat. CAUSAL CONTRAST: gating to VERTICAL-only transmission
          RAISES recovery in the predicted direction (mean Mantel 0.47 vs 0.06, up to 0.94, sig 2/4) — but NOT
          robustly (vertical-only shrinks viable demes → small-D Mantel noise; ecological convergence competes).
          So: robust negative for horizontal, suggestive-but-noisy positive for vertical. 禁止造假.
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_genealogy.py 450 (runs/r161_genealogy/panel.png EYE-VERIFIED: TRUE vs reconstructed
          distance heatmaps; recovery scatter weak under horizontal; contrast bars vertical(green) > horizontal
          (red) on 2/4 seeds, null≈0; 3D deme-coloured world). 166 genesis tests (+7). genealogy unit-validated
          (perfect tree→corr 1.0, label-null→0). track_genealogy/vertical_only default-off = R150..R160 path.
redteam:  partial. ROBUST NEGATIVE: horizontal recovery 0/4 sig, mean 0.06 indistinguishable from label-null.
          The vertical-only positive is SEED-DEPENDENT (2/4) and confounded by deme-count shrinkage (vertical
          seed3 corr 0.94 but only 5 demes = low power). Honest: the clean per-seed contrast is NOT established;
          only the mean trend + the robust horizontal negative are.
blocked:  none
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife only, NOT torch/CUDA). MEMORY: ONE sim/pytest at a time; GENESIS is KD-tree + fixed-pool + bool repertoire (<100MB); genealogy log grows append-only (analysis-only, bounded runs); close GL ctx (r.ctx.release()).
next:     R162 frontier (see progress.md ## Frontier + ## Decisions pending). Lead options: (a) make VERTICAL
          recovery ROBUST — stabilise vertical-only viability (seed founders with recipes / gentler bootstrap so
          demes don't shrink) for a clean 4/4 contrast, OR drop spatial ecological selection so cultural
          divergence is NEUTRAL vertical drift (the cleanest descent recovery); (b) PIVOT — TEMPORAL phylogeny
          (snapshot pop over time, reconstruct the ladder of cumulative descent + an open-ended complexity
          metric that keeps climbing); (c) GENERATIVE/unbounded tech space. 禁止造假.
