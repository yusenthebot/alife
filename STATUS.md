# STATUS — main
updated: 2026-06-21T15:10 · loop 181
goal:     CEO DIRECTION (R140): build GENESIS — a persistent real 3D world that, just by running, freely develops
          toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied
          agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture.
          Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R181 made the Stage-2→3 signalling EMBODIED: the learned signal now drives REAL spatial harvest.
          POSITIVE, red-teamed (independent skeptic CONFIRMED via a scramble null).
doing:    R181 DONE (POSITIVE). signal_spatial=True (default-off byte-identical; requires signal_task): g_t now names
          WHICH of two fixed world PATCHES is ripe. SCOUTS march to the true ripe patch; BLIND FORAGERS march to the
          patch their DECODED scout-signal names; the foraging reward is EARNED BY PHYSICAL PRESENCE at the ripe patch
          (navigation), not a bare decode. Money shot: forager MASS tracks the flipping ripe patch IN SPACE.
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_r181.py → runs/r181_signal_spatial/signal_spatial.png EYE-VERIFIED (11s, 3-panel; panel
          B = forager x-density heatmap + cyan mean-x tracking the green ripe-patch step line). LEARN (lr=1.5) 3 seeds
          tail spatial_yield 0.69/0.67/0.60 (mean 0.66) vs one-knob CONTROL (lr=0, frozen urns) 0.25; asymmetry +0.40.
          task_flip=0.012 (physical transit needs time the abstract R180 decode did not).
redteam:  independent skeptic CONFIRMED (4 refutations + a decisive scramble null). (a) flocking IMPOSSIBLE — steering
          target = _patches[decoded symbol] only, no neighbour-position term; scramble keeps scouts 94% at ripe yet
          forager yield collapses 0.68→0.35. (b) no label leak — foragers' g_t input masked to 0, target = urn guess.
          (c) lr=0 is a clean one-knob (gates only the 2 Roth-Erev lines). (d) not settling — 0.66>0.5 (a settler) and
          control 0.25<0.5 (frozen urns thrash). Fresh seed=5=0.78 reproduces.
blocked:  none
caveats:  headline MEAN is seed-fragile (seed1=0.453; asymmetry-vs-control is robust EVERY seed — report mean-over-
          seeds, not a per-run figure). spatial_yield is TRANSIT-CAPPED (<1.0: a perfect decoder is mid-transit after
          each flip). The EMERGENT part is the symbol→patch MAPPING; locomotion is a hardwired go-to-target drive.
          2-patch/2-symbol binary. scramble residual 0.35>control 0.25 (residual decode ~0.60, minor non-collapse).
next:     R182 LEAP — options at ORIENT: (A) scale to N>2 patches / larger vocabulary (compositional referents, Kirby
          iterated-learning pressure) so the signal must carry >1 bit; (B) Stage-3 proper — roles EVOLVE/specialise
          (who becomes a scout is selected, not a fixed golden-ratio split, needs a scouting cost for an interior eq);
          (C) make locomotion EVOLVED not hardwired (the brain learns to act on the decoded symbol). Pick highest
          ambition×feasibility.
docrule:  README=description+deploy+block diagram ONLY (CEO R91); per-round catalog→progress.md; layout→CODEBASE_GUIDE.md;
          runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy). MEMORY: ONE sim at a time; featherweight numpy; GL released.
