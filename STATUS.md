# STATUS — main
updated: 2026-06-21T08:55 · loop 175
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R175 lands frontier (1)'s SUSTAINED-DEPTH rung: the open-ended world's connected tech
          DEPTH now keeps climbing the whole horizon, not just breadth. R174's caveat was depth plateaus
          by ~tick 6 under the UNIFORM composition draw; R175 adds a depth-rewarding SELECTION PRESSURE
          (depth_bias = softmax over tree level → preferential reuse of the deepest techniques) so the
          frontier keeps extending tick after tick, vs an identical unbiased control (only depth_bias=0).
doing:    R175 DONE. combinatorial.discover_inplace gains level_bias (default 0 = EXACT uniform path, no
          extra RNG; >0 = stable softmax over depth). GenesisConfig.depth_bias threads it to both discovery
          sites. Not a new mechanism/representation — only WHICH two known techniques the draw selects.
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_r175.py → runs/r175_depth/{depth.png,world.gif} EYE-VERIFIED (~44s). 10 ticks×60
          steps as GENUINE separate subprocesses; LARGE cap K=20000 for BOTH (breadth never the limiter).
          BIASED (depth_bias=1.0): connected DEPTH 32→76 monotone, +2 on the very last tick; breadth →4651;
          diet 7 axes 4; pop 1000; tree.n=4738. UNBIASED (==R174, only knob differs): DEPTH 5→12 then FROZEN
          12 from tick 6; breadth →5700; diet 6. Biased 6× deeper. World gif = dense gold (deep) living pop.
redteam:  CONFIRMED — metric not gameable: connected_depth = longest FULLY-KNOWN grounded prereq chain held
          by the society, not a registry artifact. Control isolated 3 ways: (a) depth_bias=0 bit-identical to
          pre-R175 no-arg call; (b) bare-tree biased draw ≥2× deeper than uniform same seed; (c) full-world
          run differs ONLY in depth_bias (same cap, same ticks) yet splits climb-vs-plateau. 224 tests (+3).
blocked:  none
caveat:   depth-bias TRADES breadth for depth (unbiased ends broader, 5700 vs 4651). And the EMBODIED ceiling
          (diet 7 / axes 4) saturates by tick 1, so depth above the gated tiers is repertoire-deep, not
          further-embodied — body is ≥ unbiased throughout but finite (8 tiers / 4 axes). Both honest.
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife). MEMORY: ONE sim at a time; full-stack world <200 MB; GL context released after render.
next:     R176 LEAP (frontier 1): MAKE THE BODY KEEP DEEPENING WITH THE TECH. Repertoire depth now climbs
          unbounded but the body ceilings at 8 tiers / 4 axes by tick 1 — give embodiment open-ended headroom
          (many more tiers/axes, or a depth-SCALED continuous phenotype) so the EMBODIED ceiling rises tick
          after tick alongside the tech depth. Alt: (2) breadth×depth JOINT climb (heal the tradeoff); (3)
          run the cron entrypoint for real wall-clock days with depth_bias on. 禁止造假.
