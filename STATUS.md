# STATUS — main
updated: 2026-06-20T28:00 · loop 155
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R155 ACHIEVED + red-teamed ROBUST: costly/bounded culture-gated capabilities -> a DIVISION OF LABOUR.
owns:     all of ~/alife (single session)
doing:    R155 DONE. R154's capabilities were FREE -> transmission converged the whole population to the full
          vector (no specialization). R155 makes each capability EXCLUDABLE + BOUNDED: each tech node = the
          exclusive harvesting KEY to one parallel food NICHE (cap_niches), a somatic BUDGET (cap_budget=1)
          caps keys held -> must specialize, newborns keep the PARENT's key first (heritable). Resource
          depletion -> negative frequency dependence -> a STABLE balanced polymorphism of capability profiles
          = a division of labour THROUGH the tech tree (attacks the R152 public-good negative from the
          EXCLUDABLE door). cap_niches=False byte-identical to R154. 128 genesis tests green (+10).
verify:   scripts/run_genesis_specialize.py 900 900 (runs/r155_specialize/panel.png + profile-coloured 3D
          specialize.gif EYE-VERIFIED: blue niche-0 + orange niche-1 specialists ~50/50 intermixed, two
          coexisting castes not one converged phenotype). MIXED frac_per_key [0.52,0.48], profile_entropy
          1.00 (max for 2 profiles), balance 0.98, mean_keys 1.00 (budget binds). Mono collapses toward
          extinction (24, frac_keyed 1.0 -> NOT key erosion, genuine niche-wastage). FREQ-DEP SELECTION: real
          niches erase a 0.9/0.1 seed (gap 0.04) where INERT keys (niche_free_frac=1) drift (gap 0.63).
redteam:  ROBUST (independent agent). Claim1 CONFIRMED 5 seeds; Claim3 CONFIRMED (neutral-control decider =
          selection not drift); Claim2 direction CONFIRMED & genuine (mono keeps keys, recovers on free food
          -> niche-wastage, not a force_mono artifact) but MAGNITUDE is cap-bound (mixed rides cap) -> stated
          as "mono driven toward extinction", NOT a fixed Nx. No integrity bugs. 禁止造假.
blocked:  none
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife only, NOT torch/CUDA). MEMORY: ONE sim/pytest at a time; GENESIS is KD-tree + fixed-pool + bool repertoire (bounded, <100MB); close GL ctx (r.ctx.release()).
next:     R156 default = NAIVE bootstrap of the deep capability keys (R155 demonstrated the DYNAMICS via seeded
          keys; an isolated deep node has no intermediate gradient -> didn't bootstrap from naive in 900 steps,
          same bootstrap-deadlock lesson as Stage 2). Give the keys a graded acquisition ladder OR make the
          niche payoff reward partial depth. Alts: >2 niches (richer caste structure); couple capability
          specialization to BUILDING (builder vs forager caste via excludable tools); unbounded generative
          tech space. See progress.md ## Frontier.
