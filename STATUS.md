# STATUS — main
updated: 2026-06-21T06:40 · loop 172
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R172 lands frontier (1)'s FOUNDATION: PERSISTENCE NOW WORKS ON THE OPEN-ENDED GENERATIVE
          SUBSTRATE. The grown tree itself is checkpointed, so a resumed run keeps its connected depth AND its
          embodied diet ceiling instead of collapsing to a fresh seed-only tree. The open-ended climb is durable.
doing:    R172 DONE. GrowingTree.state()/restore() (registry rebuilt from parents, restore IN PLACE) +
          save/load_checkpoint persist tree_pa/pb/level/n when generative_tree on; depth_gates snapshot records
          diet ceiling + axes so the climb shows on the on-disk trajectory. Off-path byte-identical.
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_r172.py → runs/r172_persist/{panel.png,world.gif} EYE-VERIFIED (~8.5s). 4 REAL
          subprocess restarts ×80 on generative+depth_gates: on-disk continuous step 0→320, conn_depth 3→9,
          diet ceiling 1→4, axes→2, pop 1000. Continuity proof: resumed-chain vs uninterrupted max|diff|=0,
          bit-for-bit identical on ALL signals. Render shows restored gold (deep) pop. 216 genesis tests (+3).
redteam:  CONFIRMED — load-bearing not-vacuous control (test_persist_generative_tree_restore_is_load_bearing):
          a boundary chain that reloads the checkpoint but RESETS the tree to a fresh seed-only GrowingTree
          (pre-R172 bug) DIVERGES (max_abs_diff>0). So the bit-for-bit continuity is CAUSED by the tree restore,
          not trivial reconstruction. Plus depth/diet genuinely CLIMB in the window (not flat) + lossless roundtrip.
blocked:  none
caveat:   continuity is exact only when the resumed process rebuilds the SAME gen_cfg() (a cfg/capacity mismatch
          raises on restore by design) — the multi-day driver must pin the config.
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife). MEMORY: ONE sim at a time; full-stack world <200 MB; GL context released after render.
next:     R173 LEAP (frontier 1, now UNBLOCKED): STAND UP THE MULTI-DAY UNATTENDED CLIMB — wire a supervisor/cron
          tick to persist.run_segment on the generative+depth_gates gen_cfg() against one on-disk state_dir, with
          a rolling live panel regenerated each tick from the accumulated trajectory (the literal "left running
          for days, it keeps developing" deliverable). Alt: (2) long-horizon fixed-vs-generative depth divergence
          shown in the BODY; (3) Stage-2 signalling redesign (parked). 禁止造假.
