# STATUS — main
updated: 2026-06-20T26:00 · loop 154
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R154 ACHIEVED + red-teamed ROBUST: culture gates a MULTI-AXIS physical phenotype.
owns:     all of ~/alife (single session)
doing:    R154 DONE. Generalised R153 (culture unlocks ONE action = what you EAT) into a multi-DIMENSIONAL
          capability VECTOR: deep tech-tree nodes ALSO unlock LOCOMOTION (higher max speed, node@level cap_level_step)
          and HARVEST REACH (larger eat radius, node@level 2·cap_level_step). Cultural depth now reshapes the whole
          physical phenotype — diet (R153) + speed + reach — a tech-driven capability economy, not a single switch.
          Additive behind `tech_capabilities` (requires combinatorial); both mults=0 OR flag off = R153 byte-identical
          (no nodes designated, speed cap=cfg.speed, reach=cfg.eat_radius, no extra RNG). 127 genesis tests green (+9).
          New: combinatorial.capability_techniques; genesis _cap_speed/_cap_reach (per-agent, threaded into _act speed
          clamp + _eat_tech_actions reach), tech_capabilities_test, snapshot fields.
verify:   scripts/run_genesis_capabilities.py 800 800 (runs/r154_capabilities/panel.png + capability-breadth-coloured
          3D capabilities.gif eye-verified: social world turns GOLD as nodes spread, purple newborns mixed in). Social
          vs asocial, 2 seeds: realized_axes 2/2 vs 0; speed_cap 5.72 vs 3.00; reach 5.74 vs 3.00; realized_speed
          4.61 vs 2.65; diet tiers 4 vs 1. Asocial EXACTLY at base (categorical — deep nodes unreachable in one lifetime).
redteam:  ROBUST (independent agent, 6 probes). CONFOUND KILLED: with cap_speed_mult=0 (node unlocked, zero bonus)
          realized_speed collapses 4.35→2.71 ≈ asocial 2.53 → ~90% of the movement gap IS the cap, not a health
          confound. Metric integrity (hand-set rep exact), asocial categorical-base at 2500 steps (3.0000/3.0000),
          reach = real access (mote at 4.5 eaten only by node-holder), byte-identical-off, reproducible seeds 2/3. 禁止造假.
blocked:  none
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife only, NOT torch/CUDA). MEMORY: ONE sim/pytest at a time; GENESIS is KD-tree + fixed-pool + bool repertoire (bounded, <100MB); close GL ctx (r.ctx.release()).
next:     R155 default = make capability axes COSTLY / traded-off so agents can't hold ALL of them → emergent
          capability SPECIALIZATION (a division of labour through the TECH TREE itself, attacking the R152 negative
          from a new door). Alts: more axes (sense-range — needs threading per-agent sense through all sense sites;
          new build types / tools); GENUINELY UNBOUNDED generative tech space (lift max_techniques cap). See progress.md ## Frontier.
