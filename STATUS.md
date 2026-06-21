# STATUS — main
updated: 2026-06-21T12:05 · loop 178
goal:     CEO DIRECTION (R140): build GENESIS — a persistent real 3D world that, just by running, freely develops
          toward a CIVILIZATION via genuinely autonomous EVOLVED-NEURAL creatures (not scripts). Staged: 3D embodied
          agents → emergent language → cooperation/division-of-labour → building/economy → cumulative culture.
          Visually-checkable, genuine emergence, NEVER faked.
phase:    review — R178 attacked Stage (2) emergent signalling via DIRECT common interest (Skyrms/Lewis referential
          game), the hypothesis that R144/R145 failed only because alarm-call payoff is INDIRECT. HONEST NEGATIVE.
doing:    R178 DONE (honest negative). signal_game (default-off byte-identical, requires signalling=True): each step
          an agent observes a private referent BIT (new input), emits its utterance; nearest neighbour DECODES via a
          guess output (new output); correct decode pays BOTH +signal_reward. signal_game_mi() diagnostic added.
owns:     all of ~/alife (single session)
verify:   scripts/run_genesis_r178.py → runs/r178_signal_game/signal_game.png EYE-VERIFIED (~2s) + fast probes
          (strong-reward / small-dense / 1200-step). decode_acc PINNED AT CHANCE in BOTH arms (PAID max 0.537 vs
          FREE control reward=0 max 0.562 — indistinguishable); MI-vs-null = noise spiking >3 EQUALLY in both. The
          FREE control + scrambled null FALSIFY reward-driven emergence (no PAID>FREE asymmetry).
redteam:  the verify IS adversarial by construction — the FREE (reward=0) arm + scrambled-channel null are two
          independent controls and both refute the positive claim; the negative is robust, not a tuning artifact.
blocked:  none
rootcause: pure GENETIC evolution + SHIFTING partners can't break the encoder/decoder chicken-and-egg (random
          decoder scores 50% regardless of encoding → no selection gradient). 3rd Stage-2 negative (R144/R145/R178)
          → same gap: NO within-lifetime learning. Skyrms' fix = within-life reinforcement w/ stable roles.
docrule:  README=description+deploy+block diagram ONLY (CEO R91); per-round catalog→progress.md; layout→CODEBASE_GUIDE.md;
          runs/ GITIGNORED. run.sh ulimit -v 24GB (pure-numpy). MEMORY: ONE sim at a time; featherweight numpy; GL released.
next:     R179 LEAP (frontier A): ONE bounded attempt at WITHIN-LIFETIME signalling reinforcement (mutable per-agent
          signalling policy / Hebbian-Roth-Erev update on utterance+guess weights from the decode reward, repeated
          partner interaction) — the diagnosed fix for Lewis emergence. If it ALSO fails the FREE control, PIVOT
          cleanly to frontier B = Stage (3) division-of-labour (R142 specialists + R177 banked culture). 禁止造假.
