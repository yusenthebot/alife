# STATUS — main
updated: 2026-06-21T14:05 · loop 180
goal:     CEO DIRECTION (R140): build GENESIS — a persistent real 3D world that, just by running, freely develops
          toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied
          agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture.
          Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R180 BRIDGED Stage (2)→(3): the learned signal is now FUNCTIONAL — a DIVISION OF COGNITIVE
          LABOUR. POSITIVE, red-teamed.
doing:    R180 DONE (POSITIVE). signal_task=True (default-off byte-identical; requires signal_learn=True): a SHARED
          good-type g_t∈{0,1} FLIPS each step (non-stationary → communication is load-bearing); each slot is a SCOUT
          (observes g_t) or a BLIND FORAGER (g_t masked to 0). A forager learns the current good-type ONLY by decoding
          a scout's R179 urn signal; correct decode pays the foraging reward (real energy). Money shot: blind foragers
          TRACK the flipping world through scouts.
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_r180.py → runs/r180_signal_task/signal_task.png EYE-VERIFIED (13s, 3-panel). LEARN
          (lr=1.5) 3 seeds tail task_success 0.78/0.73/0.87 (mean 0.79); one-knob CONTROL (lr=0, urns frozen) 0.50;
          asymmetry +0.30. Panel B overlay: foragers' aggregate decode follows the true g_t step (functional tracking).
redteam:  the lr=0 control at 0.497 is the built-in null and refutes two ways at once — (a) g_t is balanced ~50/50 so
          a constant guesser scores 0.5 → 0.79 needs genuine symbol→g decoding (not constant-guessing); (b) the
          forager-blind mask holds (foragers carry zero g in input → only the decoded scout symbol informs them).
          Only scout→forager pairs count. Robust 3/3 seeds. Genuine asymmetric division of cognitive labour, not R179.
blocked:  none
caveats:  convention strength varies by seed (0.73–0.87, like R179's 0.65–0.83 spread); accuracy is capped below 1.0
          by the re-learning transient after each flip. 2-symbol/2-state Lewis game (vocabulary/compositional scaling
          = future rung). Payoff is the abstract foraging reward into energy, not a spatial harvest yet.
next:     R181 LEAP — options at ORIENT: (A) make the functional channel SPATIAL — scouts signal WHICH of N food
          patches is ripe → foragers move there (real harvest coupling, not abstract reward); (B) scale to a larger
          vocabulary / compositional referents (Kirby iterated-learning pressure); (C) Stage-3 proper: roles EVOLVE /
          specialise (who becomes a scout) rather than a fixed golden-ratio split. Pick the highest ambition×feasibility.
docrule:  README=description+deploy+block diagram ONLY (CEO R91); per-round catalog→progress.md; layout→CODEBASE_GUIDE.md;
          runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy). MEMORY: ONE sim at a time; featherweight numpy; GL released.
