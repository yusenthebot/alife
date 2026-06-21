# STATUS — main
updated: 2026-06-20T36:30 · loop 160
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R160 verified: cultural divergence is hierarchically TREE-structured (phylogenetic signal), robust.
doing:    R160 DONE (PIVOT off the twice-inert economy to cultural cladistics). New alife/genesis/phylogeny.py
          (Holland delta-Q treelikeness, UPGMA cophenetic corr, column-shuffle null) + World.phylogeny_test:
          reconstruct a CLADOGRAM of spatial-deme traditions on the R157 substrate, measure whether the
          divergence is hierarchically TREE-like (descent-with-modification) vs flat. Read-only; never feeds
          selection. POSITIVE+ROBUST (3/3 seeds + subsample-stable): local treelike 0.63-0.68 > column-shuffle
          0.51 (3/3); coph 0.68-0.79 > 0.60-0.63 (3/3). The shuffle preserves marginal freqs + prereq-DAG
          structure but breaks clade covariance -> the signal is genuinely PHYLOGENETIC, not flat/artifact.
          HONEST caveats: (1) magnitude MODEST (~0.65, substantial homoplasy; not a clean tree); (2) the
          PANMICTIC secondary is NULL (local 0.675 vs panmictic 0.709, 1/2) -> tree structure is descent
          BROADLY (spatial lineage + heritable repertoire), NOT specifically the nearest-hearth cultural
          channel; (3) asocial can't form a floor (pop collapses to 74 w/o culture on this substrate). 禁止造假.
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_phylogeny.py 450 (runs/r160_phylogeny/panel.png EYE-VERIFIED: nested cladogram of
          27 demes; treelike green>grey 2/2; coph green>grey 2/2; deme-coloured 3D world; frontier depth climbs).
          159 genesis tests (+4). phylogeny_test read-only — no flag, byte-identical to R159 sim path.
redteam:  ROBUST. 3/3 seeds (incl. headline render seed); subsample (random half/deme) keeps treelike 0.654 vs
          shuffle 0.506 = NOT sampling noise; metric unit-tested (perfect tree->1.0, star->nan, shuffle drops it).
          Honest: panmictic contrast null (signal not from local cultural transmission specifically); modest mag.
blocked:  none
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife only, NOT torch/CUDA). MEMORY: ONE sim/pytest at a time; GENESIS is KD-tree + fixed-pool + bool repertoire (bounded, <100MB); close GL ctx (r.ctx.release()).
next:     R161 frontier options (see progress.md ## Frontier): (a) SHARPEN the phylogeny — drive treelikeness
          toward a clean tree (lower homoplasy) by gating horizontal transmission / stronger lineage isolation,
          and recover the TRUE descent tree (cophenetic vs a tracked genealogy) for a ground-truthed cladistics
          claim; (b) TEMPORAL phylogeny — snapshot the population over time, reconstruct the ladder of cumulative
          descent + an open-ended complexity metric that keeps climbing; (c) cultural rate/innovation bursts
          (punctuated equilibria) across the tree. Lean (a): ground-truth the descent claim. 禁止造假.
