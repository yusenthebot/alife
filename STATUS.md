# STATUS — main
updated: 2026-06-20T44:00 · loop 165
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R165 landed frontier (1): PHYLORATE / accelerating innovation dynamics on the unbounded space.
          Autocatalytic recombination on an OPEN combinatorial space gives SUPER-LINEAR (exponential) innovation.
doing:    R165 DONE. New alife/genesis/phylorate.py — the RATE law of cumulative innovation. Effort law E(N) on
          unbounded.TechSpace: additive null (fixed pool) SATURATES (decel); fixed-effort combinatorial LINEAR;
          AUTOCATALYTIC E(N)=max(base,alpha*N) on the OPEN space SUPER-LINEAR (exponential, multiplier 1+alpha).
          dN/dt-vs-N plane = mechanism-intrinsic discriminator (fall/flat/rise/rise-then-0). DECISIVE control:
          IDENTICAL alpha*N effort on a CAPPED space COLLAPSES (collision_frac->1, new->0) — super-linearity is
          the OPEN adjacent possible, NOT the multiplier. Non-tautological discovered part: collision_frac->1e-4
          on the open space (pair-space ~N^2 > discoveries ~N), so autocatalysis stays fed. 189 genesis tests (+7).
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_phylorate.py (runs/r165_phylorate/panel.png EYE-VERIFIED: crimson autocat+OPEN rockets
          up the log-y; rate-vs-N rises steeply; collision orange spikes to 1 while open stays ~0; accel bars crimson
          huge-positive vs orange negative). accel: additive -0.12 | fixed ~0.001 | autocat-OPEN +465 | capped -2.8.
redteam:  CONFIRMED (a)(b)(c)(d) independent agent, 4 seeds, recomputed collision from raw registry (max diff 0.0):
          exponential multiplier 1.4996≈1+alpha (R²=1.0); capped pins effort at alpha*K yet new->0 (mechanism≠
          multiplier); collision 0.40->0.0001 genuine. SHARPEST CAVEAT (baked into docstring): E(N)∝N is a MODELLING
          ASSUMPTION not emergent — the DISCOVERED content is the narrower "open space doesn't self-throttle"; it is
          EXPONENTIAL not power-law (growth_exponent rises with window, read only as ">1 = super-linear").
blocked:  none
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife only, NOT torch/CUDA). MEMORY: ONE sim/pytest at a time; phylorate.py = registry dict + Python ints (autocat keeps steps≤22 so N stays ~55k, <100MB); no GL.
next:     R166 frontier options: (1) embed unbounded.TechSpace into the LIVE GenesisWorld so the unbounded repertoire
          GATES physical action and is SELECTED (fixed-width rep matrices break on sparse repertoire — spike-then-
          migrate, gate on vr-lead). (2) ENDOGENOUS phylorate — make the alpha*N effort EMERGE from the live economy
          (more agents/energy from accumulated tech → more recombination) rather than be posited, closing the red-team
          caveat. (3) Stage-2 SIGNALLING redesign (synchronous lethal-predation arena). 禁止造假.
