# STATUS — main
updated: 2026-06-20T41:30 · loop 163
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R163 landed frontier option (1): TEMPORAL phylogeny / open-ended cumulative descent.
          Combinatorial culture RECOVERS the time-ladder of descent; additive null scrambles it; asocial never climbs.
doing:    R163 DONE. New track_tech_history passive observer (logs each technique's FIRST-APPEARANCE step; no RNG,
          byte-identical off) + phylogeny.temporal_ladder_signal (precedence + level<->time Spearman vs label-perm
          null) + World.temporal_phylogeny_test. HEADLINE (ROBUST POSITIVE, red-teamed CONFIRMED 4 seeds): the
          combinatorial (prereq-gated) arm recovers the generative tree's TIME-LADDER — precedence 1.000 (a
          technique never appears before BOTH its prereqs) + level<->time corr 0.94 (p~0 vs null ~0), 2/2 seeds;
          the ADDITIVE null (same tree+machinery, prereq gate OFF) scrambles it (prec 0.35, corr ~0); the ASOCIAL
          null never climbs (max_level 0, only 8 seeds). Frontier depth climbs 0→9, breadth 8→~312 vs asocial flat.
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_temporal.py 500 (runs/r163_temporal/panel.png EYE-VERIFIED: gold staircase climb vs
          flat asocial; combinatorial ladder scatter deep=late corr 0.94; additive scatter scrambled corr 0.01;
          tall gold recovery bars 2/2 vs ~0 null; depth-coloured live 3D world n=3733). 174 genesis tests (+6).
redteam:  ROBUST POSITIVE (independent agent, refutation-first, CONFIRMED 6/6). Decisive control = the ADDITIVE
          null: identical tree + identical metric machinery, prereq gate the ONLY difference, cleanly scrambles
          BOTH precedence (1.0→0.35) + corr (0.94→0) → neither headline is a tautology or a level-definition
          artifact. Re-run 4 seeds (0,1,7,13) all robust. _spearman matches scipy 1e-9. HONEST: precedence=1.0 is
          mechanistically forced (discriminating, not vacuous — additive breaks it); the additive null reaches the
          WHOLE pool (max_level 20/distinct 1500) but in SCRAMBLED order, so depth/breadth MAGNITUDE alone cannot
          distinguish cumulative descent from unstructured accumulation — only the temporal ORDER does (the point).
blocked:  none
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife only, NOT torch/CUDA). MEMORY: ONE sim/pytest at a time; GENESIS is KD-tree + fixed-pool + bool repertoire (<100MB); tech-history log = one int array of length max_techniques (analysis-only, bounded runs); close GL ctx (r.ctx.release()).
next:     R164 PIVOT to frontier option (2): GENUINELY UNBOUNDED generative tech space — lift the max_techniques cap
          (a new technique IS the hashed pair of its parents) so depth can climb without bound; pair with the R163
          temporal-ladder + a max-depth complexity metric that provably keeps climbing. The descent-structure rung
          (spatial R160-R162 + temporal R163) is now CLOSED with clean positives. 禁止造假.
