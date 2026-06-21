# STATUS — main
updated: 2026-06-21T00:30 · loop 166
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R166 RECONNECTED the abstract R165 rate law to the LIVE GenesisWorld. The innovation
          RATE law EMERGES from the live economy (closes R165's "E(N)∝N is posited" caveat).
doing:    R166 DONE. New alife/genesis/livephylorate.py — step_trajectory drives the REAL combinatorial
          GenesisWorld (evolved-neural agents) and emits a phylorate-shaped trajectory {step,n_distinct,
          new,active} so R165's rate tools apply UNCHANGED to the live economy; rate_slope = live
          accelerating-or-not read. HEADLINE: tech PAYS energy (harvest×(1+tech_gain·tech)) → bigger pop
          → more newborns → more innovation attempts = ENDOGENOUS autocatalysis (no longer posited).
          DECISIVE CONTROL tech_gain=0 on the SAME tree → rate flattens, repertoire saturates ~4-5× lower.
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_livephylorate.py 1200 → runs/r166_livephylorate/panel.png EYE-VERIFIED:
          (A) red ECONOMY rate-vs-N rises (~0.5→1.3) vs gray CONTROL flat/low; (B) repertoire 960/1937 vs
          235/397; (C) workforce → capacity 9000 vs stuck ~1.7-2.1k; (D) slope bars econ +1.08/+1.35 vs
          ctrl -0.44/+0.31. 2 regimes × 2 seeds, 122s. 192 genesis tests (+3).
redteam:  CONFIRMED (independent agent, 4 fresh seeds). ECONOMY repertoire 3.3-6.9× & workforce 3.6-4.8×
          larger 6/6; tech_gain isolated to genesis.py:835 (byte-identical discovery RNG). LOAD-BEARING:
          MATCHED-N dN/dt — econ ~2-3× ctrl at EQUAL N, gap WIDENS → genuine endogenous effort, NOT a
          "more agents → more births" artefact. CAVEAT (baked into docstring): rate_slope SIGN is fragile
          (ctrl flips -0.92..+0.48/kN across seeds) → report matched-N + repertoire/workforce gap, not the
          bare slope; combinatorial channel gives a weak intrinsic rise, the economy AMPLIFIES it.
blocked:  none
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife only). MEMORY: ONE sim at a time; live combinatorial world ~9k agents × 8k-bit rep ≈ 9 MB, <100 MB; no GL in this round.
next:     R167 frontier options: (1) ENDOGENOUS-DEPTH — does the live economy also push frontier DEPTH
          (max_level), or only breadth? deepen the matched-N analysis into a dedicated panel. (2) Lift the
          live max_techniques cap via unbounded.TechSpace so the live world is genuinely OPEN (sparse rep,
          spike-then-migrate, vr-lead gate — fixed-width rep matrices break). (3) Stage-2 SIGNALLING
          redesign (synchronous lethal-predation arena) — the long-deferred language rung. 禁止造假.
