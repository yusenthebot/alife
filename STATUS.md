# STATUS — main
updated: 2026-06-21T02:55 · loop 168
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R168 is a LEAP BACK FROM ABSTRACTION: the R160-R167 arc analysed cumulative culture
          on standalone registry toys; R168 runs the WHOLE civilization stack TOGETHER in one persistent,
          RENDERED, watchable world — the CEO's actual deliverable.
doing:    R168 DONE. New alife/genesis/civdev.py: civ_config (canonical full-stack regime — building/processing
          + combinatorial culture + tech-gated diet tiers + culture-gated physical capabilities), develop_
          trajectory (read-only observer of the civilization-development signals), develop_vs_control (full vs
          asocial null), capability_color (3D agents coloured violet→gold by realized culture depth). First
          time every separately-validated R148-R167 mechanism runs as ONE living world.
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_civ.py 1500 800 → runs/r168_civ/{civ.gif,panel.png,checkpoint.npz} EYE-VERIFIED
          (~30s). PANEL: connected tech depth climbs 0→14 (cumulative staircase), both capability axes unlock
          ~step150, edible diet 1→3.86/4 tiers, population persistent at capacity, resume_ok=True. GIF: agents
          start VIOLET (base phenotype) and the whole population turns GOLD as culture deepens — the civilization
          developing, watchable. Asocial control (learn=False) flat: conn_depth 0, axes 0, eats tier-0 only.
          199 genesis tests (+3). Checkpoint save→reload→continuity proven.
redteam:  CONFIRMED-WITH-CAVEAT (independent agent). Holds 3 fresh seeds (full conn_depth 9-11 & axes=2 vs
          control 0); connected_depth independently recomputed bit-for-bit (=11); deterministic observer. CAVEAT
          (baked into docstring): the asocial floor is structural at the SHARED innov_steps=1 (one lifetime's
          discovery from empty rep can't reach a 2-prereq level-1 node); a generous budget DOES let the asocial
          world develop (innov_steps=30→depth~8). Honest claim = Tomasello's ratchet: at a MATCHED per-lifetime
          innovation budget, cumulative depth requires TRANSMISSION. Fair: both arms share innov_steps=1.
blocked:  none
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife). MEMORY: ONE sim at a time; full-stack world ~2k agents <200 MB; GL context released after render.
next:     R169 LEAP options (frontier): (1) the world develops a FULL civilization but each run RESETS — wire a
          single PERSISTENT LONG/RESUMABLE run (checkpoint chain) the CEO can leave running cloud/local, with
          development surfaced live. (2) BREAK OUT — wire unbounded.TechSpace (R164) into the live world so the
          OPEN repertoire keeps climbing past the fixed-tree ceiling (sparse-rep rewrite, vr-lead gate). (3)
          Stage-2 SIGNALLING redesign (synchronous lethal arena, beat frozen+deaf+causal, ≥3 seeds). 禁止造假.
