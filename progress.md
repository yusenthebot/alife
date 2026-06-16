# alife — progress

## Current state (Round 1 complete — 2026-06-16)

Vectorized Boids flocking ecosystem foundation, built from zero in `~/alife`.
Clean isolated venv (`.venv`, numpy 2.4 / matplotlib 3.11 / pillow / imageio).

**What works (REAL-VERIFIED — eyes on frames + metrics, not just unit tests):**
- `alife/world.py` — toroidal world, minimum-image pairwise displacement, wrap/reflect.
- `alife/boids.py` — pure vectorized Reynolds step (sep/ali/coh), O(N²) numpy. ~25s for 650 boids × 420 steps incl. render.
- `alife/metrics.py` — order parameter (Vicsek φ), milling, mean NN distance, cluster count (union-find).
- `alife/render.py` — headless Pillow renderer: heading-hue triangles + fading motion trails.
- `alife/sim.py` — driver collecting per-step metric time series + frames.
- `scripts/run_boids.py` — emits flock.mp4 + key frames + metrics.csv + metrics.png.
- 14 pytest tests pass (emergence + invariants + metric units).
- **Verified run** (`runs/r1_demo`): φ 0.076 → 0.915; NN dist 3.81 → 2.76; clusters 1→2.
  Start frame = random rainbow scatter; end frame = coordinated colored streams. Confirmed by eye.

**What did NOT work / gotchas:**
- System matplotlib broken (numpy 1.x/2.x ABI clash) → solved with project venv.
- Sourced ROS2 `PYTHONPATH` leaks `launch_testing` pytest plugin (crashes on missing `yaml`)
  → always run via `scripts/test.sh` / `scripts/run.sh` which do `env -u PYTHONPATH`.

**Next-round seed (R2 — evolution):**
Add a per-individual **genome** (the boid weights + perception radii + speed become heritable
traits), **energy** (depletes with motion, replenished by feeding on food patches),
**reproduction** (split when energy high, offspring mutates), **death** (energy→0).
Selection then acts: fitter trait combos persist. Metric: trait distributions drifting over
generations + population dynamics. REAL-VERIFY: watch trait histograms evolve + render the
ecosystem. Keep `step` pure so the genome swap stays local.

## Frontier
- **Current ceiling:** hand-coded fixed-rule flocking; collective order emerges but nothing
  *evolves* yet — no heredity, no selection, no lifecycle.
- **Next frontiers (ambition × feasibility):**
  1. Evolution loop (genome→selection→reproduction) — high value, feasible now → R2.
  2. Neural-network brains (sensors→MLP→motor), weights evolved by GA — the "intelligence" payoff → R3.
  3. Predator–prey co-evolution — open-ended arms race → R4.
- **Fidelity/stack ladder:** numpy 2D (now) → spatial hashing / numba or C++ for N≫1k →
  torch MLP brains (CPU torch already present) → moderngl/3D ecosystem viewer.
- **Radical ideas weighed:** jump straight to 3D (deferred — verify evolution in 2D first,
  cheaper to watch); jump straight to RL (deferred — GA over evolved weights is the truer
  "natural selection" framing the goal asks for, RL is a later option).
