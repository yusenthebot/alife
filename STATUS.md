# STATUS — main
updated: 2026-06-20T22:30 · loop 151
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R151 INTEGRATED CAPSTONE: all ladder stages run in ONE world; reveals an emergent STAGE INTERACTION (verified + red-teamed).
owns:     all of ~/alife (single session)
doing:    R151 DONE. Every ladder stage was verified in ISOLATION behind its own flag; they had NEVER run
          together. The capstone turns them ALL on in one world (predators + caste specialize + building +
          culture + combinatorial). Integration first surfaced + fixed a real CORRECTNESS collision: the
          harvest payoff was `if specialize ... elif culture` (mutually exclusive), so with BOTH on culture's
          tech_gain energy bonus was SILENTLY DROPPED. Fixed = compose MULTIPLICATIVELY via a new
          `_harvest_gain` helper (byte-identical to every prior single-flag config; unit-test + byte-id guarded;
          93 genesis tests green, +3). HEADLINE FINDING (only visible integrated): NICHE CONSTRUCTION (Stage 4)
          SUBSTITUTES FOR THE DIVISION OF LABOUR (Stage 3) — built hearths ripen raw food passively (and the
          building action REPLACES the per-agent `_process` path), so the costly processor caste is redundant
          and selected away. REAL-VERIFY (scripts/run_genesis_capstone.py; runs/r151_capstone/panel.png +
          caste-coloured 3D capstone.gif eye-verified): identical food level, WITH hearths frac_proc(spec>0.8)
          → 0.00 (seeds 0+1), WITHOUT hearths → 0.62; meanwhile predator-prey PERSIST (no extinction, 2 seeds),
          hearths accumulate (600), open-ended culture climbs (pop_distinct→319, frontier lvl→10). MECHANISM
          confirmed: hearths sustain ~400 ripe food with ~0 processors. RED-TEAM (independent agent, 禁止造假):
          ROBUST across seeds 2/3/4 (0.00 vs 0.44-0.57), whole-distribution shift (not a threshold artifact),
          predators+culture ruled out, ripening causally load-bearing (kill it → extinction). HONEST CAVEAT: the
          no-hearth state is processor-DOMINATED (spec_mean ~0.7, harvesters only 5-14%), so "division of labour"
          slightly oversells its balance; substitution direction/magnitude are not in doubt. Also honest: the
          open-ended cultural climb is transmission-driven (payoff-independent), so the harvest fix is a
          CORRECTNESS fix, not a climb-mover in this food-rich regime. COMMITTED; pushing.
blocked:  none
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife only, NOT torch/CUDA). MEMORY: ONE sim/pytest at a time; GENESIS is KD-tree + fixed-pool + bool repertoire (bounded, <100MB); close GL ctx (r.ctx.release()).
next:     R152 default = make Stages 3+4 COMPLEMENT not substitute: hearths require a processor caste to BUILD/
          maintain them so a genuine division-of-labour economy RE-EMERGES around niche construction (the
          balanced DoL the capstone showed is currently missing). Alts: couple the tech tree to WORLD-ACTIONS
          (techniques unlock build types/tools); parked Stage-2 signalling redesign. See progress.md ## Frontier.
