# STATUS — main
updated: 2026-06-21T13:10 · loop 179
goal:     CEO DIRECTION (R140): build GENESIS — a persistent real 3D world that, just by running, freely develops
          toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied
          agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture.
          Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R179 CLEARED Stage (2) emergent signalling: the diagnosed fix for the R178 chicken-and-egg
          (within-lifetime Roth-Erev reinforcement, Skyrms 2010) WORKS. POSITIVE, red-teamed.
doing:    R179 DONE (POSITIVE). signal_learn=True (default-off byte-identical; requires signal_game=True): each agent
          carries two mutable Lewis URNS beside the frozen brain — SENDER (symbol|referent) + RECEIVER (guess|symbol)
          — sampled each step and reinforced +signal_lr on a correct decode. A shared convention bootstraps WITHIN a run.
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_r179.py → runs/r179_signal_learn/signal_learn.png EYE-VERIFIED (2s). LEARN (lr=0.4):
          decode_acc 0.49→0.86 monotone, MI(symbol;referent) z=114 (clears the scrambled null); CONTROL (lr=0, one
          knob) pinned at chance 0.51, z≈0. Red-team 3/3 seeds: LEARN acc 0.65–0.83 / z 55–69, control 0.44–0.54 / z≈0.
redteam:  two independent controls both refute the null — (a) signal_lr=0 one-knob (urns frozen = R178 = chance),
          (b) scrambled-label MI null. Degeneracy ruled out: symbols balanced ~50/50, so >0.65 acc on a balanced
          random referent is impossible by constant-guessing → genuine symbol↔referent encoding. Robust 3/3 seeds.
blocked:  none
caveats:  signalling here is within-life LEARNED (Roth-Erev urns, NOT inherited — reset uniform at birth, each gen
          re-learns), exactly Skyrms' mechanism, layered beside the NN genome. Convention strength varies by seed
          (0.65–0.83; some partial-pooling). Canonical 2-referent/2-symbol Lewis game (vocabulary scaling = future rung).
rootcause-resolved: R144/R145/R178 negatives all = "no within-lifetime learning"; R179 adds exactly that → emergence.
docrule:  README=description+deploy+block diagram ONLY (CEO R91); per-round catalog→progress.md; layout→CODEBASE_GUIDE.md;
          runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy). MEMORY: ONE sim at a time; featherweight numpy; GL released.
next:     R180 LEAP — Stage (2)→(3) bridge: now signalling is REAL, make it FUNCTIONAL — either (A) scale the Lewis
          game to a larger vocabulary / compositional referents (Kirby iterated-learning pressure), or (B) couple the
          learned channel to Stage-3 division-of-labour (signal a food/role need → coordinated foraging). Pick at ORIENT.
