# STATUS — main
updated: 2026-06-20T24:30 · loop 153
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R153 ACHIEVED + red-teamed ROBUST: culture UNLOCKS world-actions.
owns:     all of ~/alife (single session)
doing:    R153 DONE. Lifted the R151 frontier "make culture MATTER physically": until now the learned `tech`
          only multiplied a harvest SCALAR (1+tech_gain·tech) — cultural depth changed a NUMBER, not what an
          agent DID. R153 makes culture change a PHYSICAL action: food spawns in recipe-locked TIERS; a tier-t
          mote (t≥1) is edible ONLY by an agent whose combinatorial repertoire holds that tier's RECIPE technique
          (a deep tech-tree node; tier t needs tree-level ≥ recipe_level_step·t). Deeper CULTURE physically
          unlocks richer food the world otherwise denies. Additive behind `tech_actions` (requires
          combinatorial); tech_actions=False = R150/R151 byte-identical (food_tier all-zero, no extra RNG, eat
          path unchanged). 109 genesis tests green (+10). REAL-VERIFY (scripts/run_genesis_recipes.py;
          runs/r153_recipes/panel.png + diet-breadth-coloured 3D recipes.gif eye-verified): social vs asocial,
          2 seeds — SOCIAL realized_tiers 1→4/4, mean diet breadth 3.37/4, pop 2000, 0% food wasted; ASOCIAL
          stuck at 1 tier, edible 1.0, pop ~96 (alive but locked out), 81% of ripe food rots. RED-TEAM ROBUST
          (independent agent, 6 probes): categorical gate (asocial tier_eats[1:]==EXACTLY 0); reproducible seeds
          5/6/7; CONFOUND KILLED — with tier_value_bonus=0 the pop gap is byte-identical → ~100% of the gap is
          genuine ACCESS to more motes, NOT richer payoff (the strongest "real action-unlock" result). 禁止造假.
          HONEST: social pop is capacity-clamped (2000) — a ceiling, not a free equilibrium (doesn't affect any claim).
blocked:  none
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife only, NOT torch/CUDA). MEMORY: ONE sim/pytest at a time; GENESIS is KD-tree + fixed-pool + bool repertoire (bounded, <100MB); close GL ctx (r.ctx.release()).
next:     R154 default = ADD MORE culture-gated PHYSICAL actions beyond eating (techniques unlock build types /
          faster movement / longer sense / new tools) so cultural depth reshapes movement+construction, not just
          diet — a multi-axis tech-driven economy. Alts: GENUINELY UNBOUNDED generative tech space (lift the
          max_techniques cap, techniques = pairs created on combination); EXCLUDABLE-infra redesign to revisit
          the parked R152 3+4 complement; parked Stage-2 signalling substrate redesign. See progress.md ## Frontier.
