# STATUS — main
updated: 2026-06-20T23:30 · loop 152
goal:     CEO DIRECTION (R140): build GENESIS — a persistent, real 3D world that, just by running (local/cloud), freely develops toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture. Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R152 HONEST NEGATIVE: coupling building to the caste does NOT flip R151's substitution into complement.
owns:     all of ~/alife (single session)
doing:    R152 DONE (honest negative). Tried to make Stages 3+4 COMPLEMENT — a builder caste maintaining the
          hearths a harvester caste eats from — by coupling building to the caste: convex build skill
          (deposit = build_gain·spec^gamma, only high-spec builds a real hearth) + a maintenance WAGE (reusing
          the R147 _pay_processors path; _build records struct_last_builder, _ripen_hearths credits it on
          food_proc, harvester eat pays the maintainer). Additive behind build_specialized (requires building
          AND specialize); default off = R148..R151 byte-identical. 99 genesis tests green (+6). REAL-VERIFY
          (scripts/run_genesis_complement.py; runs/r152_complement/panel.png + caste-coloured 3D complement.gif
          eye-verified): the builder caste did NOT re-emerge across THREE distinct regimes — food-rich: caste
          fully collapses (= R151); scarce+fast-decay (shown): viable world but only ~3% maintainer MINORITY
          (frac_build 0.03 vs SUBSTITUTE 0.00, shift +0.029 ≈ 0; spec_mean 0.13 vs 0.11, both harvester-dom);
          small-reach: whole world starves. FINDING: SUBSTITUTION is the robust attractor — shared/accretive/
          persistent infrastructure stays a near-public good a tiny minority supplies; coupling does not flip it
          (extends R151). 禁止造假. HONEST: WAGE-OFF kills the pop but is CONFOUNDED (wage = energy injection),
          not claimed as caste-load-bearing. Mechanism committed (default off) for a future EXCLUDABLE-infra
          redesign. COMMITTED; pushing.
blocked:  none
docrule:  README = description+deploy+block diagram ONLY (CEO R91); per-round catalog → progress.md; layout → CODEBASE_GUIDE.md; runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy alife only, NOT torch/CUDA). MEMORY: ONE sim/pytest at a time; GENESIS is KD-tree + fixed-pool + bool repertoire (bounded, <100MB); close GL ctx (r.ctx.release()).
next:     R153 default = COUPLE the tech tree to the 3D WORLD (make culture MATTER physically): techniques
          UNLOCK new world-actions (build types / food recipes / tools / speed) so cultural depth changes what
          agents DO, not just a harvest scalar. Alts: genuinely unbounded generative tech space (lift the
          max_techniques cap); EXCLUDABLE-infrastructure redesign to revisit the parked 3+4 complement;
          parked Stage-2 signalling substrate redesign. See progress.md ## Frontier + ## Decisions pending.
