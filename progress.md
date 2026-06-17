# alife — progress

## Current state (Round 6 complete — 2026-06-16)

Added **recurrent (memory-capable) brains** to the toolkit and rigorously tested whether
evolved memory helps. Honest headline: across the memory tasks tried, **it did not robustly
beat a memoryless control** — a real, documented frontier difficulty, not a failure to report.

### Stack of rounds
- **R1** emergent Boids flocking. **R2** natural selection (genome/energy/repro/death).
- **R3** evolved NN foraging brains (generational GA, 13–22× held-out). **R4** predator–prey
  co-evolution arms race. **R5** continuous predator–prey ecology (two-species coexistence).
- **R6** recurrent brains + memory-task investigation. `brain.py` (RecurrentSpec), `memory.py`.

### R6 — what works (REAL-VERIFIED: tests + comparison run)
- `brain.py` — `RecurrentSpec` + `forward_recurrent`: a brain with a hidden state (W_hh) that
  persists across steps. Recurrence is real and tested (output depends on history; state evolves
  under constant input). Weights are the genome, evolved by the same GA.
- `memory.py` — two memory-task harnesses with a **clean controlled FF-vs-RNN comparison**
  (identical architecture; the only difference is whether hidden state persists or is wiped):
  - `forage_occluded` — food sensing periodically blacks out (must bridge gaps).
  - `nest_forage` — central-place foraging: carry food home to a nest visible only when near it
    (food forced far from nest → must leave home-sight and remember the way back).
  - `evolve_task` — generic GA over either task / either arm.
- `scripts/run_memory.py`; 58 tests pass.

### What did NOT work — the honest finding (this is the round's main result)
Evolved recurrent memory did **not** robustly outperform the memoryless control:
- **Occluded foraging:** memoryless WON (held-out ~51 vs ~38). Foraging is solvable by a
  history-independent **systematic sweep** that covers ground during blackouts — the task does
  not actually require memory, and the extra recurrent machinery just made the policy harder to evolve.
- **Central-place (nest) foraging**, the genuinely memory-requiring task, was highly
  **seed/parameter-dependent**: at one setting recurrent generalized +53% (held 13.2 vs 8.7);
  at others memoryless tied or won; with more GA power (pop 200, 60 gens, 3 seeds) the held-out
  means were ~equal (RNN 3.5 vs FF 3.9). In one seed memoryless got **0** (couldn't home) while
  recurrent got 6.3 — so memory CAN be decisive, but the GA does not reliably *discover* it.
- **Root cause (known in evo-robotics):** reactive policies are surprisingly powerful for
  foraging, and evolving genuine memory use (path integration) with a small GA on ~200 weights is
  a hard search. Not faked, not cherry-picked — reported as-is.

### Next-round seed (R7 — make memory pay, or pivot to 3D)
Two honest options:
1. **Earn the memory win:** a task where reactive policies provably fail — e.g. a discrete cue
   the agent must recall after it vanishes (delayed-response), or a curriculum (shrink nest-sense
   over generations) that scaffolds path integration; larger/CTRNN nets; novelty search to escape
   reactive local optima.
2. **Pivot to 3D** (the goal's stated summit): take the working R1–R5 stack (flocking → selection
   → evolved foraging brains → predator–prey ecology) into a real-time 3D renderer (moderngl
   offscreen / raylib), where the mesmerizing "watch it evolve" payoff lives. R6's recurrent
   brains remain available but are not on the 2D critical path.

## Frontier
- **Current ceiling:** rich 2D evolutionary ecosystem (selection, NN foraging, predator–prey
  coexistence); recurrent brains exist but memory advantage is unproven; still 2D.
- **Next frontiers (ambition × feasibility):**
  1. **3D ecosystem viewer** (moderngl/raylib offscreen) — the goal's summit, high payoff → R7.
  2. Make evolved memory pay (delayed-response task / curriculum / novelty search) → R7–R8.
  3. Speciation, spatial hashing / C++ for N≫2k; richer sensory (vision rays, communication).
- **Fidelity/stack ladder:** numpy 2D (now) → moderngl/raylib 3D → numba/C++ for scale.
- **Radical ideas weighed:** novelty/quality-diversity search to beat reactive local optima (R7);
  jump to 3D now (strong candidate — the visual summit the goal asks for); CTRNN continuous-time
  brains for better temporal dynamics (R7).
