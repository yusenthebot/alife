# STATUS — main
updated: 2026-06-21T05:10 · loop 170
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R170 lands frontier (1): OPEN-ENDEDNESS MADE CAUSAL in the live world. The living culture
          no longer explores a FIXED pre-built tree (frozen ceiling) — it GROWS the tech tree on demand from
          the population's real compositions, open-ended BY CONSTRUCTION, bounded only by the memory cap.
doing:    R170 DONE. New combinatorial.GrowingTree (live-world analogue of R164 unbounded.TechSpace over the
          SAME dense rep): materialize a deeper node the first time two known techniques compose; pa/pb/level
          are the World's _tree_* arrays mutated in place. Wired behind generative_tree flag (off=byte-identical).
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_r170.py → runs/r170_generative/{panel.png,world.gif} EYE-VERIFIED (~7s). 3 live
          full-stack worlds ×320 steps. generative big-cap K=4000: breadth 145→3962, depth 5→9, tree grew
          6→4000 nodes from real compositions. generative capped K=30: FROZEN at breadth 30 / depth 2. fixed
          pre-built tree: breadth→185 depth→8 (hard ceiling). 207 genesis tests (+5: GrowingTree unit + cap
          control + byte-identity-off + live-world open-ended climb).
redteam:  CONFIRMED — freeze is the CAP not pop death (cap sweep: breadth tracks cap exactly 30/120/3668, pops
          healthy 719/1000/1000); load-bearing null innov_steps=0 → breadth stays 6=n_seed, tree never grows.
blocked:  none
caveat:   in a SHORT run fixed-tree depth (8) ≈ generative (9-10) — claim is the CAP control (frontier bounded
          ONLY by capacity; depth scales 2/3/10 with K), NOT "out-depths fixed in 320 steps". Generative tree
          does NOT yet GATE physical actions (needs pre-built deep nodes) — next rung.
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife). MEMORY: ONE sim at a time; full-stack world <200 MB; GL context released after render.
next:     R171 LEAP options (frontier): (1) GATE physical actions on the GROWN tree — dynamic recipe/capability
          designation (deepest live nodes unlock diet tiers / capability axes) so open-ended culture causally
          drives EMBODIED capability, not just an abstract repertoire. (2) wire persist.run_segment into the
          supervisor for a multi-day cloud climb on the generative substrate. (3) Stage-2 SIGNALLING redesign
          (synchronous lethal arena, beat frozen+deaf+causal, ≥3 seeds). 禁止造假.
