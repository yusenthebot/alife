# STATUS — main
updated: 2026-06-21T08:10 · loop 174
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R174 lands frontier (1)'s SUSTAINED-CLIMB rung: the unattended world now KEEPS DEVELOPING
          across many ticks (not just persists). R173's loop saturated in tick 1 (K=1000); R174 fixes the
          REGIME — large cap + gentler innovation + deeper diet/axes gates — so depth/breadth AND the embodied
          ceiling rise tick after tick, vs an identical CAPPED control that freezes once its tree fills.
doing:    R174 DONE. genesis/daemon.py: climb_curve (N real resumed ticks → per-tick frontier) + render_climb_
          panel (open-vs-capped 2×2). SUSTAINED regime _r174_cfg (max_techniques=20000, innov_steps=2,
          n_food_tiers=8, n_capabilities=4). scripts/genesis_daemon_tick.sh = the literal cron entrypoint.
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_r174.py → runs/r174_climb/{climb.png,world.gif} EYE-VERIFIED (~22s). 8 ticks×60
          steps as GENUINE separate subprocesses (true process death each tick). OPEN (K=20000): breadth
          133→4931 still climbing on the last tick, depth 5→12, diet 2→6, axes 1→4, pop 1000, tree.n=5011.
          CAPPED (K=250, only K differs): breadth FROZEN 244 (243→244→244), depth 6, diet 3, axes 2, pop 481.
          Open ends 20× past + strictly deeper. Cron entrypoint runs idempotent bootstrap→resume ticks. 221 tests (+2).
redteam:  CONFIRMED across seeds 0,1,2,3 — open keeps climbing (breadth →3703/7800/7343, depth 11/13/14, diet
          5/6/7) while capped freezes (239/197/88, depth 6/6/6, Δlast≤0) with a LIVING pop (≥200). The freeze
          is the CAP not pop death; the only knob that differs is K.
blocked:  none
caveat:   within the 8-tick horizon BREADTH climbs throughout; connected DEPTH (and the depth-gated diet/axes)
          climbs then PLATEAUS by ~tick 6 (depth 12) — random composition's max-depth growth decelerates and the
          body ceilings cap at the configured tier/axis count. "Keeps developing" = breadth open-ended + depth/
          body strictly past the frozen capped control. Sustaining DEPTH over many more ticks is R175.
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife). MEMORY: ONE sim at a time; full-stack world <200 MB; GL context released after render.
next:     R175 LEAP (frontier 1, sustained DEPTH): make connected DEPTH keep climbing over MANY ticks, not
          plateau by tick 6 — slow the deceleration (a depth-rewarding selection pressure so the deepest
          techniques are re-composed, or more tiers/axes so the body ceiling never maxes), and run the cron
          entrypoint for real wall-clock days. Alt: (2) long-horizon fixed-vs-generative BODY divergence; (3)
          Stage-2 signalling redesign (parked). 禁止造假.
