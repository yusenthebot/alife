# STATUS — main
updated: 2026-06-21T10:05 · loop 177
goal:     CEO DIRECTION (R140): build GENESIS — a persistent real 3D world that, just by running, freely develops
          toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied
          agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture.
          Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R177 lands frontier (1)'s next rung: fix R176 caveat 2 (the body's DRIVER, personal mastery,
          SATURATES) by driving embodiment off the ACCESSIBLE BANKED cultural record (a lossless external memory)
          instead — the body deepens with the SOCIETY's cumulative culture, not lossy individual mastery.
doing:    R177 DONE. pheno_cumulative: body driver = max(personal pop.tech, deepest struct_tech BANKED in nearest
          strong hearth within hearth_radius). struct_tech is a running MAX over builders (never decays) → exceeds
          the lossy living-pop mean. _pheno_driver feeds _cap_speed/_cap_reach/embodied_scale. Default-off byte-identical.
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_r177.py → runs/r177_body/{body.png,world.gif} EYE-VERIFIED (~33s). 8 ticks×50 steps as
          GENUINE separate subprocesses, K=20000, seed 0. CUM (pheno_cumulative): body DRIVER 5.9→56.3 vs personal
          mastery 3.9→42.8 in the SAME run — gap GROWS 2.0→13.5 (cumulative culture increasingly outpaces the
          individual = Tomasello ratchet). CUM embodied_scale ends 2.13 > PER (R176 personal) 2.00 DESPITE a
          SHALLOWER tree (cum conn_depth 63 < per 69). pop 1000 both. world.gif = dense gold (deep) living 3D pop.
redteam:  CONFIRMED (skeptic, read code). byte-identical OFF (no path/RNG); driver genuinely LOCAL (nearest hearth
          within hearth_radius); struct_tech lossless max, untouched by culture_decay. THREE honest caveats below.
blocked:  none
caveat:   (1) driver≥personal is TRUE BY CONSTRUCTION (max(a,b)≥a); the load-bearing finding is the gap's MAGNITUDE
          + GROWTH (2.0→13.5), not its sign. (2) struct_tech is a lossless running-max per hearth LIFETIME, but a
          slot resets to founder tech on death+refound → not a globally death-proof monotone ratchet. (3) cross-arm
          "outclimbs" is divergent-RNG (cum body faster→diff pop→shallower tree); fair one-knob-at-construction, and
          cum body ends deeper DESPITE the shallower tree, which strengthens it. Single seed; KDTree rebuilt per-call (perf wart).
docrule:  README=description+deploy+block diagram ONLY (CEO R91); per-round catalog→progress.md; layout→CODEBASE_GUIDE.md;
          runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy). MEMORY: ONE sim at a time; full-stack world <200 MB; GL released.
next:     R178 LEAP (frontier 1/2): R177's banked driver STILL decelerates (its source, the frontier+builder mastery,
          asymptotes). Push for a driver that does NOT asymptote: (a) scale the body with an OPEN-ENDED COUNT (#
          distinct traditions / tree SIZE), which grows unbounded by construction, not the saturating depth; OR
          (b) pivot to Stage (3) cooperation/division-of-labour, seeded by R142 diet specialists + R177 banked culture. 禁止造假.
