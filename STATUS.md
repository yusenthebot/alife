# STATUS — main
updated: 2026-06-20T35:00 · loop 159
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R159 verified: PRODUCTIVE goods trade unlocks wasted food, but STILL causally inert (deeper negative).
doing:    R159 DONE (Stage-4 economy, attempt 2). Answered R158's inert-REDISTRIBUTION negative with PRODUCTION: a
          tier-t specialist harvests up to goods_max EXTRA wasted ripe locked motes within trade_radius and ships
          each as an edible GOOD to a nearby HUNGRY COMPLEMENTARY partner (energy-conserving: good=mote value,
          mote removed -> frees a food slot). seed_specialists isolates the economy from the R157 emergence
          bootstrap. POSITIVE (structure): the productive economy FIRES — ~2450 wasted motes/run consumed-for-
          trade, shipped LOCALLY (partner dist 7.9 << radius 12) to complementary partners, vs scramble null
          (dist 69). HONEST NEGATIVE (DEEPER than R158): pop ON == pop OFF (|goods-off|=0, 2/2 seeds + 2/2 tests).
          Unlocking wasted food does NOT raise carrying capacity because the pop is NOT food-limited at all —
          RED-TEAMED: pop=900 flat across food_regrow 12->80 (7x supply) AND food_cap 300->2500 (8x stock; at
          fc=300 pop is 3.2x the food count). The binding constraint is foraging/lifespan, not food. So PRODUCTION,
          like redistribution, leaves it untouched. 禁止造假.
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_goods.py 300 (runs/r159_goods/panel.png EYE-VERIFIED: pop ON/OFF curves OVERLAP at
          900; pop FLAT as food supply varies 6x; goods volume real; branch-coloured 3D living world). 155 genesis
          tests (+4). trade_goods=False + seed_specialists=False byte-identical to R157.
redteam:  ROBUST negative. Refuted the "food_cap-limited" alternative: varied food_cap 300->2500 and food_regrow
          12->80, pop pinned at 900 in EVERY case (pop even exceeds the standing food count 3.2x at fc=300). The
          carrying capacity is intrinsic (foraging/lifespan/world-size), not set by food supply -> unlocking food
          cannot lift it. Two independent economy attempts (R158 redistribution, R159 production) now agree: an
          economy bolted onto this substrate does not change the population outcome.
blocked:  none
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife only, NOT torch/CUDA). MEMORY: ONE sim/pytest at a time; GENESIS is KD-tree + fixed-pool + bool repertoire (bounded, <100MB); close GL ctx (r.ctx.release()).
next:     R160 (PIVOT per anti-thrash — economy is twice-shown inert on THIS pop ceiling). Two genuine options:
          (a) CULTURAL PHYLOGENY/cladistics across generations — reconstruct the lineage tree of recipe branches,
          measure cumulative cultural complexity climbing over a long run (the R157-next rung, independent of the
          inert economy); (b) make the population FOOD-limited by construction (raise the intrinsic forage ceiling
          well above food supply, e.g. larger world / cheaper metabolism / no max_age cap) so that THEN trade's
          food-unlocking can finally bind — a substrate change, gated on a real argument. Lean (a): it advances
          the civilization ladder without fighting the population invariant. See progress.md ## Frontier.
