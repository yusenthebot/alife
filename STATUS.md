# STATUS — main
updated: 2026-06-21T06:05 · loop 171
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R171 lands frontier (1): OPEN-ENDED CULTURE NOW DRIVES THE BODY. R170's generative grown
          tree was an abstract repertoire; R171 gates EMBODIED capability (diet tiers + locomotion/reach axes)
          on the agent's realized cultural DEPTH, so the embodied ceiling is open-ended too (freezes when capped).
doing:    R171 DONE. New `depth_gates` (requires generative_tree): tier t edible iff depth >= recipe_level_step*t;
          axis i unlocks iff depth >= cap_level_step*(i+1); _eat_depth_gates + depth-gated _cap_speed/_cap_reach +
          diet_capability_ceiling() read-out. off byte-identical; mutually exclusive with the fixed-node gates.
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_r171.py → runs/r171_depth/{panel.png,world.gif} EYE-VERIFIED (~8s). 3 live worlds
          ×320: uncapped K=4000 depth 4→11, diet ceiling→top tier 4, axes→2, pop 1000, eats all tiers; capped
          K=20 frozen depth 1/ceiling 0/axes 0; null innov=0 tree never grows, ceiling 0. 213 genesis tests (+6).
redteam:  CONFIRMED — capped world with ALL food free keeps a HEALTHY pop (309) yet ceiling stays 0 (depth/tree
          frozen 1/20) vs uncapped 10/4000/4/2: the freeze is the depth-CAP, not pop death (cap = only difference).
          Plus cap-sweep monotone in K + load-bearing innov=0 null + depth_gates=False byte-identity (all tested).
blocked:  none
caveat:   diet/axes ceiling = MAX over living agents (pins early once any agent is deep); load-bearing claim is
          the CAP control + BROAD realized eating (_tier_eat_count positive across ALL tiers), not single-agent max.
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife). MEMORY: ONE sim at a time; full-stack world <200 MB; GL context released after render.
next:     R172 LEAP options (frontier): (1) WIRE THE SUPERVISOR to persist.run_segment on the generative+depth_gates
          substrate — a multi-day cloud climb where depth/diet ceiling/axes + a rolling live panel keep advancing on
          disk (the literal "left running for days" deliverable). (2) long-horizon depth-divergence verify (fixed
          plateaus vs generative keeps deepening) paired with the embodied ceiling. (3) Stage-2 SIGNALLING redesign
          (synchronous lethal arena, beat frozen+deaf+causal, ≥3 seeds). 禁止造假.
