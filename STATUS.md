# STATUS — main
updated: 2026-06-21T09:05 · loop 176
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R176 lands frontier (1)'s OPEN-ENDED-EMBODIMENT rung: the BODY now keeps deepening WITH the
          tech depth, not ceilinged. R175 caveat was the categorical body (diet 7 / axes 4) saturates by ~tick 1
          while connected DEPTH climbs. R176 adds depth_phenotype: max speed + harvest reach scale CONTINUOUSLY
          and unboundedly-by-form with realized cultural depth, so the body has no categorical ceiling.
doing:    R176 DONE. depth_phenotype makes _cap_speed/_cap_reach a continuous mapping speed=cfg.speed*(1+
          pheno_speed_gain*depth), reach=cfg.eat_radius*(1+pheno_reach_gain*depth); embodied_scale() reads the
          living-pop mean speed mult. Requires depth_gates. depth_phenotype=False is BYTE-IDENTICAL (no path, no RNG).
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_r176.py → runs/r176_body/{body.png,world.gif} EYE-VERIFIED (~31s). 8 ticks×50 steps
          as GENUINE separate subprocesses, K=20000. PHENO (gain=0.02): embodied_scale 1.09→2.00 monotone, STILL
          rising on the last tick; realized_axes FROZEN at 4 from tick 1 (categorical ceiling); conn_depth 20→69.
          CTRL (gain=0): embodied_scale FROZEN at 1.000 though conn_depth climbs 8→74. pop ~1000 both. world.gif =
          dense gold (deep) living 3D population. The continuous body actually moves bodies (off!=on in pos).
redteam:  CONFIRMED (skeptic, ran code+tests). Mechanism holds: continuous body genuinely affects physics
          (_cap_speed→_limit_speed clip; _cap_reach→harvest radius), OFF byte-identical (same RNG state), gain=0
          body frozen at 1.0 while depth climbs. 224 tests (+4). TWO HONEST CAVEATS recorded below.
blocked:  none
caveat:   (1) gain=0 "control" is NOT byte-identical one-knob isolation — gain changes physics→energy→birth/death→
          divergent RNG, so depth trajectories differ (ctrl 8,21,55..74 vs pheno 20,40..69). It STILL isolates the
          MAPPING (depth climbs to ~70 in BOTH while body_scale stays 1.0 at gain=0 → not a relabel/run-length).
          (2) embodied_scale is AFFINE in mean living depth, which empirically SATURATES (decel diffs, asymptote
          ~mean-tech 50). "Unbounded" is true of the FORM (no categorical clip, unlike axes), NOT the observed curve.
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife). MEMORY: ONE sim at a time; full-stack world <200 MB; GL context released after render.
next:     R177 LEAP (frontier 1/2): the body is now continuous but its DRIVER (mean depth) saturates — push for
          a body trait whose driver does NOT asymptote. Options: (a) heal the R175 breadth/depth tradeoff so the
          DEPTH driver itself keeps climbing unbounded (JOINT breadth×depth climb); (b) make embodiment scale with
          an OPEN-ENDED quantity (tree size / # distinct traditions) not the saturating mean depth; (c) Stage (2)
          emergent signalling, seeded by the R142 diet specialists — pivot off frontier 1 if its driver ceilings. 禁止造假.
