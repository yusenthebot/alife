# STATUS — main
updated: 2026-06-20T17:40 · loop 149
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — Stage-5 CUMULATIVE CULTURE ACHIEVED (R149, verified+red-teamed). Ladder stages 1,3,4,5 done.
owns:     all of ~/alife (single session)
doing:    R149 DONE — Stage-5 cumulative culture = POSITIVE. culture=True gives each agent a LIFETIME-learned
          scalar `tech` (NOT genetic): a newborn ACQUIRES it by copying (×culture_fidelity) the best technique
          recorded at the nearest hearth (the built world = cultural repository) or its parent, +one innovation
          step. Higher tech multiplies harvest energy (selected), but each generation must RE-LEARN it. Building
          WRITES the builder's tech into the hearth record (keeps max) → a ratchet across generations. REAL-VERIFY
          (2500-step technique-coloured 3D + controls, panel.png + GIF eye-verified: population BRIGHTENS dark→gold
          as culture accumulates, mean frame brightness 24→51): FALSIFIABLE headline tech_mean cumulative 12.93 vs
          ASOCIAL (learn=False) 0.19 = 66.6x, 3/3 seeds (asocial pinned exactly at innov_mean=0.19 — no
          accumulation). FROZEN-GENOME (evolve=False) tech_mean 12.98 → cultural NOT genetic. FIDELITY THRESHOLD
          (Lewis-Laland) monotone: 0.99→23.1, 0.90→5.85, 0.70→2.62, 0.50→1.82. RED-TEAM (general-purpose agent):
          CONFIRMED — asocial ceiling is structural (max-order-stat ~√logN, can't reach cumulative even at N=5e5);
          tech is a separate array never touched by mutate_brains; fidelity dose-response can't be faked. HONEST
          caveats (applied): headline now LEADS tech_mean (falsifiable, collapses w/o transmission) not the
          near-monotone tech_max high-water mark; "open-ended/keeps climbing" SOFTENED to fidelity-bounded ceiling
          (~innov/(1-fidelity), high but finite). 89 genesis tests green (12 new). COMMITTED + PUSHED.
blocked:  none
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife only, NOT torch/CUDA). MEMORY: ONE sim/pytest at a time; GENESIS is KD-tree + fixed-pool (bounded, <1GB); close GL ctx (r.ctx.release()). numpy/scipy+moderngl+imageio; torch DEFERRED CEO-gate.
next:     R150 = the full ambition ladder (3D foundation→niches→arms race→DoL→niche construction→culture) is now
          COMPLETE. Options: (1) INTEGRATE — run all stages in ONE world simultaneously (DoL+building+culture
          coexisting) as the capstone living civilization; (2) genuinely OPEN-ENDED culture — combinatorial
          innovation (tech enables better innovation, ideas-beget-ideas) so the metric does NOT saturate; (3)
          revisit parked Stage-2 SIGNALLING with the substrate redesign (synchronous lethal predation rounds).
          See progress.md ## Frontier. Decide via Decision Workflow if torn; default = (1) integrated capstone.
