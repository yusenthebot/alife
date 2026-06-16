# alife — progress

## Current state (Round 2 complete — 2026-06-16)

Evolving artificial-life ecosystem in `~/alife`. Boids flocking (R1) now sits on top of a
full **evolutionary lifecycle**: genome → energy → feeding → reproduction → death → selection.

**What works (REAL-VERIFIED — eyes on frames + trajectories + histograms, plus an adversarial skeptic pass):**
- `alife/genome.py` — 7 heritable traits (perception, w_sep/ali/coh, w_food, max_speed, metabolism), random + gaussian mutate, bounded.
- `alife/ecosystem.py` — `Ecosystem` with dynamic population: per-genome movement (R1 rules + heritable food-attraction), metabolic energy cost, eating food, energy-split reproduction with mutation, starvation/age death, food regrowth. Pure-ish step; arrays grow/shrink each tick.
- `alife/world.py` — added `delta_to` (toroidal cross-set distance, agents↔food).
- `alife/render.py` — `eco_frame`: food motes + creatures hued by a heritable trait (food-attraction), so selection is visible as the color mix shifting.
- `scripts/run_evolution.py` — emits evolution.mp4 + key frames + population.png + traits.png + trait_hist.png + csv.
- 25 pytest tests pass (R1 14 + genome 4 + ecosystem 7, incl. a directional-selection test).

**Verified run** (`runs/r2_evo`, 2400 steps): pop 260→1400, births 2426 / deaths 1286, max gen 14.
Directional selection (mean trait, initial→final): w_food 1.90→3.12↑, max_speed 2.54→3.28↑,
metabolism 1.21→0.69↓, w_coh 1.45→0.37↓↓, w_ali 1.48→0.77↓; **w_sep 1.44→1.40 = flat drift control.**
perception evolved an intermediate peak = stabilizing selection. Frames: start = sparse rainbow,
end = dense + warm-shifted (food-seekers won). The population *discovered flocking is costly* under
food competition and selected it away — emergent, not coded.

**Hardening (the verify moat):**
- Adversarial skeptic pass (3 lenses, `scripts/review_r2.workflow.js`) — all returned refuted=FALSE:
  code (0.96, no bug fakes it; clip bias is *downward*, opposing the rise), stats (0.78, drift ruled
  out — 38–45σ vs drift expectation, r(w_ali,w_coh)=0.998 selection signature), fake (0.97, indep
  re-run reproduces it, no hardcoding). False alarms (energy double-count, cull indices) all dismissed.
- Replicates (`scripts/replicates.py`, `runs/r2_replicates`, 6 seeds): w_food ↑ in **6/6**, metabolism
  ↓ in **6/6**; w_sep (near-neutral control) moves ~¼ as much. "Could be luck" resolved.
- Honest caveats carried to R3: w_food/max_speed/metabolism pile at trait bounds (widen / add cost);
  w_sep is the only near-neutral trait (w_ali/w_coh are genuinely selected against, not controls).

**What did NOT work / gotchas:**
- Same venv + `env -u PYTHONPATH` discipline as R1 (use scripts/test.sh, scripts/run.sh).
- Population currently saturates at the hard `pop_cap` (1400), not a food-set carrying capacity —
  ecology is food-limited (standing food ~15) but the cap is the binding constraint. Fine for R2;
  for richer boom-bust dynamics, lower food or raise costs so ecology caps below the hard cap.
- max_speed pins to the upper bound and metabolism near the lower bound — selection wants to push
  past the trait bounds (physical constraints). Expected.

**Next-round seed (R3 — neural-network brains):**
Replace the hand-coded steering rules with a small **evolved neural network brain** per creature:
sensory inputs (nearest-food direction/distance, neighbor density/heading, own energy, maybe a
small retina of ray-cast sensors) → MLP (weights ARE the genome) → motor output (turn + thrust).
No backprop — weights evolve by the same GA (mutation + selection). Goal: behavior (foraging,
avoidance, flocking-or-not) should EMERGE from evolved weights, not from rules. Keep ecology +
energy + reproduction; swap only the controller. REAL-VERIFY: brains evolve competent foraging
from random nets; watch behavior improve across generations + render it.

## Frontier
- **Current ceiling:** evolution works, but behavior is still hand-coded rules with evolved
  *weights on fixed rules*. The creatures don't have brains — they can't learn qualitatively new
  behaviors, only retune the 7 knobs.
- **Next frontiers (ambition × feasibility):**
  1. Evolved NN brains (sensors→MLP→motors), GA over weights — the "intelligence" payoff → R3.
  2. Predator–prey co-evolution (two species, an arms race) → R4.
  3. Speciation / niches; spatial scaling (spatial hash / numba / C++) for N≫1400 → R4–R5.
  4. 3D ecosystem viewer (moderngl/raylib) — deferred until brains + co-evolution proven in 2D.
- **Fidelity/stack ladder:** numpy 2D O(N²) (now) → spatial hashing / numba / C++ for big N →
  torch or hand-rolled numpy MLP brains (CPU torch present) → moderngl/3D.
- **Radical ideas weighed:** jump to RL (deferred — GA over weights is the truer "natural
  selection" framing the goal asks for; RL is a later alternative). Jump to 3D now (deferred —
  cheaper to evolve & watch in 2D first). Continuous/CTRNN brains vs feedforward (consider in R3).
