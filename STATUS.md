# STATUS — main
updated: 2026-06-20T29:00 · loop 156
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R156 ACHIEVED + red-teamed ROBUST: emergent DIVERGENT cultural TRADITIONS (cultural F_ST).
doing:    R156 DONE. R150-R155 measured ONE global culture frontier; a civilization needs MANY divergent
          traditions. R156 shows the EXISTING substrate already grows them: oblique transmission copies the
          NEAREST strong hearth (a spatial cultural store), so a region that climbs one BRANCH of the
          open-ended tree reinforces it locally -> spatially structured traditions. New metric tradition_test
          = Wright's F_ST over the boolean repertoire across a grid^3 of spatial demes. Causal NULL
          panmictic_culture: SAME learners (same nearest-hearth in-range gate) but copy a RANDOM global hearth
          -> the place<->tradition link is cut. panmictic=False byte-identical to R150. 133 genesis tests (+5).
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_traditions.py 500 (runs/r156_traditions/panel.png + tradition-coloured 3D
          traditions.gif EYE-VERIFIED). LOCAL F_ST > PANMICTIC on 2/2 seeds (mean 0.0262 vs 0.0188), distinct
          deme-dominant traditions 8 vs 5. F_ST-over-time: green local lines sit above grey panmictic.
redteam:  ROBUST (inline, refutation-first). (1) metric integrity: hand-built perfectly-divergent demes F_ST
          =1.0000, identical demes =0.0000. (2) POSITION-SHUFFLE null (3 seeds): LOCAL real 0.032 >> shuffle
          noise floor 0.007 (3/3) = GENUINE spatial structure not sampling noise; local>panmictic 3/3 (0.032
          vs 0.021). HONEST: magnitude modest (~4-5x noise floor); panmictic keeps a small residual structure
          (local reproduction is spatial) but local adds structure on top -> directional+causal claim holds.
blocked:  none
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife only, NOT torch/CUDA). MEMORY: ONE sim/pytest at a time; GENESIS is KD-tree + fixed-pool + bool repertoire (bounded, <100MB); close GL ctx (r.ctx.release()).
next:     R157 options (frontier): traditions are real but MODEST F_ST — deepen them. (a) lossy/decaying hearth
          records (union-accumulator never forgets -> homogenizes; add forgetting so local divergence sharpens
          into discrete cultures); (b) couple a tradition to a PAYOFF (different branches gate different food
          niches a la R155 -> traditions become economically distinct, not just neutral drift); (c) cultural
          phylogeny / cladistics across generations; (d) inter-group contact -> diffusion/replacement dynamics.
          See progress.md ## Frontier.
