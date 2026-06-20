# alife — progress

## Current state (Round 150 — 2026-06-20) — GENESIS Stage 5 made OPEN-ENDED: COMBINATORIAL culture (the tech tree that lifts R149's finite ceiling)

**R150 lifts R149's one acknowledged caveat — its scalar `tech` ratchets to a FINITE fixed point
~innov/(1-fidelity) (cumulative but not open-ended) — by replacing the scalar with a discrete combinatorial
tech tree, and the open-ended climb is verified + red-teamed.** New module `alife/genesis/combinatorial.py`
(pure array functions) + additive wiring in `genesis.py` behind `combinatorial=True` (requires culture=True;
`combinatorial=False` is R149 byte-identical, guarded by a test). The mechanism (Kauffman's "adjacent
possible" / Arthur's combinatorial evolution of technology):
- a fixed tech TREE: technique k>=n_seed_tech has two DETERMINISTIC prerequisites (`build_tech_tree`, fixed
  `TREE_SEED` → identical across sim seeds); level(k)=1+max(level of prereqs);
- a technique is DISCOVERABLE only once BOTH its prerequisites are known → the set of reachable techniques
  (the adjacent possible) GROWS with the repertoire → discovery ACCELERATES (ideas-beget-ideas) → no
  dynamical fixed point (open-ended; the only bound is the deliberate `max_techniques` cap);
- each agent carries a boolean REPERTOIRE (World-owned `self.rep` [capacity, K], bounded mem); a newborn
  inherits by social learning (`copy_with_fidelity`: copy parent ∪ nearest-strong-hearth record, each bit kept
  w.p. `culture_fidelity`) then makes `innov_steps` discoveries from its adjacent possible (`discover_inplace`);
- `tech` (the harvest payoff, unchanged path) = the deepest LEVEL known (`max_level_known`) → mastery is
  selected; hearths ACCUMULATE the union of builders' repertoires (`np.bitwise_or.at`) = the open-ended
  cultural store. Checkpoint round-trips `rep`/`struct_rep`. 13 new tests (90 genesis tests green).

**REAL-VERIFY (`scripts/run_genesis_combinatorial.py`; level-coloured 3D GIF + 2-seed combinatorial/asocial/
R149-scalar controls; `runs/r150_combinatorial/panel.png` + `combinatorial.gif` eye-verified):**
- **OPEN-ENDED CLIMB** — living-population distinct techniques (`pop_distinct`) climb 8→**1040** (130x the
  asocial floor of 8), and the per-window discovery RATE **RISES 63→120** (accelerating = the open-ended
  signature), with the frontier (deepest tech-tree level) climbing **0→13**. Final 1040 << 8000 cap → not
  pool-filling.
- **REQUIRES TRANSMISSION** — asocial (`learn=False`) sustains a living reproducing population (→~2200, gen
  7.8) yet flatlines at **8 distinct / level 0 forever** (one lifetime from an empty repertoire reaches only
  seed primitives) → cumulative culture is impossible alone; this is the acid test.
- **LIFTS R149's CEILING** — the R149 scalar ratchet (`combinatorial=False`) DECELERATES, its technique RATE
  falling **1.52→0.68** toward a finite fixed point, while R150's rate rises. Tree depth is a TUNABLE design
  parameter (max depth **21/25/28/31** at cap 2k/4k/8k/16k), NOT a dynamical attractor → genuinely open-ended.

**RED-TEAM (mandatory; general-purpose agent, independent probes; 禁止造假 — all CONFIRMED):** (1) the
**population-growth confound is RULED OUT** — restricting to windows where population is FIXED at the 6000 cap,
the discovery rate still rises (seed0 84.6→93.8, seed1 176.4→204.0/window), so the acceleration is intrinsic to
combinatorial discovery, not the 900→6000 ramp. (2) `pop_distinct` is the union over LIVING slots only (339 ==
manual living-union; dead-slot union 0 — no slot-reuse leak; newborns full-overwrite their row). (3) asocial is
a fair control (only transmission removed; population alive). (4) same seed+config twice → byte-identical
pop_distinct; tech tree depends only on TREE_SEED, not the sim seed. (5) the count-vs-scalar framing is
legitimate — the falsifiable signal is the unit-independent RATE DIRECTION (rises vs falls), and the
apples-to-apples frontier-LEVEL comparison (R150 keeps deepening, R149 plateaus) is in the panel too.
**This is a genuine open-ended combinatorial culture, not theatre.** Substrate committed + reusable.

### Round 147 — GENESIS Stage 3: DIVISION OF LABOUR ACHIEVED (convex specialization trade-off → caste)

**R147 fixed R146's honest negative and Stage 3 is now POSITIVE: a heritable processor/harvester CASTE
emerges, the two roles are played by genetically distinct castes, and the specialised economy out-produces a
forced-generalist one.** R146 diagnosed exactly why DoL failed — processing was cheap and non-exclusive, so a
generalist doing both was optimal (no specialization trade-off). R147 supplies the missing ingredient: a
heritable caste trait `spec ∈ [0,1]` (0=harvester, 1=processor) with **CONVEX (accelerating) returns to
specialization**, all additive to `alife/genesis/` (`specialize=False` → R146 byte-identical, 50 genesis tests
green incl. determinism + the byte-identical guard):
- **harvest gain = `food_value * (1-spec)^spec_gamma`** (only pure harvesters eat at full value);
- **process reach = `process_radius * spec`** → ripened volume ~`spec³`, strongly convex output;
- a processor earns a **WAGE** (`process_payment`) when a HARVESTER eats a mote IT ripened (per-mote
  attribution via `food_proc`) — so **processors live on wages, harvesters on food = genuine producer/consumer
  interdependence (trade)**, not a free public good;
- crucially **`spec` is NOT a brain input** — the brain's process-gate decision can't read its own caste, so
  any role↔caste alignment must be **built by selection** (genetic linkage), which is the emergence signal.

**The caste regime (found empirically): `spec_gamma=4, process_payment=18, process_cost=1.0`.** At the
shallower `gamma=2` generalists still win (the population collapses to one intermediate `spec≈0.42`, bimodality
DROPS below the founding uniform, processors≈harvesters) — convexity must be **steep** so an intermediate is bad
at BOTH tasks and disruptive selection splits the population. (`spec_gamma`/`process_payment` are the new
`GenesisConfig` defaults for the specialize path; R146/earlier untouched; the runner passes `process_cost=1.0`.)

**REAL-VERIFY (`scripts/run_genesis_caste.py`; 5000-step spec-coloured 3D GIF + 5-seed evolve/frozen/
force-generalist controls; `runs/r147_caste/panel.png` + `caste.gif` eye-verified):**
- **DIFFERENTIATION** — `spec` settles into a clean **BIMODAL** distribution (two modes at 0 and 1, near-empty
  middle; Sarle BC **0.90**), and the **caste-GAP `proc_spec − harv_spec` RISES 0 → +0.32 over the run**
  (evolution aligns the heritable caste with the behavioural role) vs **~0 for a frozen genome** (frozen is also
  bimodal — gamma=4 disruptive selection on standing variation — but its castes do NOT preferentially process/
  harvest: gap mean ~0, scattering +0.25/−0.05/−0.08/+0.25/−0.28 across seeds).
- **PRODUCTIVITY** — **evolve pop 2451 > frozen > force-generalist 1753** (≈1.4×). Evolve beating *frozen*
  (both specialised/bimodal) shows the evolved **alignment** itself adds productivity, not just specialization
  — this defuses the "convexity makes the productivity comparison circular" objection.

**RED-TEAM (mandatory; 禁止造假 — all passed):** (1) **5/5 seeds** positive caste-gap (+0.27,+0.47,+0.23,+0.43,
+0.28) with evolve>frozen>forcegen population each seed — not a single-seed fluke (unlike R146's killed clonal-
deme 8×). (2) **Castes are SPATIALLY INTERMIXED** — nearest-neighbour same-caste 0.54 ≈ random-mix expectation
0.51, so processors and harvesters live side by side and interact (real division of labour), NOT segregated into
separate regions (which would make it R142-style niche partitioning, not DoL). (3) **Interdependence confirmed**
— a flowing public good (~61 ripe / ~60 raw at any instant) with harvesters within sense range of processor-
ripened food. The GIF visually confirms orange (processor) and teal (harvester) agents thoroughly mixed through
the 3D volume. **This is a genuine emergent division of labour, not theatre.** Substrate committed + reusable
(caste trait, wage attribution, convex efficiency, bimodality/caste_test read-outs).

### R146 (previous round) — GENESIS Stage 3: division of labour, attempt 1 (public-goods processing) — HONEST NEGATIVE

**R146 pivoted to Stage 3 (cooperation / division of labour) and built a two-stage food ECONOMY on the
genesis substrate — a working new layer, but the division-of-labour claim it was meant to produce did NOT
emerge.** Mechanism (all additive to `alife/genesis/`, `processing=False` → R141..R145 byte-identical,
40 genesis tests green incl. determinism + checkpoint guards):
- food spawns **RAW (inedible)**; an evolved **PROCESS output** ripens every raw mote within `process_radius`
  into **edible (ripe)** food, paying `process_cost` — ripe food is a **local PUBLIC GOOD** any neighbour can
  harvest, and **decays back to raw** after `ripe_ttl` (a continuous FLOW, not a stock);
- prey gain a **nearest-RAW-food sense channel** (n_in +4) so they can navigate to processing sites, and a
  process-gate output (n_out +1); a `scramble_allocation` ablation replaces the evolved gate with a Bernoulli
  draw at the same mean rate (identical processing BUDGET, allocation conditioning destroyed);
- an in-situ `process_allocation_test` reads corr(process-decision, local ripe proximity) — a **negative**
  value would be the response-threshold DoL signature (process when ripe scarce, harvest when abundant).

**REAL-VERIFY (founders=0 full diversity, 7000-step role-coloured 3D GIF + 2-seed evolve/frozen/scramble
controls; `runs/r146_labor/panel.png` eye-verified):** the economy **WORKS robustly** — population sustains
**~2300 across all 4 seeds**, the processing→ripe→harvest flow closes (high-throughput, low standing ripe
stock). But **NO division of labour emerged:** corr(process, ripe-prox) sits at **~+0.2 for BOTH evolve and
frozen** (incidental — agents process where food is generally dense; this is the OPPOSITE sign of need-based
allocation, which would be negative), and **evolve pop 2279 ≈ scramble 2288** (no productivity gain from
allocation), **evolve ≈ frozen** generally (ratio ~1.0). The `frac_processing` settles ~0.22 — a population
average consistent with **generalist time-sharing, not a differentiated processor/harvester caste**.

**RED-TEAM did its job (禁止造假).** A clonal-deme variant (`n_founder_genomes=8`, intended to give kin
selection a foothold) showed a tempting **8× evolve-vs-frozen population gap on seed 0** — but red-teaming
across 4 seeds revealed **3 of 4 go EXTINCT** (with only 8 founder genomes the bootstrap starves if none is a
competent processor); the 8× was a **single-seed bootstrap fluke, not division of labour**, and was rejected.

**Diagnosis (the real finding):** generalists are optimal here because processing is **cheap and
non-exclusive** — an agent can freely process *and* harvest, so there is **no specialization trade-off** and
the strong public good is forgiving enough that even random brains sustain the population (hence evolve ≈
frozen, nothing to select for). Raising `process_cost` does NOT induce allocation — it just causes extinction
(cost ≥ 6 → pop 0). Genuine division of labour needs a **specialization trade-off with CONVEX (accelerating)
returns** (a caste: doing both strictly worse than a mix of specialists), not merely a shared public good.
This is the principled next mechanism (R147). The processing substrate is committed and reusable. See
`## Decisions pending` and `## Frontier`.

### R145 (previous round) — GENESIS Stage 2: kin-selection attempt at signalling — SECOND honest negative (relatedness ≠ the missing piece)

**R145 tested the decisive hypothesis from R144's diagnosis — that genuine alarm signalling failed for lack
of RELATEDNESS — and the same four-control protocol REFUTED it.** R144's negative was traced to ~zero
relatedness (n0 distinct founder genomes mix freely, so warning a neighbour helps a stranger; Floreano &
Mitri 2009: communication evolves under HIGH relatedness, collapses without). R145 supplies exactly the
missing kin-selection machinery, all additive (`alife/genesis/`, defaults off → R141..R144 byte-identical,
32 genesis tests green incl. determinism guards):
- **clonal founder demes** (`n_founder_genomes>0`): G genomes, each cloned into a tight spatial cluster
  sharing one lineage, so a prey's nearest neighbour is its clone and warning it propagates the caller's OWN
  genes (Hamilton rb>c). A `neighbour_relatedness` instrument confirms it took.
- a **stronger informational asymmetry** (`prey_pred_range=8` ≪ `sense_range=32` — a neighbour closer to
  the predator can warn earlier), and a small **honest-signalling emit cost** so silence is the default.

**REAL-VERIFY (2 seeds × 3 conditions × 12000 steps = 369 s foreground; panel.png + utterance-coloured 3D
GIF eye-verified):** the kin manipulation clearly took — **mean nearest-neighbour relatedness 0.90** (vs ~0
in R144) — and yet alarm signalling **STILL did not emerge**, all four controls failing across both seeds:
evolved MI **0.0016** < **frozen 0.0047** (sensory-reaction artifact, not meaning) ≈ null 0.0010; HEAR pop
1980 vs DEAF 2019 (**ratio 0.98 → no survival benefit**); causal flee intact 0.151 < deaf 0.206 (**no
adaptive listening**); MI-over-time bounces around the null with no climb. **This is a real scientific
finding, not a tuning failure: relatedness was high (0.90) and emergence still did not happen — so
relatedness is necessary-but-NOT-sufficient here.** Two independent negatives (R144 no-kin, R145 high-kin)
now agree. 4 new tests (813 total). 禁止造假: the protocol again declined to fake a positive.

**Diagnosis → why even kin selection wasn't enough (the bootstrap is the real wall):** with random brains
the emitted utterance carries ~null information about danger (frozen MI ≈ evolved MI ≈ 0), so receivers have
nothing honest to listen to; with no honest signal, listening has no survival gradient (hear≈deaf); with no
listening, honest emission has no payoff — a chicken-and-egg deadlock that high relatedness alone does not
break, because the marginal per-prey benefit of one neighbour's alarm is swamped by the noise of individual
foraging/evasion outcomes. Breaking it likely needs a far sharper selective event structure (e.g. discrete
synchronous predation "rounds" where a missed warning is reliably lethal and a heeded one reliably saves —
the Floreano/Mitri foraging-arena design), which is a substrate change, not another parameter sweep.

**DECISION (anti-thrash): PIVOT.** Two principled signalling attempts with different mechanisms have both
returned clean negatives; a third parameter variation would be thrash. Per the loop's anti-thrash rule,
**R146 pivots to Stage 3 — cooperation / division of labour**, seeded by the R142 diet specialists that
already coexist. The signalling rung is logged honestly below for a future substrate-level redesign, not
abandoned. See `## Decisions pending`.

### R144 signalling substrate (previous round)

**R144 built the Stage-2 SIGNALLING substrate + the four-control emergence protocol** (scrambled null ·
frozen-genome control · causal lesion · intact-vs-deaf survival). Each prey emits an evolved scalar
utterance and hears its nearest neighbour's, over the kin-adjacency. `signalling=False` is byte-identical to
R143. REAL-VERIFY (3 seeds × 8000 steps): HONEST NEGATIVE — evolved MI 0.0037 ≤ frozen 0.0152 (artifact),
HEAR/DEAF pop ratio 0.96 (no benefit), causal flee intact≈deaf (no listening). The protocol caught the
artifact (禁止造假). Diagnosed as a relatedness problem → motivated R145's kin-selection test (which refuted it).

### R143 arms race (previous round)

**R143 added a co-evolutionary PREDATOR** — a second evolved-neural species that hunts the prey. Prey gain
a predator-sense channel (brain n_in 9→13) and evolve **EVASION**. Additive; `n_predators0=0` is the exact
R141/R142 prey-only world (byte-identical). REAL-VERIFY (16k-step run, 3D): a living predator-prey ecology
with **boom-bust cycles** (prey & predators oscillating out of phase), **coexisting 3/3 seeds (no
extinction)**; prey flee-directedness evolves — windowed **+0.231 evolve vs +0.090 frozen** (every seed
evolve>frozen, ~2.5×); foraging still evolves under predation. 4 new tests (800 total). Stage 1 of the
GENESIS ladder (foundation → niches → arms race) is now complete: a persistent 3D world that evolves,
sustains diverse coexisting strategies, and stays alive/receding under predation.

**HONEST notes:** (1) coexistence is a **knife-edge** — predator cap 1200 → prey go extinct
(overexploitation crash); cap 350 → predators go extinct (out-evolved by evasive prey); cap **550** (~0.2×
prey, predprey3d's ratio) coexists. (2) The arms race is **one-sided in practice**: predators pin at their
cap during prey-rich phases so predator-pursuit selection is weak (the project's known R34 limit) — prey
evasion clearly evolves, a clean *symmetric* two-sided escalation does not. (3) GIF prey/predator colour
contrast is subtle (prey lineage colours drift reddish) — a future render tweak.

### R142 niches (previous round)

**R142 broke the R141 monoculture** with resource partitioning. R141's foundation evolved foraging skill
but swept to a MONOCULTURE (one strategy). R142 adds `n_food_types` food types + a heritable **diet** trait:
each agent senses/eats only its own type (the trade-off), so distinct food types support distinct specialist
lineages — coexisting ecological niches (Gause's competitive-exclusion principle). All additive to
`alife/genesis/`; `n_food_types=1` is byte-identical to R141 (no extra RNG draws, R141 tests/determinism intact).

**REAL-VERIFY:** a 16k-step K=3 run rendered in **real 3D, agents coloured by diet** (GIF eye-verified:
**red + green + blue specialists coexist** throughout the volume — three foraging niches living side by
side, vs R141's single converged colour). **Diet diversity locks at 3.00** the whole run; foraging
directedness still **evolves to +0.106**; lineage diversity ~**1.9** (≈2× the monoculture). RED-TEAM
across **3 seeds**: K=1 diet-diversity **1.00 / 1.00 / 1.00** (monoculture) vs K=3 **3.00 / 3.00 / 3.00**
(three persistent niches) — a flat, clean separation. 4 new tests (796 total). This also seeds Stage-3
division of labour (specialists already coexist).

**HONEST negative (recorded, not hidden):** the FIRST R142 attempt — spatial food **patchiness** (clumped
food, `food_mode="patches"`) — did NOT break the monoculture (diversity still collapsed to 1.0) AND broke
the directedness readout (clumped food → agents sit in clumps, no directed steering). Identical patches +
free migration still let one lineage sweep all of them. Patches remain an orthogonal option (useful later
for niche construction) but the diversity win came from resource partitioning, not spatial structure.

### R141 GENESIS foundation (previous round)

R141 shipped the foundation: a persistent 3D world, evolved-neural agents, in-situ food-scarcity selection,
kin-adjacent reproduction, fixed body, checkpoint/resume. REAL-VERIFY: foraging directedness evolved
0→**+0.166**, food-limited pop ~2400, 65 generations; red-team 3 seeds evolve +0.170/+0.153/+0.211 vs frozen
+0.063/+0.104/+0.078 (all positive); 3D GIF eye-verified. The monoculture sweep it exposed is what R142 fixed.

### R140 review (previous round)

R140 was a milestone REVIEW round at 130 modules / 781 tests: **781 passed, 0 failed** (14m57s); every
R131–R139 headline adversarially re-verified on **fresh unseen seeds** (17/17 survived); milestone gallery
eye-verified; de-slopped (5 stale gallery stubs + an old workflow deleted, 5 dead `if False` branches fixed);
docs current (130 / 781, README trimmed to CEO-R91); architecture audited HEALTHY. Honest correction: the
wolf-sheep predator-LAG-SIGN test was not seed-robust → rewritten to the robust boom-bust CV signature.

### R139 details

R139 added dendritic solidification (`alife/dendrite.py`): a snowflake crystal grows from an undercooled
melt. Freeze a pure liquid below its melting point and the crystal does not grow as a smooth ball — it
throws out sharp branching arms (the shape inside every snowflake and most cast metals). Modelled with
the Kobayashi (1993) phase field: a phase p (1=solid, 0=liquid) couples to a temperature T; the gradient-
energy coefficient ε(θ)=ε̄(1+δ cos(j(θ-θ0))) depends on the interface-normal angle (this is the lattice
ANISOTROPY), and latent heat K·∂p/∂t reheats the surrounding melt. Two physical ingredients combine: the
Mullins-Sekerka tip instability (a protruding tip sheds its latent heat faster, stays colder, grows
faster — runaway sharpening) and the anisotropy (which pins the runaway to j preferred directions). The
result, eye- and data-checked: a six-fold ice dendrite and a four-fold cubic-metal dendrite, with side
branches when interface noise is added, and a clear latent-heat HALO of warm melt around the crystal.
Quantitatively the number of primary arms equals the anisotropy mode j (measured from the angular Fourier
spectrum of the tip-radius profile: j=4→4, j=6→6 — the measured count equals the set parameter), and the
anisotropy DRIVES the growth (with δ=0.04 the solid fraction reaches 0.40 vs 0.10 for δ=0). Honest: these
are relatively "fat" dendrites, not ultra-fine needles; the square-grid Laplacian is not perfectly
isotropic, so the δ=0 case and j≥8 show a spurious grid 4-fold (I claim only j=4 and j=6, the physical
cases); the equation signs were validated empirically against a saved probe image. Genuinely distinct in
mechanism from snowflake.py (Reiter's hexagonal vapour-CA, a discrete rule) and dla.py (random-walk
aggregation) — this is a continuum PDE with real latent-heat coupling and tunable anisotropy, and it
retires the deferred dendrite frontier. VISUAL: six-fold + four-fold + side-branched crystals + the
temperature halo + arm-count=j bars + growth-vs-anisotropy curve + a 35-frame growth GIF.

### R138 details

R138 added Turing patterns on a sphere (`alife/turingsphere.py`): how an animal gets its spots on a
curved, CLOSED body rather than a flat sheet. The Gray-Scott reaction-diffusion system runs on the
surface of a sphere, represented as an icosphere mesh (an icosahedron subdivided n times and projected to
the unit sphere — this avoids the lat-lon coordinate-pole singularity and gives near-uniform resolution).
Diffusion is the random-walk graph Laplacian (Lap u = mean(neighbours) − u), whose eigenvalues lie in
[−2, 0] so the standard explicit Gray-Scott step is stable, and which conserves constants exactly
(|L·1| < 1e-16). The same chemistry that spots a plane spots the ball — three eyeball-distinct coat
regimes by (F,k): isolated SPOTS (a leopard ball, ~41 spots), a LABYRINTH, and a CORAL maze. The fresh,
sphere-specific result is that the CLOSED geometry quantises the pattern: with no boundary the spots must
wrap around and join up, and their number is set by the ratio of sphere size to the intrinsic Turing
wavelength — refine the mesh (a larger sphere in wavelength units) and the spot count climbs 0 → 18 → 41
across subdiv 3/4/5, roughly ∝ area/λ². Honest: the spot-count metric is only meaningful in the isolated-
spots regime (the size-law panel uses that; the labyrinth/coral are connected and not counted as spots),
and the graph Laplacian approximates the Laplace-Beltrami operator — I claim the qualitative pattern and
the size-scaling, not precise wavelengths. Genuinely distinct from coatpattern.py (flat 2D Gray-Scott on
a tapering body) and reactiondiff.py (flat GS): this is a closed curved manifold with topological
quantisation. VISUAL: three coat-regime balls rendered in 3D (Poly3DCollection, per-face colour) + the
spot-count-vs-size law + the spotted ball unwrapped to a seamless lon-lat map + the far side + a 30-frame
rotating GIF.

### R137 details

R137 added invasion fronts (`alife/fisherfront.py`): how fast life spreads — and when it can't get
started. The logistic reaction-diffusion u_t = D u_xx + r u(1-u) (Fisher-KPP 1937) sends a population
into empty habitat as a travelling wave with a uniquely selected speed c = 2√(rD); remarkably it is a
PULLED front — the speed is set entirely by the dilute leading edge, not the bulk — so faster growth or
diffusion speeds invasion as a square root. Add an Allee effect (growth that goes negative when too
sparse, r u(1-u)(u-a) with threshold a) and the front becomes PUSHED, c = √(rD/2)(1-2a), with a sharp
EXTINCTION THRESHOLD: for a<½ the population still invades, at a=½ the front stalls, and for a>½ it
RETREATS — a large founder population is driven extinct because its sparse edges can't grow. Both results
match CLOSED-FORM theory (the cleanest validation): the measured Fisher speed lands on the 2√(rD) line
across r and D (a little below, the known Bramson logarithmic finite-time correction to pulled fronts),
and the Allee front velocity lands on √(rD/2)(1-2a) to under 1% with its zero-crossing exactly at a=½.
In 2D the contrast is eyeball-obvious: a Fisher colony grows from a small disk to fill the field (radius
15→51), while an Allee a=0.7 colony collapses to extinction (28→8) from the same kind of seed. The
dynamics are deterministic (fully reproducible). Fresh and distinct from barkley/excitable (an excitable
PULSE with a refractory stable rest state, not the monostable invasion of one state by another) and from
the Gray-Scott / Turing pattern family (a single travelling front, not a standing pattern). VISUAL: 2D
invasion-vs-extinction snapshots + the Fisher speed law + the Allee velocity-vs-threshold zero-crossing +
shape-invariant travelling profiles + a 38-frame side-by-side GIF.

### R136 details

R136 added grain growth (`alife/graingrowth.py`): a polycrystal coarsens by curvature, the same way a
soap froth or an annealed metal does — small grains shrink and vanish, big grains swallow them, the mean
grain grows without bound. Modelled with the Q-state Potts model (Anderson-Srolovitz-Grest 1984): each
lattice site carries one of Q grain orientations, the energy counts unlike-neighbour bonds (= boundary
length), and a low-temperature Metropolis update (vectorised checkerboard) lets curved boundaries migrate
toward their centre of curvature (von Neumann-Mullins). Results, eye- and data-checked: the mosaic
visibly coarsens (fine salt-and-pepper → big grains); the total boundary length per area decays as a
power law (∝ t^-0.39) while the grain count falls (∝ t^-0.76) and the mean grain area grows ×33. The
TWO independently-measured quantities are mutually consistent — boundary ∝ 1/R and grain count ∝ 1/area
with area ∝ R², so the grain-count exponent should be twice the boundary exponent, and it is (ratio
1.93) — a built-in, non-circular validation. CONTROL: a greedy (strictly-downhill, no thermal noise)
update PINS — the boundaries freeze at bond density ~0.49 — showing thermal annealing is required to beat
lattice pinning. Robust across seeds 0/1/2. Honest: lattice Potts gives reduced exponents (R ∝ t^0.39
rather than the ideal parabolic 0.5; area ∝ t^0.78 not t^1) — the well-known lattice-pinning correction;
I do NOT claim the ideal n=1. Mechanically a Potts/Metropolis model but phenomenologically DISTINCT from
cellsort.py (the cellular Potts model: cell SORTING by differential adhesion with an area constraint, no
grains vanish) — here there is no area constraint and grain count collapses 8587→258 by pure boundary
minimisation. VISUAL: 3-time coarsening mosaic gallery + boundary power-law (vs pinned control) +
grain-count/area laws + final polycrystal + a 32-frame coarsening GIF.

### R135 details

R135 added Faraday waves (`alife/faraday.py`): vibrate a dish of liquid up and down and, above a
critical amplitude, the flat surface spontaneously erupts into a regular lattice of standing waves
(Faraday 1831). Modelled as a spectral surface field where the vertical vibration modulates effective
gravity g→g−a·cos(Ωt), so each Fourier mode is a damped Mathieu (parametrically forced) oscillator and a
cubic −βh³ term saturates the growth. Three results, eye- and data-checked: (1) PARAMETRIC ONSET —
nothing happens below a forcing threshold, then a pattern grows from noise (above threshold rms ×544; the
sub-threshold control a=0.2 DECAYS ×0.18 — and that decay is what proves the growth is real parametric
pumping, not a numerical instability); (2) SUBHARMONIC response — the surface oscillates at HALF the
drive frequency (measured temporal peak 3.14 vs Ω/2=3.16, and explicitly NOT at Ω), the defining
signature of parametric resonance; (3) the WAVELENGTH is TUNED by the drive — the selected wavenumber k*
(measured from the emergent field's FFT) lands on the gravity-capillary dispersion ω0(k*)=Ω/2, so shaking
faster makes a FINER lattice (gallery Ω×0.7/1.0/1.5 → k 1.42/1.94/2.59, matching theory 1.50/2.00/2.71).
Robust across seeds 0/1/2. Honest: an isotropic cubic model gives a cellular/labyrinthine lattice — I do
not claim a specific square/hex symmetry. Genuinely fresh — no Faraday/Mathieu/parametric module existed;
distinct from chladni (driven plate NODAL lines, not parametric) and swifthohenberg (autonomous pattern,
no temporal subharmonic). VISUAL: 3-frequency pattern gallery (coarse→fine) + rms-growth-vs-control +
subharmonic FFT + k*(Ω) dispersion match + a 60-frame eruption GIF.

### R134 details

R134 added murmuration vs a predator (`alife/murmuration.py`): a starling murmuration boiling away from
a hawk is collective ANTI-PREDATOR behaviour — no bird sees the whole flock, yet the group flows around
the predator and it mostly goes hungry. On top of plain boids (cohesion + alignment + separation) sits a
FLEE response: a prey within sense range steers directly away from the predator, and because neighbours
align with it the turn spreads through the flock. The predator chases the nearest prey; a catch respawns
that bird (holding the flock size). The pay-off is dramatic and control-validated: zeroing the flee
weight (same flock, prey just ignore the hawk) lets the predator park in the herd and feed — ON vs OFF
catch counts differ 80×/52×/167× across seeds 0/1/2 (robustly large, never marginal), and fleeing keeps
the hawk ~3.2 cells from the nearest bird vs ~2.2 when ignored. Neighbour queries via a periodic KD-tree
(`cKDTree(boxsize=L)`) + a per-agent boids loop. Honest: a loose agitated flock (polarization ~0.35, not
a tight band — the hawk keeps it stirred), and the alignment-propagated turning WAVE is the model
mechanism, not a separately measured headline (tests assert against random baselines: spread < L/√6,
polarization > 2/√N). Agent-based predator evasion, distinct from boids/boids3d/swarm3d (no predator) and
predprey (population dynamics, not spatial evasion). VISUAL: flock streaming away from the hawk (heading
arrows) + flee-ON-vs-OFF catch bar + hawk-distance-over-time + a 126-frame evasion GIF.

### R133 details

R133 added termite construction (`alife/termites.py`): stigmergy — structure with no blueprint (Grassé
1959). Random-walking termites deposit cement whose pheromone makes other termites more likely to
deposit nearby; the structure itself is the only coordination ("work begets work"). From a flat floor
the positive feedback breaks symmetry → material self-organises into MOUNDS (clustering var/mean ~5);
turn the feedback off (random deposition) and the floor stays flat (~1); clustering switches on as the
stigmergy strength k rises (control-validated metric). Distinct from antcolony (foraging trails) and
gpuslime (transport networks) — this is CONSTRUCTION, agents accreting persistent structure. HONEST: in
2D the positive feedback COARSENS into irregular mounds rather than the perfectly regular pillars of a
real 3D nest (regular spacing needs activator-inhibitor tuning — frontier). Visual: mounds + termites +
pheromone field + clustering-vs-k + watch-it-build GIF. (Also tried+abandoned a viscous-fingering attempt
this round — surface tension on a discrete DBM doesn't smooth the fractal; see honest notes.)

### R132 details

R132 added Wolf-Sheep-Grass (`alife/wolfsheep.py`): the classic 3-level agent food chain (NetLogo "Wolf
Sheep Predation") — grass regrows on a timer, SHEEP graze+breed+starve, WOLVES eat sheep+breed+starve,
all on a toroidal agent grid. Nothing is tuned to oscillate, yet the three populations fall into the
textbook predator-prey BOOM-BUST: sheep multiply on grass, wolves on sheep, sheep crash, wolves starve,
grass recovers. Verified: 3-way coexistence over thousands of steps; the predator LAGS the prey
(cross-correlation peak +86 — wolves follow sheep, the Lotka-Volterra phase relation); sheep
anti-correlate with grass (corr −0.86, overgrazing); grass is the essential base (no regrowth → the
whole chain collapses). Honest: in this regime sheep are GRASS-limited, so removing wolves doesn't boom
them (the wolves crop the surplus). The most "alive"/on-brand visual of the streak — a living world you
watch. Agent-based, distinct from ODE predprey / RD spatialpredprey / brain-evolution ecosim. Visual:
world snapshot (grass/sheep/wolves) + population cycles + predator-prey phase loop + cross-correlation
lag + a world GIF.

### R131 details

R131 added excitable media (`alife/barkley.py`): BZ-type spiral & target waves from the Barkley model
(continuum reaction-diffusion), du/dt=D∇²u+(1/ε)u(1-u)(u-(v+b)/a), dv/dt=u-v. An excitable medium sits
at a stable rest state, ignores sub-threshold kicks, but fires past the threshold (v+b)/a and propagates
the pulse; a broken front winds into re-entrant SPIRAL waves, and a periodic pacemaker emits concentric
TARGET rings (the iconic BZ petri-dish visual). Verified: rest state stable (no spontaneous firing),
firing threshold ~b/a (sub-threshold kick dies, supra ignites a wave), constant wave speed (~3.85
cells/time, front advances linearly in a 1D cable), spirals re-entrant, targets form rings. Honestly
PIVOTED from the Oregonator (the BZ-specific kinetics self-ignited in our parameterisation — rest state
unstable) to the robust Barkley reduction (the standard fast excitable model). Distinct from R88
excitable.py (a discrete Greenberg-Hastings CA, one spiral) and R124 cgle (complex amplitude PDE).
Visual round: spiral field + target rings + threshold curve + wave-speed line + target-wave GIF.

### R130 milestone review

R130 milestone review (the R123-R129 VISUAL streak). Adversarial re-verify with FRESH seeds: R121
flowforage (chemotaxis selected + flow reduces it), R122 dielectric (D(η) decreasing 1.69→0.95), R123
selfpropelled (mill M=0.96/P=0.01 + flock P=1.0), R124 cgle (defects 26→102 across BF line), R125
cahnhilliard (t^0.35 coarsening), R127 swifthohenberg (dom_k=0.99, rolls>hex elongation), R128 lanes
(drive 0.70 vs no-drive 0.20), R129 chladni (sand |φ| 0.062 vs 0.613) — all hold. R126 coatpattern:
the narrowing-elongates DIRECTION reproduces (1.18→1.43) but the effect size is seed-sensitive/weak
(1.21× this seed, below the 1.3× bar) — consistent with the already-recorded honesty that the coat
geometry effect is delicate; not a regression. Full-suite backstop run ALONE (per the R120 concurrent-
crash lesson). Milestone gallery R121-R129 at `runs/r130_review/gallery.png`. Workspace tidy; README +
CODEBASE_GUIDE counts refreshed to ~121 models / 712 tests. **Ambition critic:** seven visual rounds
(R123-R129) cover pattern-PDEs, active matter, and eigenmode self-assembly; the visual frontier still
has BZ target waves, a rendered creature-ecosystem mp4, SmoothLife, double-mill, and a proper viscous-
fingering animation. Build resumes (visually-first) at R131.

R129 added Chladni figures (`alife/chladni.py`): sand self-assembling onto the nodal lines of a
vibrating plate. A square plate's normal modes φ_{m,n}=sin(mπx)sin(nπy) have nodal lines where the
surface never moves; grains drift off the shaking antinodes (down grad(φ²)) with a little noise and
pile up on those motionless nodes, drawing the mode's zero set — the classic Chladni figures. (m,n) and
(n,m) are DEGENERATE (same frequency ∝√(m²+n²)), so the plate vibrates in combinations φ_{m,n}±φ_{n,m},
giving the rich diagonal patterns (not just a grid). Verified: grains settle where |φ| is ~10× below
random (0.061 vs 0.608) — sand genuinely finds the nodes; gallery of recognizable figures (finer with
pitch); degeneracy + x↔y symmetry checks. A fresh KIND of visual (eigenmode-driven self-assembly),
distinct from everything in the catalog. Visual round: 6-mode gallery (freq-ordered) + sand-assembly GIF.

R128 added lane formation (`alife/lanes.py`): two crowds driven in opposite directions through the same
space spontaneously segregate into LANES — non-equilibrium self-organisation (Helbing pedestrian
dynamics / driven binary colloids). Overdamped particles in a periodic box, each driven ±x by its
species, with soft neighbour repulsion + noise: a walker straying into the on-coming stream is bumped
sideways more than among its own kind, so same-direction walkers accrete into stripes parallel to the
flow. The lane order parameter (species purity within transverse y-stripes, control-validated: clean
lanes ~0.84, mix ~0.2) rises ~0.1→0.89 with the drive; without drive it stays mixed (~0.10); noise
melts the lanes above a critical value. Neighbour repulsion via a periodic KD-tree (O(N log N), fast).
Diverse from the recent PDE-pattern streak — active-matter agents; distinct from boids (alignment),
mips (same-species phase separation), selfpropelled (mill/flock). Visual round: mixed→lanes snapshots +
order-vs-time + noise-melting transition + lanes-forming GIF.

R127 added Swift-Hohenberg convection (`alife/swifthohenberg.py`): the Rayleigh-Bénard patterns —
parallel rolls and honeycomb hexagons — from the simplest equation with a BUILT-IN wavelength:
du/dt = ru − (1+∇²)²u + g u² − u³. The (1+∇²)² operator is minimised at k=1, so any growing pattern
picks that wavelength automatically (measured dominant k≈1.0) — no diffusion-ratio tuning, unlike
Turing. The drive r is the heating (flat below r=0); the quadratic term g is convection's up/down
asymmetry: g=0 gives ROLLS (stripes), g>0 near onset breaks into HEXAGONS (the classic Bénard cells).
Rolls vs hexagons read by eye (parallel stripes vs honeycomb) and by cell elongation (control-validated:
rolls elong 2.4, hexagons ~1.15, ~880 cells); the Fourier ring shows 6 spots at 60° for hexagons.
Fourier integrating-factor split (stiff 4th-order linear part exact, nonlinearity explicit — same trick
as cgle/cahnhilliard). A reliable clean visual round after the finicky coat round. Distinct from RD
Turing (built-in wavelength, convection patterns).

R126 added animal coat geometry (`alife/coatpattern.py`): how the leopard gets its spots, and Murray's
rule that DOMAIN GEOMETRY selects the Turing pattern. Gray-Scott in a spot-forming regime makes a 2D
spot lattice on a wide sheet; squeeze the domain into a narrow strip and the spots lose rows and
ELONGATE toward stripes; below one intrinsic wavelength no pattern fits (blank). Quantified with
control-validated blob metrics (spot count drops 115→25→0, elongation rises 1.25→~2 as width shrinks).
A no-flux masked Laplacian on a tapering body+tail domain shows the spotted body thinning down the tail.
This ADVANCES the R92 gierermeinhardt recorded honest-negative (where a narrowed Gierer-Meinhardt domain
went blank instead of patterning): with Gray-Scott we map the full geometry gradient and reach the
blank threshold cleanly. HONEST: clean dramatic transverse stripes remain a delicate sub-regime (the
continuous taper gives thinning spot-rows, not a sharp striped tail) — matching R92's difficulty, not a
full resolution. Visual round (CEO steer): leopard-coloured tapering creature + width-sweep gallery +
elongation/count-vs-width curves.

R125 added Cahn-Hilliard spinodal decomposition (`alife/cahnhilliard.py`): a quenched binary mixture
(alloy / oil-water / polymer blend) spontaneously UNMIXES into interpenetrating domains of two phases
that slowly COARSEN — small domains dissolve to feed big ones. The canonical "Model B": a CONSERVED
order parameter c down a double-well free energy, dc/dt = M∇²(−ε²∇²c + c³ − c). The Laplacian out front
makes c conserved (material is moved, not created) — distinct from the non-conserved reaction-diffusion
Turing patterns (gierermeinhardt/reactiondiff). From tiny noise the field splits into ±1 domains whose
characteristic size follows the Lifshitz-Slyozov-Wagner law L(t) ~ t^(1/3) — measured exponent 0.33.
Convex-splitting semi-implicit Fourier scheme (unconditionally stable for any ε, conserves the mean
exactly). The coarsening-length metric (structure-factor first moment) is validated on a stripe control.
Visual round (CEO steer): the coarsening sequence (watch domains merge) + log-log L(t) line on t^(1/3) +
an unmixing GIF.

R124 added the complex Ginzburg-Landau equation (`alife/cgle.py`): the universal amplitude PDE
dA/dt = A + (1+ib)∇²A − (1+ic)|A|²A that every oscillatory medium reduces to near onset. The phase of
the complex field is a colour wheel; wherever the phase winds a full turn around a point the amplitude
must vanish and a TOPOLOGICAL DEFECT (spiral core) sits there — visible at a glance as a rainbow
pinwheel in the phase image and a dark dot in |A|. Each defect has integer charge ±1 (winding number),
and on a periodic torus the total charge is always 0 (defects born/die in ± pairs — verified). The
Benjamin-Feir-Newell line 1+bc=0 splits the behaviour: 1+bc>0 freezes into rotating SPIRAL pinwheels;
crossing to 1+bc<0 they break into DEFECT TURBULENCE and the defect count explodes (~84 → ~366). The
winding-number defect counter is validated on controls (single spiral=+1, ± pair=net 0, uniform=0).
Visual round (CEO steer): rainbow spiral gallery + amplitude defect-cores + BF-transition curve +
rotating-spiral GIF. Fourier integrating-factor split-step. Distinct from R88 excitable.py (a discrete
Greenberg-Hastings CA with one spiral) — this is the continuum complex PDE with many interacting defects.

### CEO steer (R123): the loop had done many ABSTRACT rounds (eigenvalue clouds, growth-rate plots,
critical exponents); pivot to VISUALLY-CHECKABLE rounds — open the figure and immediately SEE it works
(recognizable patterns, life-like motion, animations), not metric plots.** R123+ bias toward visual.

R123 added self-propelled particles (`alife/selfpropelled.py`): the D'Orsogna et al. (2006) model —
self-propulsion/drag (α−β|v|²)v + a Morse potential (short-range repulsion, longer-range attraction) +
a tunable alignment term. One knob flips the collective state, each with a silhouette you name at a
glance: MILL (a hollow rotating RING circling an empty centre, P~0 M~1), FLOCK (cohesive march one way,
P~1 M~0), CLUMP (a still disordered blob, low speed, P~0 M~0). The state is read by EYE and confirmed by
two order parameters — polarization P=|mean heading| and signed milling M=|mean (r̂×v)| (both validated
on hand-built controls: tangent ring M~1, half-CW-CCW M~0, aligned P~1). The mill is genuinely emergent
(adding alignment destroys it → flock, proving it is rule-driven, not prescribed), and is the shape
Reynolds boids (boids/boids3d/swarm3d) structurally cannot make. Decided via an adversarial
proposer+judge workflow; PIVOTED from the judge's first pick (Couzin 2002 zonal model) after it would
NOT mill in 3 sweeps even with a rear blind spot — D'Orsogna SPP mills reliably. Figure: mill/flock/clump
snapshots + (P,M) bars + a hero animated GIF of the spinning milling torus (heading-hue colour-wheel).

R122 added the dielectric-breakdown model (`alife/dielectric.py`): Laplacian growth with one knob
(Niemeyer-Pietronero-Wiesmann 1984). Grow a cluster into a harmonic field (φ=0 on the cluster, φ=1 far
away, Laplace between), adding a perimeter cell with probability ∝ φ^η. The single exponent η sweeps
the whole morphology zoo: η=0 ignores the field → COMPACT (fractal dimension D→2, Eden-like); η=1 is
the DLA regime → FRACTAL dendrite; large η over-rewards the strongest tip → lightning-like NEEDLES
(D→1). Verified: D(η) measured by radius-mass scaling decreases monotonically (~1.86→1.62→1.24→1.02
for η=0,1,2,4). The harmonic field explains the mechanism — protruding tips screen the fjords,
concentrating the gradient, and η sets how ruthlessly that compounds. Sparse Laplace solve (precomputed
5-point operator, boolean-restricted to free cells). Generalises R78 DLA (the η=1 random-walker case);
distinct algorithm (field-based, not random-walker). D(η) is finite-size honest (η=1 measures ~1.6 vs
asymptotic 1.71; the TREND is the claim).

R121 added a COMPOSED world (`alife/flowforage.py`) — the depth/composition frontier the R120 review
called for. It couples three existing pieces into one eco-evolutionary world: a fluid FLOW (the R101
lattice-Boltzmann solver `fluid.py`, Kármán snapshot, or an analytic divergence-free vortex array)
advects a population of microswimmers that CHEMOTAX up a diffusing/depleting NUTRIENT field, eat,
reproduce with mutation, or starve — a toy of ocean plankton. Two emergent results none of the parts
shows alone: (1) the heritable chemotactic sensitivity χ is SELECTED — it rises ~1.56→2.7 when a
nutrient gradient exists to exploit (depletion makes the field patchy), while a neutral tag (chemotaxis
disabled) just drifts; (2) the FLOW shapes that evolution — stronger currents do some of the foraging,
so less chemotaxis is selected (χ falls 2.68→2.42 with flow strength, robust 5/5 seeds). Verified
non-circularly (χ is the evolved trait measured from the population; selection emerges from the eco
dynamics). Honest tertiary: chemotaxis+depletion makes foragers spread to EVEN spacing (resource
tiling, dispersion<1), not patches. Genuinely imports/runs fluid.py for the showcase flow.

### R120 milestone review

R120 milestone review: all eight R112–R119 headline claims re-verified with FRESH seeds — R112
Keller-Segel growth-rate crosses zero at the predicted chi_c; R113 3D Ising chi-peak T_c≈4.50 (>2D
2.269); R114 somitogenesis size=2πv/ω (0.1%); R115 chimera coherent+incoherent coexist (controls
full-sync); R116 May transition at σ√(SC)=1 + predator-prey stabilises (pp>rand); R117 growing-Turing
n∝L (corr 0.967); R118 phyllotaxis packing peak at exactly the golden angle + emergence; R119 snowflake
six-fold symmetry + compactness↓ with humidity — all hold, zero regressions. Full suite backstop: 642
pass. Milestone gallery (R111–R119) at `runs/r120_review/gallery.png`. Workspace tidy (root docs =
README/QUICKSTART/CODEBASE_GUIDE + progress/STATUS state); README + CODEBASE_GUIDE counts refreshed to
~112 models / 642 tests. **Ambition critic:** the project is now a very broad catalog (~112 isolated
models); the next frontier is depth/composition — a COMPOSED multi-model "world" (couple existing parts
into one emergent ecology), the deferred ambitious fluid round (viscous fingering / Laplacian growth),
and a few candidates not yet built (forest-fire SOC, gLV many-species dynamics, French-flag positional
information). Build resumes at R121.

R119 added snowflake growth (`alife/snowflake.py`): six-fold snow crystals from a one-rule cellular
automaton on a hexagonal lattice (Reiter 2005). Water vapour diffuses across the plane; wherever the
crystal or its immediate neighbourhood sits, vapour is captured and frozen. Diffusion smooths (favours
flat faces) while the tip instability sharpens (Mullins-Sekerka → dendrites), and one humidity knob β
sweeps the morphology from compact plates/stars to branching dendrites — the Nakaya diagram from a
local rule. Six-fold symmetry is EXACT (inherited from the lattice; the neighbour set is closed under
the mirror and inversion — verified). Morphology (compactness = fill of the enclosing disc) decreases
monotonically as β rises (compact→dendrite). A fresh KIND (crystal growth/dendrites), distinct from
dla.py (random-walker aggregation) — here it's a deterministic vapour-diffusion CA.

R118 added phyllotaxis (`alife/phyllotaxis.py`): why sunflowers/pinecones spiral by the golden angle
(137.508°) and count in Fibonacci. WHY (Vogel 1979): place organ n at angle n·α, radius ∝√n; packing
uniformity (min nearest-neighbour gap) peaks SHARPLY at exactly the golden angle — the most irrational
number, so no two organs ever align radially; rational angles p/q give q radial spokes with big gaps,
and even 0.5° off golden opens visible arms. HOW (Douady-Couder 1992): no plant computes φ — each new
primordium forms in the LEAST-CROWDED spot (min repulsion from outward-drifting predecessors), and that
purely local rule self-selects the golden angle (golden branch), with a secondary Lucas branch (~99.5°)
at lower growth rate G. Both verified from raw geometry/dynamics (packing optimum found by sweeping
angle; emergent angle measured from the rule, locks ~139.6° on the golden branch — finite-G offset from
137.5). A fresh KIND (optimal packing / Fibonacci morphogenesis), distinct from lsystem.

R117 added Turing-on-a-growing-domain (`alife/growingturing.py`): how a stripe pattern keeps its
spacing as the embryo grows. Static Turing freezes a fixed stripe count, but the intrinsic wavelength
λ* is set by the chemistry (Schnakenberg reaction-diffusion, λ*∝1/√γ), so on a domain that grows by
periodic uniform stretch the stretched stripes go Turing-unstable and a NEW stripe INSERTS/splits —
holding the spacing. Verified: stripe count grows in proportion to length (n∝L/λ*, corr 0.985);
wavelength oscillates in a sawtooth around λ*≈7.5 (stretch to ~1.5λ*, insert, reset; std/mean 10%);
chemistry sets λ* (∝1/√γ), not the domain. Insertion is RD-driven, not an interpolation artifact
(linear interp smooths; count jumps only after relaxation). A developmental route distinct from R114
somitogenesis (clock+front SET spacing) and from static Turing (count frozen).

R116 added May's complexity-stability theorem + Allesina-Tang (`alife/maystability.py`): random-matrix
ecology. A community Jacobian (self-regulation −d, random interactions with connectance C and strength
σ) has eigenvalues filling a Girko DISK of radius σ√(SC) centered at −d, so the equilibrium is stable
only while σ√(SC) < d — raising diversity/connectance/strength DESTABILISES (May 1972, the
diversity-stability debate). Transpose-correlation ρ turns the disk into an ellipse with semi-axes
σ√(SC)(1±ρ) (Allesina-Tang 2012): predator-prey interactions (ρ<0) shrink the cloud away from the
imaginary axis and push the stability edge far out, while mutualism/competition (ρ>0) destabilise —
interaction STRUCTURE beats raw complexity. Verified from raw eigenvalue spectra vs theory (Girko
radius, the κ=1 transition, the elliptic-law edges). A different KIND of model — spectral random-matrix
theory, not agent dynamics — distinct from all our predator-prey/ecosystem rounds.

R115 added chimera states (`alife/chimera.py`): identical phase oscillators on a ring, coupled
symmetrically through a NONLOCAL kernel with a small phase lag, spontaneously break into a coherent
(phase-locked) domain coexisting with an incoherent (drifting) one — the symmetry is broken by the
dynamics alone (Kuramoto-Battogtokh 2002; Abrams-Strogatz). Coupling sum = circular convolution via
FFT. Verified: the local order parameter shows a plateau (R≈1) beside a dip (R<1), global order is
partial (~0.72, neither full sync nor incoherence), and the split persists in space-time. Robust
across seeds. Controls: all-to-all coupling OR zero phase-lag → full sync, no chimera. Distinct from
kuramoto.py (global sync) and explosivesync.py. Honest finite-N nuance: on finite rings chimeras are
extremely long-lived (lifetime grows with N) rather than strictly eternal.

R114 added somitogenesis (`alife/somitogenesis.py`): the clock-and-wavefront model of vertebrate
segmentation (Cooke-Zeeman 1976; the her1/her7 segmentation clock). Every presomitic-mesoderm cell
runs a genetic OSCILLATOR; a determination WAVEFRONT recedes along the body axis and freezes each
cell's clock phase as it passes. A purely TEMPORAL rhythm crystallises into a periodic spatial pattern
of somites, with the geometry forced: somite size = wavefront speed × clock period = 2πv/ω, verified
EXACTLY (0.2% — the analytic law emerges from integrating the clocks, not plugged back in). Controls:
no clock → no segments; instant front → no pattern. A posterior frequency gradient reproduces the
travelling "kinematic" phase waves of the real PSM, arresting into graded somites (anterior larger).
A distinct route to spatial pattern from Turing self-organization (R45/gierermeinhardt) — wavelength
SET by a clock + moving boundary, not a diffusion instability — and from Kuramoto sync.

R113 added the 3D Ising model (`alife/ising3d.py`): the dimension-dependence of a phase transition.
R85 built 2D Ising (Onsager T_c=2.269); this is the 3D analogue, where each spin has z=6 neighbours
instead of 4, so order resists thermal noise to a HIGHER critical temperature T_c≈4.51 (no closed form
in 3D). Vectorized 3D checkerboard Metropolis on an L³ lattice; T_c located three independent ways —
the magnetisation collapse, the susceptibility peak (measured ≈4.5), and the size-independent Binder
cumulant crossing (≈4.43–4.45) — every number contrasted with 2D. Mean-field T_c=z (=4, 6) overestimates
both real values but captures the dimension trend exactly. Confirmed across independent seeds. The
coordination number is the knob: more neighbours → higher T_c.

R112 added Keller-Segel chemotactic aggregation (`alife/kellersegel.py`): the original 1970 model of
Dictyostelium slime-mold aggregation. Cells secrete a diffusing chemoattractant and crawl up its
gradient — a positive feedback that, above a critical sensitivity chi_c, makes a uniform cell lawn
linearly unstable and collapses it into mounds ("chemotactic collapse"). A pattern-forming instability
driven not by reaction kinetics (R45 Gray-Scott) but by nonlinear ADVECTION, and distinct from R55
Physarum networks / R95 single-cell chemotaxis. Conservative finite-volume + upwind scheme: cell mass
conserved to machine precision, density stays non-negative. The headline is verified RIGOROUSLY — the
measured single-mode (k_min) linear growth rate lies exactly on the dispersion-relation prediction and
crosses zero at the predicted chi_c≈1.03 (the end-state onset sits higher due to critical
slowing-down — an honest finite-time nuance). 10 tests.

R111 added spatial rock-paper-scissors (`alife/rpsmobility.py`): cyclic competition on a lattice
where MOBILITY decides survival — low mobility keeps three species coexisting in cyclic spiral
domains, but above a critical mobility the spirals merge and biodiversity collapses to one survivor
(Reichenbach-Mobilia-Frey 2007). Distinct from R39's well-mixed RPS.

### R110 milestone review

R110 milestone review: all nine R101–R109 headline claims re-verified with fresh seeds (Poiseuille +
Kármán, swimmer-vs-control, granular Beverloo/jamming, explosive-sync hysteresis, KPZ β<½, OFC
Gutenberg-Richter, repressilator parity, space-stabilizes-coexistence) — all hold; R101–R109 gallery
at `runs/r110_review/gallery.png`; workspace tidy; the untracked `nca.py` scaffold was deleted (the
CPU torch install never converged — re-creatable if torch ever lands).

### Recent build rounds (R104–R109)

All numpy/scipy: R109 spatial predator-prey (`alife/spatialpredprey.py`) — a
reaction-diffusion predator-prey where space rescues coexistence (asynchronous pursuit waves keep the
global population off the extinction floor that the well-mixed boom-bust cycle skims). R108 synthetic
gene circuits (`alife/genecircuit.py`, repressilator clock + loop-parity rule + toggle switch). R107
Olami-Feder-Christensen earthquakes (non-conservative SOC → Gutenberg-Richter). R106 KPZ surface
growth (ballistic deposition → β≈1/3). R105 explosive synchronization (Kuramoto on scale-free +
frequency=degree → first-order hysteretic sync). R104 granular DEM hopper (Beverloo / jamming). (R104
aimed at Neural Cellular Automata but a CPU torch install never converged; `alife/nca.py` is scaffolded
and untracked — its fate is decided at the R110 review.)

### The evolved-swimming arc (R101–R103)

The evolved-swimming-in-a-real-fluid arc is **complete** (R101→R103): R101 built a D2Q9
lattice-Boltzmann solver (`alife/fluid.py`, verified vs a parabolic Poiseuille profile and a Kármán
vortex street at Re=108, St=0.20); R102 dropped a flexible undulatory swimmer into it
(`alife/swimmer.py`, self-propels with the speed *emerging* from momentum conservation — net 22.6 vs
0 for the rigid control); R103 EVOLVED the gait (`alife/evoswim.py`) — a GA scored purely on emergent
swim speed climbs 10.7→12.8 (×10⁻³/step), beats the whole random-gait distribution, and the evolved
champion swims net 53.5. Real fluid dynamics + fluid-structure interaction + evolved locomotion, all
verified against physics/controls.

### R100 milestone review (2026-06-18)

R100 milestone review: full-suite backstop (511); all nine R91–R99 headline claims re-verified with
fresh seeds (R91 symmetric-control=0 drift, R92 spots∝area, R93 mild-τ segregates, R94 Derrida=K/2 at
K_c=2, R95 chemotaxis dose-response, R96 K_c=1.596σ, R97 percolation p_c≈0.593, R98 q_c≈40, R99 MIPS
CV control) — none broke; R91–R99 gallery at `runs/r100_review/gallery.png`. **Ambition decision:**
after 14 steady classic-model rounds (R85–R99), R101+ escalates to a bigger leap in *kind* — the
**evolved-swimming-in-a-real-fluid arc**: R101 lattice-Boltzmann (D2Q9) fluid verified against known
flows, R102 an immersed swimmer that self-propels, R103 evolve the swimming gait.

Public README was restructured at R91 per CEO: project description + deploy + block diagram only;
per-round catalog lives here, repo layout in `CODEBASE_GUIDE.md`.

An evolving artificial-life ecosystem built from zero over 111 autonomous rounds. The full stated
goal is realized — **Boids flocking → natural selection → neural-network brains → predator–prey →
energy/reproduction → a 3D ecosystem you watch evolve** — plus deep stretch work: ~10k-creature
scale, atmospheric GPU rendering, a dozen+ classic evolutionary phenomena, an open-endedness
trilogy (R28–R30), evolving morphology (R31), the **capstone (R33): in-situ foraging evolution
(no GA)**, a **Digital Genesis arc (R51–R53)** of self-replicating evolving programs, a
**GPU-compute substrate (R54–R60)** running 1M-agent ALife (RD / Physarum / Vicsek / evolution /
local-adaptation / Lenia), and **R61: Particle Life — organisms self-assemble from an asymmetric
force matrix**, **R62: Autocatalytic sets (RAF) — self-sustaining chemistry at a phase
transition**, **R63: Hypercycles (Eigen-Schuster) — limit cycle, parasite, spiral waves**, **R64: Development & diversity — L-system plants + MAP-Elites morphospace**, and
**R65: Ant-colony foraging — stigmergy trails + Deneubourg shortest path**, and
**R66: The edge of chaos — searching the CA rule space (Langton's λ)**, and
**R67: Evolving CA to compute — emergent global synchronization (Mitchell-Crutchfield-Das)**, and
**R68: Physarum transport networks — maze-solving + Tokyo-rail networks (Tero-Nakagaki)**, and
**R69: Hopfield associative memory — energy landscape + 0.138N capacity limit**, and
**R71: Bak-Sneppen co-evolution — self-organized criticality + punctuated equilibrium**, and
**R72: Genetic programming — evolution rediscovers a hidden equation (symbolic regression)**, and
**R73: Reservoir computing — an ESN learns to dream the Lorenz attractor**, and
**R74: The abelian sandpile — self-organized criticality + fractal order**, and
**R75: Swarm cognition — a honeybee colony decides by cross-inhibition consensus**, and
**R76: NK fitness landscapes — ruggedness, trapping & the complexity catastrophe**, and
**R77: Evolution of cooperation — iterated Prisoner's Dilemma strategy evolution**, and
**R78: Diffusion-limited aggregation — Brownian growth into a fractal**, **R79: Cellular Potts model — tissue sorts itself by differential adhesion**, and
**R81: Restricted Boltzmann machine — a neural network learns to dream**, and
**R82: The voter model — coarsening with and without surface tension**, and
**R83: Network science — scale-free networks & their Achilles heel**, and
**R84: Epidemics on networks — the vanishing threshold of scale-free topology**, and
**R85: The Ising model — spontaneous magnetisation & the order-disorder phase transition**, and
**R86: Nagel-Schreckenberg traffic — phantom jams emerge from local rules, propagate backward**, and
**R87: Watts-Strogatz small-world networks — a few shortcuts collapse path length, clustering survives**, and
**R88: Excitable media — self-sustaining spiral waves & re-entry (Greenberg-Hastings)**, and
**R89: A major transition — the evolution of division of labor (Jensen: specialise iff returns accelerate)**, and
**R91: Evolved Particle Life — selection discovers self-propelled matter (the asymmetry is the engine)**, and
**R92: Gierer-Meinhardt activator-inhibitor — Turing spots with an intrinsic wavelength (spots ∝ area)**, and
**R93: Schelling segregation — mild individual preferences make extreme separation nobody chose**, and
**R94: Kauffman random Boolean networks — order, chaos, and the critical edge at K=2**, and
**R95: Bacterial chemotaxis — run-and-tumble climbs a gradient with no sense of direction**, and
**R96: Kuramoto oscillators — spontaneous synchronization above a critical coupling**, and
**R97: Percolation — a spanning cluster is born at the critical density p_c ≈ 0.593**, and
**R98: Axelrod culture dissemination — why contact doesn't always erase differences**, and
**R99: Motility-induced phase separation — activity alone makes clusters (no attractive force)**, and
**R101: A real fluid — D2Q9 lattice-Boltzmann verified against Poiseuille flow & the Kármán vortex street**, and
**R102: A swimmer in a real fluid — self-propulsion emerges from an undulatory gait**, and
**R103: Evolving a swimming stroke — a GA discovers fast locomotion in a real fluid**, and
**R104: Granular media (DEM) — constant-rate hopper discharge & Beverloo's law**, and
**R105: Explosive synchronization — frequency-degree correlation turns sync into a first-order switch**, and
**R106: KPZ surface growth — ballistic deposition bends the growth exponent to 1/3**, and
**R107: Olami-Feder-Christensen earthquakes — non-conservative self-organized criticality (Gutenberg-Richter)**, and
**R108: Synthetic gene circuits — the repressilator clock & the toggle switch (loop parity decides)**, and
**R109: Spatial predator-prey — reaction-diffusion shows space rescues coexistence from boom-bust**, and
**R111: Spatial rock-paper-scissors — mobility destroys biodiversity past a threshold (RMF 2007)**, and
**R112: Keller-Segel chemotactic aggregation — a cell lawn collapses into mounds above a predicted chi_c (KS 1970)**, and
**R113: 3D Ising model — dimensionality (coordination z:4→6) lifts the critical temperature 2.27→4.51**, and
**R114: Somitogenesis (clock-and-wavefront) — a genetic oscillator's period becomes the body's segment size (2πv/ω)**, and
**R115: Chimera states — identical nonlocally-coupled oscillators split into coexisting coherent + incoherent domains**, and
**R116: May's complexity-stability + Allesina-Tang — random-matrix spectra set the edge of ecological stability (σ√(SC)=1)**, and
**R117: Turing on a growing domain — stripes INSERT to hold their wavelength as the domain grows (n∝L)**, and
**R118: Phyllotaxis — the golden angle uniquely packs gap-free (Vogel) and emerges from least-crowding (Douady-Couder)**, and
**R119: Snowflake growth — six-fold crystals + the Nakaya plate↔dendrite morphology from Reiter's hexagonal CA**, and
**R121: A composed world — chemotactic foragers EVOLVE inside a fluid flow (fluid.py + nutrient + selection); the current reshapes how much chemotaxis is selected**, and
**R122: Dielectric-breakdown model — one exponent η sweeps Laplacian growth from compact blobs to DLA fractals to lightning needles**, and
**R123: Self-propelled particles — a spinning MILL vs a marching FLOCK vs a still CLUMP from one knob (D'Orsogna 2006)**, and
**R124: Complex Ginzburg-Landau — rainbow spiral pinwheels (topological defects) breaking into defect turbulence across the Benjamin-Feir line**, and
**R125: Cahn-Hilliard spinodal decomposition — a quenched mixture unmixes into domains that coarsen as L(t)~t^(1/3)**, and
**R126: Animal coat geometry — domain width sculpts Turing spots into stripes (Murray; leopard spots & striped tails)**, and
**R127: Swift-Hohenberg convection — built-in wavelength + one knob: parallel ROLLS vs honeycomb HEXAGONS (Bénard cells)**, and
**R128: Lane formation — counter-flowing crowds spontaneously segregate into lanes (active matter / pedestrians)**, and
**R129: Chladni figures — sand self-assembles onto the nodal lines of a vibrating plate's modes**, and
**R131: Excitable media (Barkley) — BZ-type rotating spiral waves & concentric pacemaker target rings**, and
**R132: Wolf-Sheep-Grass — a 3-level agent food chain falls into predator-prey boom-bust cycles (predator lags prey)**, and
**R133: Termite construction (stigmergy) — builders with no blueprint self-organise material into mounds**, and
**R134: Murmuration vs a predator — a flock that flees as one starves the hawk (100×+ fewer catches)**, and
**R135: Faraday waves — a vibrated surface erupts into a subharmonic, drive-tuned standing-wave lattice**, and
**R136: Grain growth — a polycrystal coarsens by curvature (Q-state Potts, soap-froth/metal grains)**, and
**R137: Invasion fronts — Fisher-KPP pulled waves (c=2√rD) & the Allee extinction threshold**, and
**R138: Turing patterns on a sphere — an animal coat on a curved closed surface (icosphere Gray-Scott)**, and
**R139: Dendritic solidification — snowflake & cubic crystals from an undercooled melt (Kobayashi phase field)**.
**778 tests pass.** PUBLISHED & SYNCED through R139 on public
github.com/yusenthebot/alife. A real-fluid swimming arc runs R101
(lattice-Boltzmann) → R102 (undulatory swimmer) → R103 (evolved gait). A network-science arc runs R83 (scale-free)
→ R84 (epidemics) → R87 (small-world). An origin-of-life arc runs
R44 (error threshold) → R62 (autocatalytic sets) → R63 (hypercycles, Eigen's answer).

Status: well past the stated goal and into a long frontier tail (running divergently under standing
order to keep going until told to stop; each round commits + pushes). Each round adds a genuinely
distinct ALife phenomenon, real-run + eye-verified, never faked.

## Decisions pending
- **(R147) GENESIS Stage 3 division of labour — RESOLVED, POSITIVE.** Attempt 2 (convex specialization
  trade-off → heritable caste) worked: a bimodal processor/harvester caste emerges, role↔caste alignment is
  built by selection (caste-gap 0→+0.32, ~0 frozen), and the specialised economy out-produces force-generalist
  (5/5 seeds, red-teamed, castes spatially intermixed). Stage 3 is DONE. Next ladder rung = Stage 4 (niche
  construction / building / economy — agents reshape the 3D world). No CEO action.
- **(R145) GENESIS Stage 2 signalling — PARKED for a substrate redesign, not a CEO gate.** Two honest
  negatives (R144 no-kin, R145 clonal demes at r=0.90) show the signalling-bootstrap deadlock is not broken
  by relatedness or parameter sweeps. Revisiting needs a substrate change (synchronous discrete-predation
  selective rounds à la Floreano/Mitri, or explicit kin-fitness coupling) — a bigger build deferred to a
  later dedicated round. The loop has PIVOTED to Stage 3 (division of labour). No CEO action required; logged
  so the rung is resumed deliberately, not re-attempted blindly. Substrate (clonal demes, emit cost,
  prey_pred_range, relatedness metric, 4-control protocol) is committed and reusable.

## The rungs (detail in git log + README)

| | |
|---|---|
| R1 | emergent 2D Boids flocking (order φ 0.08→0.92) |
| R2 | natural selection — genome/energy/food/reproduction/death |
| R3 | evolved NN foraging brains (generational GA; 13–22× held-out) |
| R4 | predator–prey co-evolution (arms race) |
| R5 | continuous predator–prey ecology (2D coexistence) |
| R6 | recurrent brains (honest negative: memory not robustly better) |
| R7 | 3D flocking on the GPU (moderngl, headless on RTX 5080) |
| R8 | evolution in 3D (evolved 3D foragers + food) |
| R9 | predator–prey in 3D (aerial arms race) |
| R10 | continuous self-sustaining 3D living world |
| R11 | renderer beauty pass (fog, graded sky, rim light, shadows, glowing food) |
| R12 | milestone review + QUICKSTART + first-push gate |
| R13 | vast swarms (12k+ via KD-tree spatial index) |
| R14 | large-scale living world (~10.6k creatures, KD-tree ecosystem) |
| R15 | sustained predator–prey limit cycles (Huffaker refuge floor) |
| R16 | sympatric speciation (one species → two) |
| R17 | evolution of communication (Lewis signalling game) |
| R18 | evolution of evolvability (self-adaptive mutation rate) |
| R19 | evolution of cooperation (Hamilton's rule) |
| R20 | evolution of aging (Medawar/Williams) |
| R21 | a major transition: multicellularity (predation-driven) |
| R22 | Red Queen host–parasite coevolution |
| R23 | the gallery — every rung's headline frame in one journey poster |
| R24 | docs-hygiene (trimmed progress.md to current-state; no new capability) |
| R25 | sexual selection — Fisherian runaway (costly ornament dragged past survival optimum) |
| R26 | the memory win — RNN beats reactive brain on a provably memory-requiring task (R6 rematch) |
| R27 | milestone review — adversarial verify R25/R26, refresh README, ambition critic |
| R28 | open-endedness — MAP-Elites illuminates a behavior space (100% vs 16% objective-only) |
| R29 | open-ended navigation — sensed obstacle field; QD discovers routes around walls (103% vs 25%) |
| R30 | novelty search — beats objective on a deceptive maze (8/8 vs 2/8; Lehman-Stanley) |
| R31 | evolving morphology — mass-spring virtual creatures evolve a body + gait (dist 14→49; Karl Sims) |
| R32 | milestone review — adversarially verified R28–R31 (all hold); honest R31 gait caveat recorded |
| R33 | capstone — foraging behavior evolves IN SITU (no GA); directedness 0.08→0.33, food-limited pop |
| R34 | in-situ predator–prey — refuge-stabilized coexistence, boom-bust, prey evolve evasion (no GA) |
| R35 | evolution in a changing world — population tracks a flipping food valence (sawtooth re-adaptation) |
| R36 | review — red-team R33/R34/R35 (mutation-off controls), architecture/hygiene audit |
| R37 | evolution of sex — Muller's ratchet: asexual load ratchets up (→73), sex holds balance (~12) |
| R38 | spatial reciprocity — cooperation persists by clustering on a lattice (0.42) vs well-mixed (0) |
| R39 | rock-paper-scissors — local dispersal preserves all 3 species (~0.33) vs well-mixed fixation |
| R40 | review + phenomena-wall poster (R25–R39 montage); README roadmap refreshed; 193 tests green |
| R41 | the Baldwin effect — learning finds & assimilates a needle (Hinton-Nowlan); blind without it |
| R42 | group selection — Simpson's paradox: cooperation up in the whole, down in every group |
| R43 | animation showcase — the in-situ ecosystem as a GIF (watch foraging evolve; the "迷人" goal) |
| R44 | error threshold — Eigen's quasispecies: master sequence collapses above μc≈ln(σ)/L |
| R45 | morphogenesis — Gray-Scott reaction-diffusion: Turing patterns (spots/stripes/waves) |
| R46 | Conway's Game of Life — Gosper gun (unbounded growth) + soup→ash; the CA root of ALife |
| R47 | review — refreshed phenomena gallery (R25–R46, 17 panels); architecture/hygiene; 225 green |
| R48 | Daisyworld — life regulates planetary temperature (Gaia/homeostasis); std 1.7 vs 12.6 bare |
| R49 | evolutionary branching — one lineage splits under disruptive competition (adaptive dynamics) |
| R50 | release-readiness — README tells full R1–R49 story; roadmap to R49; docs-hygiene; 237 green |
| —  | **FIRST PUSH (Yusen approved): R2–R50 published to public github.com/yusenthebot/alife** |
| R51 | Digital Genesis — self-replicating PROGRAMS evolve (Avida/Tierra); a substrate leap (executable genome) |
| R52 | Digital Genesis II — computation PAYS: NAND computer outcompetes copier; de-novo NAND emerges (fragile) |
| R53 | Digital Genesis III — phylogeny: clades rise/fall, 24 lineages coalesce to 1 common ancestor |
| R54 | GPU substrate leap — 1.05M-cell Gray-Scott on compute shaders (GPU=CPU to 1e-7; ~100x faster) |
| R55 | GPU Physarum — 1,000,000 slime-mold agents self-organize into transport networks (stigmergy) |
| R56 | a million boids — GPU Vicsek flocking (order φ→0.98) + phase transition; full-circle to R1 |
| R57 | natural selection at a million-genome scale — GPU tournament evolution finds the global optimum |
| R58 | review — frontier gallery (R51–R57 Digital Genesis + GPU); architecture clean; full suite 272 |
| R59 | local adaptation @1M — GPU spatial evolution: the genetic map evolves to mirror the environment (corr→0.99) |
| R60 | Lenia — continuous-CA creatures self-organize on the GPU (deferred R47, resolved at scale) |
| R61 | Particle Life — organisms self-assemble from an asymmetric K×K force matrix (cells/membranes; 5.3× a gas; distinct matrices → distinct biota; all-repulsive control stays a gas) |
| R62 | Autocatalytic sets (RAF) — self-sustaining chemistry at a phase transition (Kauffman/Hordijk-Steel; giant RAF 0→625 reactions, P 0→0.98; f* grows modestly while diversity grows exponentially; circular-set fixpoint algorithm; red-teamed) |
| R63 | Hypercycles (Eigen-Schuster) — n≥5 limit cycle + all coexist (vs competitive exclusion for uncoupled); non-reciprocating parasite collapses the well-mixed cycle; spatial CA → rotating spiral waves with balanced coexistence. Honest negative: Boerlijst-Hogeweg spatial parasite-rescue NOT reproduced (red-team caught a seeding artifact; parasite invades spatially too) |
| R64 | Development & diversity — L-system plants (recursive grammar→grown form): developmental cascade, 6 species from 6 grammars, and MAP-Elites illuminating the (slenderness, branchiness) morphospace to 100% with diverse evolved plants. Honest note: every scalar fitness for an isolated plant collapses to a degenerate shape (spike/sprawl/line) — diversity illumination, not single-objective optimization, is the honest result |
| R65 | Ant-colony foraging — stigmergy: a spatial colony self-organizes a nest↔food pheromone highway (corridor 87 vs 3 off-axis; foraging accelerates), and the Deneubourg double-bridge locks onto the SHORTER route (P→1 across ratios, 12/12 seeds); equal-arm control breaks symmetry at random. Collective optimization with no optimizer |
| R66 | The edge of chaos — meta-level: search the SPACE of 2D life-like CA rules. Langton's λ phase transition (density rises monotonically); complexity is RARE and the fraction of complex rules peaks at intermediate λ (Conway sits there); a blind search of 2^18 rules rediscovers Life-like worlds clustering at the edge. Three regimes (ordered/complex/chaotic) shown |
| R67 | Evolving CA to compute (Mitchell-Crutchfield-Das) — a GA evolves a 1D CA rule table for the SYNCHRONIZATION task: from any start, drive the whole lattice to global blink-in-unison (0% random → 92% evolved), via emergent defect "particles" that annihilate (eye-verified spacetime). Honest sibling: density classification is NOT cracked (hard-IC acc below trivial; no perfect local rule) — red-team caught an inflated easy-IC metric |
| R68 | Physarum transport networks (Tero-Nakagaki) — tube conductivities adapt to Kirchhoff flow: a braided maze's dense mesh prunes to a near-shortest path (exact 52=true via BFS on the demonstrated maze + the test config; R70 review caveat: the Tero model can settle 1-2 junctions suboptimally on some mazes — a known local optimum, not always globally shortest); multi-source grows an efficient network; γ tunes redundancy↔efficiency (total material 197→55 monotone). Distinct from R55 agent-Physarum |
| R69 | Hopfield associative memory — attractor net: Hebbian weights carve an energy landscape, memories are valleys; 5 balanced patterns recalled perfectly (overlap +1.00) from 30%-corrupted/occluded cues; energy descends monotonically (Lyapunov); capacity phase transition at αc≈0.138N (recall collapses above). New compute model vs prior controllers (R3/R6/R26) |
| R70 | Milestone review — full suite 344; adversarially re-verified R62-R69 (all hold; softened R68 maze to "near-shortest"); built R59-R69 frontier gallery; refreshed README through R70 |
| R71 | Bak-Sneppen co-evolution — self-organized CRITICALITY (new dimension): least-fit species + neighbours replaced → self-organized gap at f_c≈0.667 (94% above), power-law avalanches (slope -1.16, scale-free), punctuated equilibrium (bursts + stasis in space-time). Criticality with no tuning |
| R72 | Genetic programming (Koza symbolic regression) — new evolutionary substrate: evolve variable-structure PROGRAM TREES (vs all prior fixed genomes). From (x,y) data alone, tree-GA rediscovers the formula: x²+sin(2x) recovered EXACTLY as sin(x+x)+(x*x) (RMSE 0.000), cubic RMSE 0.001; parsimony curbs bloat. Evolution writes its own equations |
| R73 | Reservoir computing (Echo State Network) — a fixed RANDOM recurrent reservoir (spectral radius 1.2) + a trained linear readout learns the Lorenz system, then closed-loop autonomously regenerates it: tracks ~4.6 Lyapunov times before chaos separates them, and reconstructs the butterfly attractor's climate (x-z + 3D). New paradigm vs trained-weight brains |
| R74 | The abelian sandpile (Bak-Tang-Wiesenfeld) — canonical lattice SOC: driven slowly, self-organizes to critical density (mean height 2.11) with scale-free power-law avalanches (slope -1.22); abelian toppling makes a point source relax into a self-similar FRACTAL (heights 0-3). Two faces: critical avalanches + emergent fractal order |
| R75 | Swarm cognition (honeybee decision, Seeley/Marshall) — agent-based collective decision: scouts recruit by quality-weighted dancing + a cross-inhibition stop-signal. Value-sensitive (best site wins, acc >0.8); cross-inhibition BREAKS DEADLOCK between equal sites into decisive consensus (loser→0.00 in ~61 steps) which recruitment alone can't (stays split 0.57/0.40, never resolves). Distinct from R65 stigmergy |
| R76 | NK fitness landscapes (Kauffman) — the GEOMETRY of evolution: epistasis K tunes ruggedness. K=0 single smooth peak (walks reach global); rising K → local optima explode (1→2045), walks get TRAPPED (frac-global 1→0), and the COMPLEXITY CATASTROPHE — gap between the global optimum and what adaptive walks reach widens (0→0.136). Verified K=0 global = mean-of-maxes |
| R77 | Evolution of cooperation (iterated PD strategy evolution) — memory-1 strategies, exact Markov payoffs. Axelrod tournament (reciprocators thrive, ALLC exploited); NOISE breaks TFT (vendettas, coop→0.5) but not self-correcting WSLS/Pavlov; well-mixed evolution is BISTABLE (5/8 seeds → cooperation, 2 → defection) — honest: cooperation contingent in well-mixed (cf R38 spatial). Distinct from fixed-strategy R19/R38 |
| R78 | Diffusion-limited aggregation (Witten-Sander) — Brownian walkers freeze on contact → self-similar fractal DENDRITE (mineral/coral/lightning), fractal dimension D≈1.57 by mass-radius (finite-size estimate of ~1.71); sticking probability controls morphology (1.0 ramified → 0.03 compact D≈1.82); line seed → coral forest. Big-jump random-walk speedup |
| R79 | Cellular Potts model (Graner-Glazier) — tissue-level morphogenesis: cells = energy-minimizing lattice domains (adhesion + area constraint, Metropolis). A salt-and-pepper mix of two cell types SORTS itself into separate tissues by differential adhesion (Steinberg); heterotypic boundary 345→181, while the EQUAL-adhesion control mixes (345→750) — mechanism proven |
| R80 | Milestone review — adversarially re-verified all 9 of R71–R79 (all hold; R73 valid-time noted as reservoir-size-dependent, published n_res=800 reproduces 4.6 Lyap); built R71–R79 frontier gallery; README refreshed through R80 |
| R81 | Restricted Boltzmann machine — generative neural net (completes trilogy w/ R69 recall, R73 prediction). CD-1 on bars-and-stripes; trained net DREAMS valid patterns 78% (21/30 distinct, no mode collapse) vs untrained 0.2% / random 0.05%; hidden weights = bar/stripe detectors; valid-dream fraction rises with training |
| R82 | The voter model — consensus dynamics: VOTER rule coarsens into rough fractal domains with NO surface tension (interface 0.21, driftless martingale mean opinion); MAJORITY rule has surface tension (smooth round domains, interface collapses to 0.107). Same lattice, two universality classes (honest: exact consensus=density needs async) |
| R83 | Network science (Barabási-Albert) — new substrate (topology): growth + preferential attachment → SCALE-FREE degree distribution (CCDF power law slope -1.82, hubs max-degree 151) vs Erdős-Rényi Poisson (slope -4.13, max 14). Robustness/fragility (Albert-Jeong-Barabási): BA robust to random failure (giant 0.8 @15%) but FRAGILE to targeted hub attack (→0); ER degrades alike |
| R84 | Epidemics on networks (SIR, Pastor-Satorras-Vespignani) — builds on R83: scale-free nets have a VANISHING epidemic threshold (BA ignites at β~0.05-0.08 where ER fizzles); hubs are super-spreaders (P(infected) rises with degree); TARGETED hub immunization crushes the epidemic (5%→0.005) where random barely helps (0.37) |
| R85 | The Ising model (Metropolis MC) — the canonical EQUILIBRIUM phase transition (vs R74 SOC): spontaneous magnetisation |M| collapses 0.99→0.03 at T_c≈2.269 (Onsager, symmetry breaking); susceptibility peaks at T_c (critical fluctuations); ordered/critical-fractal/disordered spin fields. Vectorized checkerboard |
| R86 | Nagel-Schreckenberg traffic — self-organized phantom jams on a ring from 4 local rules (accelerate / brake-to-gap / random-dawdle p / move): jams nucleate above a critical density with NO bottleneck and propagate BACKWARD at −1 cell/step (measured by stopped-field cross-correlation, 94% of steps) while cars move forward +1.47; triangular fundamental diagram peaks at ρ_c≈0.10-0.14 then collapses; control p=0 → fewer jams (the random slowdown is the cause) |
| R87 | Watts-Strogatz small-world networks — completes the network arc (the other pillar vs R83 scale-free): rewiring a ring lattice by a tiny fraction p collapses average path length while clustering survives. Matches closed-form theory (ring C0=0.600=3(k-2)/(4(k-1)), L0=50=n/2k); at p=0.01 path length → 0.32 of ring but clustering stays 0.98 (decoupling of scales); random graph C~0.01 L~3.8. Dynamical payoff: rounds to inform whole net drop 100→8 with shortcuts |
| R88 | Excitable media / spiral waves (Greenberg-Hastings CA) — new flavor (not RD R45, not life-like CA R46): cells cycle rest→excited→refractory→rest, fire when ≥thresh neighbours excited. Planar wave constant speed 1.0 cell/step; colliding waves ANNIHILATE on refractory tails (240→0, unlike linear waves); a BROKEN wavefront curls into a self-sustaining SPIRAL (re-entry, activity sustains forever, period~k); CONTROL: same medium uncut planar wave dies to 0 (no re-entry). Models BZ spirals & cardiac arrhythmia. Square geometry = Moore Chebyshev metric |
| R89 | A major transition — the evolution of division of labor. Colony-level (group) selection over members' effort split θ; sweep convexity α of task function g(x)=xᵅ. Confirms Jensen exactly: specialists beat generalists iff convex (α>1: g(1)/2 > g(0.5) ⇔ 0.5 > 0.5ᵅ). Evolve convex α=3 → BIMODAL castes (~32% pure task-A, ~32% pure task-B, ~1% generalist), spec index 0.82, productivity ~3× (superadditive); CONTROL concave α=0.5 stays generalist (spec 0.27, flat); α-sweep crosses spec 0.5 at α=1.00, exactly the Jensen threshold. Distinct from R42 group selection |
| R91 | Evolved Particle Life — a GA on R61's asymmetric force matrix maximising MOTILITY (net centre-of-mass drift). Because the matrix is asymmetric, interactions break Newton's 3rd law → net momentum → self-propulsion. Two controls: SYMMETRIC matrices drift exactly 0 (momentum conserved); symmetrizing the evolved champion kills its drift (580→0). Random asymmetric matrices already self-propel (mean ~55, max ~300); evolution amplifies it ~6× (147→~700), beating the random max ~2×. Active matter evolved from the rules up. Eye-verified: long directed CoM path vs random's wander vs symmetric's stillness |
| R92 | Gierer-Meinhardt activator-inhibitor — the other canonical Turing system (vs R45 Gray-Scott): slow self-activating activator + fast inhibitor (short-range activation, long-range inhibition). Makes leopard Turing spots (215 on 130²); INTRINSIC WAVELENGTH → spot count ∝ coat area (~12.7/1000 cells, constant spacing); inhibitor field broader than activator (Dh/Da=25); geometry sets arrangement (narrow strip → one elongated row). HONEST NEGATIVE: Murray's spots-vs-stripes-by-geometry (spotted body/striped tail) did NOT reproduce in this spot regime (thin tail goes blank, saturation suppresses pattern); clean GM stripes need a different regime, left as frontier |
| R93 | Schelling segregation (micromotives→macrobehavior, first social model) — two agent types on a grid with empties; an agent relocates if fewer than a fraction τ of its occupied neighbours share its type. CONTROL τ=0 stays mixed (seg 0.50, all content); MILD τ=0.3 → strong segregation (seg 0.76) yet everyone content (100%) — nobody wanted it; tipping curve rises sharply 0.50→~0.99 then DROPS to ~0.5 at τ≈0.8 (gridlock regime, never settles); relocation conserves agent counts |
| R94 | Kauffman random Boolean networks (gene-regulatory DYNAMICS, vs R76 static NK fitness) — N genes, each a random Boolean function of K others, synchronous updates → cyclic attractors ("cell types"). Connectivity K drives an order→chaos transition, verified vs theory: Derrida sensitivity = K/2 exactly (crosses 1 at critical K=2); one flipped gene HEALS at K=1 (→0), marginal at K=2, AVALANCHES at K≥3 (→0.46); attractor cycle length 1→7→never-closes as K goes 1→2→≥3 |
| R95 | Bacterial chemotaxis (run-and-tumble, Berg) — a cell too small to sense gradient direction climbs by biasing a random walk in TIME: straight runs + reorienting tumbles, with tumbling SUPPRESSED while concentration is improving. CONTROL α=0 (no temporal modulation) → pure diffusion (conc flat 0.25, 14% near source); α=10 climbs (conc 0.25→0.44, 37% accumulate near source); dose-response monotone (final conc 0.25→0.58 as α 0→16). Distinct from R65 ant stigmergy & R55/R68 Physarum |
| R96 | Kuramoto coupled oscillators — spontaneous synchronization with no leader or clock. N phase oscillators with spread-out natural frequencies, each pulled toward the mean phase. Verified vs theory: critical coupling Kc = 2/(πg(0)) = 1.596σ exactly; CONTROL K=0.5Kc incoherent (r≈0.05) vs K=2.5Kc synced (r→0.97); sharp monotone transition across Kc; partial sync just above Kc = a locked plateau (central frequencies pinned to the mean, 68% at 1.1Kc) flanked by drifting oscillators. Distinct from R88 excitable spatial waves |
| R97 | Percolation (2D site, geometric/connectivity transition) — fill cells with probability p, find clusters (scipy.ndimage). CONTROL p=0.55<p_c only small clusters (no spanning) vs p=0.62>p_c a giant spanning cluster; spanning probability jumps sharply across p_c=0.5927 and sharpens with size L (finite-size scaling, ~0.5 at p_c); largest-cluster fraction (order parameter) jumps ~0→0.7; cluster sizes have a cutoff below p_c but are SCALE-FREE at p_c (power law slope τ≈1.9, Fisher ~2.05) |
| R98 | Axelrod culture dissemination — homophily (interact ∝ cultural overlap) + social influence (copy a differing feature); F=10 features, q traits each. CONTROL low q=5 → MONOCULTURE (largest domain 100%, 1 region); high q=120 → frozen MULTICULTURE (551 regions, largest 1%); diversity transition in q is monotone — flat ~1.0 for q≤20 then collapses sharply at q_c≈40 to ~0.02. Diversity survives because similarity is required to influence. Distinct from R82 voter (binary) & R93 Schelling (spatial sorting) |
| R99 | Motility-induced phase separation (MIPS, active matter) — active Brownian particles with density-dependent speed v(ρ)=v0·max(0,1−ρ/ρ*); slow-in-crowds creates a runaway that phase-separates into dense clusters + a dilute gas with NO attraction. TWO controls: density-dependent CV=7.5 (clustered) vs constant-speed active gas CV=0.4 vs passive CV=0.4 (both homogeneous); onset monotone with activity (CV 0.4→10.7 vs v0). Honest: multiple finite-time domains (slow coarsening); too-dense kills MIPS (mean ρ→ρ* stalls uniformly). Distinct from R61/R91/R79 |
| R101 | A real fluid — D2Q9 lattice-Boltzmann (BGK), the first true fluid solver and the substrate for the evolved-swimming arc. Verified vs textbook physics: force-driven channel → parabolic Poiseuille profile (peak-normalized shape RMSE 0.005; magnitude within ~20% of the naive analytic, a forcing-scheme prefactor); flow past a cylinder at Re=108 → a Kármán vortex street with periodic shedding at Strouhal St=0.20 (textbook ~0.16-0.18, mildly raised by channel blockage). Symmetry-breaking (cylinder offset + initial noise) needed to trigger shedding |
| R102 | A swimmer in a real fluid (fluid-structure interaction) — a flexible body with a fish-like travelling-wave gait dropped into the R101 LBM fluid as a moving velocity source. The body is FREE; in the periodic box from rest, momentum conservation gives the recoil V_cm=−P_fluid/M, so the swim speed EMERGES (not prescribed). CONTROL: undulating (A=6) → net displacement 22.6 (steady directed swim) vs rigid (A=0) → 0.000; amplitude controls speed; tail sheds wake vorticity. Honest: momentum-conservation recoil model + feq velocity-source coupling; gait velocity kept below the LBM low-Mach limit |
| R103 | Evolving a swimming stroke (capstone) — a GA over the gait genome (amplitude, frequency, wavelength; low-Mach stability constraint enforced) scored purely on the swim speed that EMERGES from the LBM simulation, no fitness formula handed in. Best fitness climbs 10.7→12.8 (×10⁻³/step), population mean 6.6→12; the evolved gait beats the entire random-gait distribution (1.3× the best of 14 random, ~2-3× the mean); the evolved champion swims net 53.5 vs R102's hand-set 22.6. Honest: the optimum sits at the search-box corner (max amp/wavelength, freq capped) — a wider gait space would be faster |
| R104 | Granular media (soft-sphere DEM) — disks under gravity with linear spring-dashpot repulsion (scipy cKDTree contacts) draining through a gap in the floor. Real contact physics; granular signatures emerge: CONSTANT-rate discharge (cumulative-out is linear, R²=0.947 — unlike a liquid that slows as it empties; why an hourglass keeps time), Beverloo's law (rate rises super-linearly with opening, 0.064→0.724 over D=3..15), and JAMMING (a few-grain opening chokes flow to ~0). Honest: velocity-based friction (no static friction) → angle-of-repose abandoned for the hopper |
| R105 | Explosive synchronization — Kuramoto oscillators on a Barabási-Albert scale-free network with natural frequency = node degree (hubs beat fastest). CONTROL-verified: correlated freq=degree → coherence jumps abruptly (forward step ~0.79) and the backward sweep returns lower → a HYSTERESIS loop (area 0.52), a first-order switch-like transition (Gómez-Gardeñes 2011); shuffling the frequencies (same distribution, correlation destroyed) → smooth reversible 2nd-order (step ~0.22, area 0.06). Connects R96 (Kuramoto) + R83 (scale-free) |
| R106 | KPZ surface growth (ballistic vs random deposition) — particles falling on a 1D substrate. CONTROL random deposition (independent columns) → width w~t^0.5 (β=0.502), never saturates; BALLISTIC deposition (sticks on first lateral contact → column correlations) → Kardar-Parisi-Zhang roughening w~t^β with β=0.31±0.09 (seed-averaged ~1/3; single seeds noisy from corrections-to-scaling) and saturation w_sat~L^α, α=0.47 (KPZ ~1/2). One of the deepest non-equilibrium universality classes from one sticking rule |
| R107 | Olami-Feder-Christensen earthquakes — a spring-block fault grid loaded to threshold; a slip resets to 0 and gives α·stress to each of 4 neighbours (NON-conservative: 4α<1 loses stress), triggering avalanches. SOC survives despite dissipation: at α=0.22 the earthquake sizes follow a Gutenberg-Richter power law (τ≈1.9) over ~2 decades; strong dissipation (α=0.10) → only tiny quakes; conservation tunes the catalogue (big-quake fraction 0→0.98 as α 0.12→0.25). Distinct from R74 conservative abelian sandpile |
| R108 | Synthetic gene circuits (Hill-repression ODEs) — designed gene-regulatory dynamics, distinct from R94's random Boolean nets. The REPRESSILATOR (3-gene repression ring) sustains oscillations (a genetic clock, period ~12, three phase-shifted proteins); LOOP PARITY decides — odd rings (3,5,7) oscillate, even rings (2,4,6) are silent; oscillation needs COOPERATIVITY (Hill ≳ 2); the TOGGLE SWITCH (2 mutually-repressing genes) is bistable — initial bias selects one of two stable states (a one-bit cellular memory) |
| R109 | Spatial predator-prey (Rosenzweig-MacArthur reaction-diffusion) — a continuum field formulation (distinct from agent-based R5/R15/R34). CONTROL well-mixed 0D: boom-bust limit cycle, prey crashes to min ~0.011 (paradox of enrichment), global fluctuation std ~0.26; SPATIAL 2D: asynchronous patches form pursuit waves (field std ~0.14), the global population averages out-of-phase oscillators → fluctuation ~4× smaller (~0.06) and minimum ~10× higher (~0.10, far from extinction). Space turns a fragile boom-bust system into a persistent one |
| R111 | Spatial rock-paper-scissors (cyclic competition + mobility) — A beats B beats C beats A on a lattice with reaction (predation + reproduction) and conservative domino-swap EXCHANGE mobility. Distinct from R39's well-mixed RPS. Reichenbach-Mobilia-Frey (2007): low mobility → three species coexist in cyclic spiral domains (3 survivors); above a critical mobility the spirals merge until one wavelength exceeds the system → biodiversity collapses to 1 survivor; the survival curve drops 3→1 across the threshold. Honest: finite-size means strong seed fluctuation near threshold (averaged collapse is clean) |
| R112 | Keller-Segel chemotactic aggregation (Dictyostelium slime-mold, 1970) — cells secrete a diffusing chemoattractant and crawl up its gradient; the positive feedback destabilises a uniform lawn above a critical sensitivity chi_c, collapsing it into mounds (chemotactic collapse). A Turing-type instability driven by nonlinear ADVECTION (chi·rho·∇c), not reaction kinetics — distinct from R45 Gray-Scott, R55 Physarum networks, R95 single-cell chemotaxis. Conservative finite-volume + upwind: cell mass conserved to machine precision (drift ~1e-16), density non-negative. RIGOROUS verification: measured single-mode (k_min) linear growth rate lies exactly on the dispersion-relation prediction and crosses zero at the predicted chi_c≈1.03; theory = measured. Honest: the finite-time end-state onset sits above chi_c (critical slowing-down — σ→0 at threshold so a finite run can't resolve the marginal band) |
| R113 | 3D Ising model — dimensionality lifts the critical temperature. 3D analogue of R85's 2D Ising (Onsager T_c=2/ln(1+√2)≈2.269, z=4). On a cubic lattice each spin has z=6 neighbours, so order survives to T_c≈4.5115 (no closed form in 3D). Vectorized 3D checkerboard Metropolis ((i+j+k) parity splits the lattice into two sublattices whose 6 neighbours are all opposite colour → parallel update). T_c located THREE independent ways: magnetisation collapse, susceptibility peak (measured ≈4.5), size-independent Binder-cumulant crossing (≈4.43–4.45) — each contrasted with 2D. Mean-field T_c=z (=4,6) overestimates both (ignores fluctuations, worse in low-D) but gets the dimension trend. Confirmed across independent seeds. Coordination number is the knob: more neighbours → higher T_c. (3D critical exponents also differ: β≈0.326 vs 2D exact 1/8 — noted, not fitted) |
| R114 | Somitogenesis — the clock-and-wavefront model (Cooke-Zeeman 1976; her1/her7 segmentation clock). Each presomitic-mesoderm cell runs a phase oscillator; a determination wavefront recedes along the AP axis and FREEZES each cell's phase as it passes, turning a temporal rhythm into a periodic spatial pattern of somites. Geometry forced: somite size = front speed × clock period = 2πv/ω, verified EXACTLY (max rel err 0.2%, emergent from integrating clocks not plugged back in). Controls: omega=0 → 1 segment; instant front → no pattern. Posterior frequency gradient → travelling kinematic phase waves (as in real PSM) arresting into graded somites (anterior larger). Distinct route to pattern from Turing/RD (wavelength SET by clock+moving boundary, no diffusion instability) and from Kuramoto sync. Kymograph + size-law + zebra-segment figure |
| R115 | Chimera states (Kuramoto-Battogtokh 2002; Abrams-Strogatz) — a ring of IDENTICAL phase oscillators, symmetrically coupled via a NONLOCAL kernel (exp decay) with phase lag α just below π/2, spontaneously breaks into a coherent (phase-locked) domain coexisting with an incoherent (drifting) one. Coupling sum = circular convolution via FFT (O(N log N)): dθ_i/dt = ω − Σ_j G(i−j) sin(θ_i−θ_j+α). Verified at κ=4, α=1.46: local order R has a plateau (≈1) beside a dip (<0.5), global order partial (~0.72), split persists in space-time, robust across 5 seeds (coherent fraction ~0.3). Controls: all-to-all coupling OR α=0 → full sync (R≡1), no chimera. Distinct from kuramoto.py (global sync) + explosivesync.py. Honest: regime is narrow in (κ,α); on finite rings chimeras are extremely long-lived (lifetime grows with N), not strictly eternal. Figure: phase snapshot + local-order profile + 2 space-time kymographs |
| R116 | May's complexity-stability theorem (May 1972) + Allesina-Tang (2012) — random-matrix-theory ecology. Community Jacobian: diagonal −d (self-regulation), off-diagonal random interactions present w.p. C (connectance), strength std σ, transpose-correlation ρ. Girko circular law: eigenvalues fill a disk centered −d radius σ√(SC) → stable iff σ√(SC)<d, so complexity (S, C, σ) DESTABILISES. Elliptic law (correlation ρ): semi-axes σ√(SC)(1±ρ); predator-prey ρ<0 shrinks horizontal axis → stability edge pushed out (stabilising), mutualism/competition ρ>0 destabilising → interaction STRUCTURE beats complexity. Verified from raw eigenvalue spectra (scipy.linalg.eigvals): Girko radius, sharp stability transition at κ=σ√(SC)=1, elliptic-law edges per structure. Honest: finite-S puts the measured rightmost eigenvalue slightly right of the asymptotic bulk edge. A spectral (not dynamical) model — distinct from all predprey/ecosystem rounds. Figure: Girko disk + May transition + 3 structure ellipses + structure-shifted stability curves |
| R117 | Turing patterns on a growing domain (Crampin-Gaffney-Maini 1999) — Schnakenberg RD in 1D (dx=1 lattice, Du=1, Dv=40, Neumann BC) on a domain growing by periodic uniform stretch (interpolation onto a longer grid + relaxation). The intrinsic Turing wavelength λ*∝1/√γ is fixed by the chemistry, so as the domain lengthens stretched stripes go unstable and NEW stripes INSERT/split, holding the spacing. Verified: n_stripes ∝ L (corr 0.985); wavelength sawtooth around λ*≈7.5 (stretch to ~1.5λ*, insert, reset; std/mean 10%); λ* set by γ not domain; static control = fixed count, wavelength domain-independent. Insertion is RD-driven not interpolation artifact (linear interp smooths; count jumps only after relaxation). Developmental route distinct from R114 somitogenesis (clock+front) and static Turing/gierermeinhardt (frozen count). Figure: insertion kymograph + n∝L + wavelength sawtooth + λ*(γ) |
| R118 | Phyllotaxis — golden angle, optimal packing, emergence (Vogel 1979; Douady-Couder 1992). WHY golden (137.508°=360(2−φ)): Vogel spiral (organ n at angle n·α, radius ∝√n); packing uniformity = min nearest-neighbour gap (scipy cKDTree) peaks SHARPLY at exactly golden (the most irrational number → no radial alignment); rational p/q → q spokes; 0.5° off → visible gaps/arms. HOW it emerges: Douady-Couder least-crowding rule — each new primordium at the apex-circle angle minimising repulsion (Σ1/d^p) from outward-drifting (r×=exp(G)) predecessors; self-selects the golden branch (~138-140°, →137.5 as G→0) with a secondary Lucas branch (~99.5°) at low G (bifurcation diagram). Both verified non-circularly (packing optimum by angle-sweep; emergent angle measured from dynamics). Fibonacci parastichies follow from golden's continued-fraction convergents. Fresh KIND (optimal packing/Fibonacci morphogenesis), distinct from lsystem. Figure: golden sunflower + off-angle spokes + packing-optimum peak + emergence trajectory + bifurcation |
| R119 | Snowflake growth — Reiter's hexagonal snow-crystal CA (2005); Nakaya morphology (1954). On a hex (axial) lattice: a cell is RECEPTIVE if frozen (s≥1) or touching frozen; receptive cells hold water + gain constant vapour γ, non-receptive cells' water DIFFUSES (hex Laplacian, rate α); background humidity β. Diffusion smooths (flat faces) vs tip instability (Mullins-Sekerka → dendrites). One knob β sweeps compact plate/star → branching dendrite (compactness = frozen/π R² decreases monotonically with β). Six-fold symmetry EXACT (neighbour set closed under transpose-mirror + inversion → verified). Fresh KIND (crystal growth/dendrites), distinct from dla.py (random-walker DLA) — deterministic vapour-diffusion CA. Honest: full β range non-monotone (real Nakaya diagram is too) + crystal must stay inside L (np.roll periodic). Figure: 5-snowflake gallery (star/dendrite/broad/feathery/plate) + compactness-vs-β curve |
| R121 | A COMPOSED world — chemotactic foragers evolving inside a fluid flow (flowforage.py); the depth/composition frontier per the R120 critic. Couples fluid.py (R101 LBM Kármán flow, or analytic divergence-free vortex array) + a diffusing/depleting nutrient field + an evolving population (agents advected by flow + chemotaxis up ∇nutrient·χ + eat/energy/reproduce-with-mutation/die). EMERGENT results none of the parts shows alone: (1) heritable chemotactic sensitivity χ is SELECTED — rises ~1.56→2.7 with a gradient to exploit; a neutral tag (chemotaxis off) drifts (1.56→1.57) → clean selection vs drift control; (2) FLOW shapes evolution — χ falls 2.68→2.42 as flow strength rises (5/5 seeds), stirring substitutes for active foraging. Non-circular (χ measured from population, selection emergent). Honest: chemotaxis+depletion → EVEN spacing (dispersion<1, resource tiling), NOT patches (index-of-dispersion headline was wrong-signed; reframed). Genuinely imports/runs fluid.py. Figure: real Kármán vorticity + world snapshot (agents coloured by χ on nutrient) + χ-vs-time selection + χ-vs-flow-strength |
| R122 | Dielectric-breakdown model (Niemeyer-Pietronero-Wiesmann 1984) — Laplacian growth with one exponent. Solve the harmonic field around the cluster (φ=0 on cluster, φ=1 on outer ring, Laplace between via a precomputed sparse 5-point operator boolean-restricted to free cells, scipy spsolve), then add a perimeter cell with prob ∝ φ^η. η sweeps the morphology zoo: η=0 → compact (D→2, Eden), η=1 → DLA fractal dendrite, large η → lightning needles (D→1). Verified: radius-mass fractal dimension D(η) decreases monotonically (~1.86,1.62,1.24,1.02 for η=0,1,2,4). Mechanism: tips screen fjords, concentrating the gradient; η sharpens it (field panel shows bright tips / dark fjords). Generalises R78 dla.py (random-walker = η=1 special case); distinct field-based algorithm. Honest: η=1 measures D~1.6 (finite-size/batch) vs asymptotic 1.71 — the TREND is the claim. Figure: 4-η morphology zoo + D(η) curve + harmonic-field screening map |
| R123 | Self-propelled particles — D'Orsogna-Chuang-Bertozzi-Chayes (2006). Newtonian SPP: dv/dt=(α−β|v|²)v + Morse force (Cr e^{-r/lr} repulsion − Ca e^{-r/la} attraction) + bounded alignment a·(v̂_avg−v̂). One knob → three eyeball-distinct collective states: MILL (align=0: hollow rotating ring, P~0 M~0.96), FLOCK (align≥0.5: coherent march, P~1 M~0), CLUMP (low α: still disordered blob). Read by eye; confirmed by polarization P=|mean v̂| + signed milling M=|mean (r̂×v̂)| (validated on controls). Mill is emergent (alignment destroys it→flock) and is the shape Reynolds boids cannot make → distinct from boids/boids3d/swarm3d. CEO VISUAL steer; decided via adversarial proposer+judge workflow. Figure: mill/flock/clump quiver snapshots + (P,M) bars + spinning-mill GIF (heading-hue wheel = visible circulation) |
| R124 | Complex Ginzburg-Landau eqn (cgle.py) — universal amplitude PDE dA/dt=A+(1+ib)∇²A−(1+ic)|A|²A. Phase=colour wheel; each full-turn winding = a ±1 TOPOLOGICAL DEFECT (spiral core, |A|→0) — rainbow pinwheel in phase, dark dot in |A|. Benjamin-Feir line 1+bc=0: 1+bc>0 → frozen rotating SPIRALS; 1+bc<0 → DEFECT TURBULENCE, defect count explodes (~84→~366). Winding-number defect counter VALIDATED on controls (single spiral=+1, ± pair=net 0, uniform=0); net charge=0 on periodic torus (defects in ± pairs). Fourier integrating-factor split-step (diffusion exact, reaction explicit). VISUAL round (CEO steer): spiral gallery + amplitude cores + BF-transition curve + rotating-spiral GIF. Distinct from R88 excitable.py (discrete Greenberg-Hastings CA, one spiral) — continuum complex PDE, many defects |
| R125 | Cahn-Hilliard spinodal decomposition (cahnhilliard.py), "Model B" conserved-order-parameter phase separation. dc/dt=M∇²μ, μ=−ε²∇²c+c³−c. Quenched mixture unmixes into ±1 domains that COARSEN (small dissolve to feed big). Conserved order parameter (Laplacian out front → mean exactly conserved) → distinct from non-conserved RD Turing (gierermeinhardt/reactiondiff). Domain size follows Lifshitz-Slyozov-Wagner L(t)~t^(1/3) — measured n=0.33. Convex-splitting semi-implicit Fourier scheme (unconditionally stable any ε; naive semi-implicit blows up for small ε — needs the A·k² stabilizer). Length metric (structure-factor 1st moment) validated on a stripe control. VISUAL: coarsening sequence + log-log L(t) on t^(1/3) + unmixing GIF |
| R126 | Animal coat geometry (coatpattern.py) — Murray's rule that DOMAIN GEOMETRY selects the Turing pattern; "how the leopard gets its spots". Gray-Scott spot-regime (F=0.030,k=0.062): wide 2D sheet → spot lattice; narrow strip → spots lose rows + ELONGATE toward stripes; sub-wavelength → blank. Quantified (control-validated blob metrics): spot count 115→25→0, elongation 1.25→~2 as width shrinks. No-flux masked Laplacian (validated: uniform→0) on a tapering body+tail domain → spotted body thinning down the tail. ADVANCES the R92 gierermeinhardt honest-negative (GM went blank when narrowed) by mapping the geometry gradient with Gray-Scott + reaching the blank threshold cleanly. HONEST: clean transverse stripes still a delicate sub-regime (continuous taper gives thinning spot-rows, not a sharp striped tail) — not a full resolution. VISUAL: leopard tapering creature + width-sweep gallery + elongation/count curves |
| R127 | Swift-Hohenberg / Rayleigh-Bénard convection (swifthohenberg.py). du/dt=ru−(1+∇²)²u+g u²−u³. (1+∇²)² minimised at k=1 → BUILT-IN wavelength (measured dom_k≈1.0; growth rate r−(1−k²)² peaks at k=1), no diffusion-ratio tuning unlike Turing. r=drive (flat for r<0); g=up/down asymmetry: g=0 → ROLLS (stripes), g>0 near onset → HEXAGONS (Bénard honeycomb cells). Read by eye + cell elongation (control-validated: rolls 2.4, hexagons ~1.15 / ~880 cells); FFT ring shows 6 spots@60° for hexagons, diffuse ring for labyrinth rolls. Fourier integrating-factor split (4th-order linear exact). Reliable clean visual. VISUAL: rolls + hexagons fields + FFT 6-fold + g-transition + dispersion curve |
| R128 | Lane formation (lanes.py) — counter-flowing active matter self-organising into lanes (Helbing pedestrians / driven binary colloids). Overdamped particles in a periodic box, driven ±x by species, soft neighbour repulsion + noise; a walker straying into the on-coming stream gets bumped sideways more than among its own kind -> same-direction walkers accrete into stripes ∥ flow. Lane order parameter = species purity within transverse y-stripes (control-validated: clean lanes ~0.84, mix ~0.2); rises 0.1->0.89 with drive, stays ~0.10 with NO drive, melts above a critical noise. Periodic KD-tree neighbours (O(N log N)). Distinct from boids (alignment) / mips (same-species) / selfpropelled (mill). VISUAL: mixed->lanes snapshots + order-vs-time (+ no-drive control) + noise-melting transition + GIF |
| R129 | Chladni figures (chladni.py) — sand self-assembling onto a vibrating plate's nodal lines. Square-membrane modes φ_{m,n}=sin(mπx)sin(nπy), freq ∝√(m²+n²); (m,n)&(n,m) DEGENERATE → combinations φ_{m,n}±φ_{n,m} give the rich diagonal Chladni patterns. Grains drift down grad(φ²) (off antinodes) + noise → settle on nodes (|φ|=0). Verified: sand |φ|≈0.061 vs 0.608 random (~10× lower, grains find nodes); boundary φ=0; degeneracy; +combo symmetric / −combo antisymmetric under x↔y; higher mode → more nodal lines. Fresh KIND (eigenmode self-assembly). VISUAL: 6-mode freq-ordered gallery + sand-assembly GIF |
| R131 | Excitable media (barkley.py) — BZ-type spiral & target waves. Barkley continuum RD: du/dt=D∇²u+(1/ε)u(1-u)(u−(v+b)/a), dv/dt=u−v. Stable rest, fires past threshold (v+b)/a, refractory recovery. Broken front → re-entrant SPIRALS; periodic pacemaker → concentric TARGET rings (iconic BZ). Verified: rest stable, threshold ~b/a (sub-kick dies/supra propagates), constant wave speed ~3.85 cells/time (linear 1D front), spirals re-entrant, target rings form (no pacemaker→none). PIVOTED from Oregonator (self-ignited — rest unstable in our params) to robust Barkley reduction. Distinct from R88 excitable.py (discrete Greenberg-Hastings CA) + R124 cgle (complex PDE). VISUAL: spiral + target fields + threshold curve + wave-speed line + target GIF |
| R132 | Wolf-Sheep-Grass (wolfsheep.py) — 3-level agent food chain (NetLogo classic). Grass regrows on a timer; sheep graze+breed+starve; wolves eat sheep+breed+starve; toroidal agent grid (arrays of pos+energy, grass regrow-timer grid). Emergent predator-prey BOOM-BUST cycles: coexistence over 1000s of steps, predator LAGS prey (cross-corr +86), sheep anti-correlate grass (−0.86 overgraze), grass essential (no regrow→collapse). Lag metric validated on synthetic shifted signal. Honest: sheep grass-limited in this regime (removing wolves doesn't boom them). Coexistence params L=45,move=1,w_gain=25 (delicate — sweep found it; too-sparse grid→wolves starve). Agent-based, distinct from ODE predprey / RD spatialpredprey / brain-evo ecosim. VISUAL: world snapshot + pop cycles + phase loop + cross-corr lag + world GIF |
| R133 | Termite construction / stigmergy (termites.py) — Grassé (1959): builders with no blueprint. Random-walking termites deposit cement; the cement's pheromone (diffuse+evaporate) raises nearby deposit probability -> positive feedback ("work begets work") -> from a flat floor, material self-organises into MOUNDS. Verified: clustering var/mean ~5 with feedback (k=6) vs ~1 random (k=0), clustering switches on as k rises; metric validated on poisson/clumpy controls; pheromone field diffuses from mounds. Distinct from antcolony (foraging) + gpuslime (transport) — CONSTRUCTION/accretion. HONEST: 2D feedback COARSENS to irregular mounds, not regular 3D-nest pillars (activator-inhibitor frontier). VISUAL: mounds + termites + pheromone + clustering-vs-k + build GIF |
| R134 | Murmuration vs a predator (murmuration.py) — collective anti-predator evasion. Boids prey (cohesion+alignment+separation) + a hawk chasing the nearest bird; a prey within sense range adds a strong FLEE force away from the predator, and alignment spreads the turn through the flock. Caught prey respawn (flock size held). CONTROL = zero the flee weight (same flock, prey ignore the hawk) → the hawk parks in the herd and feeds: ON vs OFF catches differ 80×/52×/167× across seeds 0/1/2 (robust), and fleeing holds the hawk ~3.2 cells off the nearest bird vs ~2.2. Emergent catch-count metric, single-variable ablation. Periodic cKDTree(boxsize=L) neighbours + per-agent boids loop. HONEST: loose agitated flock (polariz ~0.35, predator keeps it stirred); the alignment-propagated turning wave is the mechanism, not a separately measured claim (tests assert vs random baselines: spread<L/√6, pol>2/√N). Distinct from boids/boids3d/swarm3d (no predator) + predprey (population, not spatial evasion). VISUAL: flock streaming from the hawk + flee-on/off catch bar + hawk-distance curve + 126-frame evasion GIF |
| R135 | Faraday waves (faraday.py) — a vertically vibrated fluid surface erupts into a standing-wave lattice (Faraday 1831). Spectral surface field; vibration modulates effective gravity g→g−a cos(Ωt) so each Fourier mode is a damped Mathieu (parametric) oscillator, cubic −βh³ saturates. (1) PARAMETRIC ONSET — above threshold rms ×544, sub-threshold a=0.2 DECAYS ×0.18 (a-only ablation; the decay proves growth is real pumping not numerical blow-up). (2) SUBHARMONIC — surface oscillates at Ω/2 (measured 3.14 vs 3.16, NOT Ω — the parametric-resonance signature). (3) DRIVE-TUNED WAVELENGTH — selected k* (emergent FFT) lands on gravity-capillary dispersion ω0(k*)=Ω/2; shake faster → finer lattice (Ω×0.7/1.0/1.5 → k 1.42/1.94/2.59 vs theory 1.50/2.00/2.71). Robust seeds 0/1/2. HONEST: isotropic cubic → cellular/labyrinth lattice, no square/hex symmetry claimed. Fresh — distinct from chladni (plate NODAL lines, not parametric) + swifthohenberg (autonomous, no temporal subharmonic). VISUAL: 3-Ω gallery coarse→fine + rms-vs-control + subharmonic FFT + k*(Ω) dispersion match + 60-frame eruption GIF |
| R136 | Grain growth (graingrowth.py) — a polycrystal coarsens by curvature (Q-state Potts, Anderson-Srolovitz-Grest 1984; soap froth / annealed metal). Site = 1 of Q grain orientations; energy = unlike-neighbour bonds (boundary length); low-T vectorised checkerboard Metropolis → curved boundaries migrate to their centre of curvature (von Neumann-Mullins), small grains vanish. Mosaic visibly coarsens (fine→large); boundary length ∝ t^-0.39, grain count ∝ t^-0.76, mean area ×33. TWO independent measures consistent: grain-count exp ≈ 2× boundary exp (area∝R²; ratio 1.93) = built-in non-circular check. CONTROL: greedy (strictly-downhill, no noise) PINS (bond plateaus ~0.49) — thermal annealing needed to beat lattice pinning. Robust seeds 0/1/2. HONEST: lattice Potts → reduced exponents (R∝t^0.39 not ideal 0.5) — no n=1 claim. DISTINCT from cellsort (CPM cell-sorting w/ adhesion+area constraint; here grains VANISH 8587→258, pure boundary min). VISUAL: 3-time coarsening mosaic gallery + boundary power-law-vs-pinned + count/area laws + final polycrystal + 32-frame coarsening GIF |
| R137 | Invasion fronts (fisherfront.py) — Fisher-KPP pulled waves + the Allee extinction threshold. Logistic RD u_t=D u_xx+r u(1-u) → a PULLED travelling front at c=2√(rD) (speed set by the dilute leading edge). Allee term r u(1-u)(u-a) → a PUSHED front c=√(rD/2)(1-2a) with an EXTINCTION THRESHOLD: a<½ invade, a=½ stall, a>½ RETREAT (founder population dies). Matches CLOSED-FORM theory: Fisher c on the 2√(rD) line across r,D (slightly below = Bramson log correction); Allee velocity on √(rD/2)(1-2a) to <1%, zero-crossing exactly at a=½. 2D: Fisher colony 15→51 (invades) vs Allee a=0.7 colony 28→8 (extinct), same seed. Deterministic/reproducible. DISTINCT from barkley/excitable (excitable PULSE w/ refractory rest, not monostable invasion) + Gray-Scott/Turing (standing patterns). VISUAL: 2D invasion-vs-extinction snapshots + Fisher speed law + Allee velocity-vs-a zero-crossing + shape-invariant profiles + 38-frame side-by-side GIF |
| R138 | Turing patterns on a sphere (turingsphere.py) — an animal coat on a curved CLOSED surface. Gray-Scott RD on an ICOSPHERE mesh (icosahedron subdivided n times → unit sphere; no lat-lon pole singularity, near-uniform resolution). Diffusion = row-normalized graph Laplacian (Lap u = mean(nbrs)−u, eigvals [−2,0] → standard GS step stable; conserves constants, |L·1|<1e-16). Three eyeball coat regimes by (F,k): isolated SPOTS (~41, leopard ball), LABYRINTH, CORAL. Sphere-specific QUANT: closed geometry quantises the pattern — spot count grows with sphere size (subdiv 3/4/5 → 0/18/41 spots, ∝ area/λ²; mesh refine = larger R/λ since normalized Laplacian sets λ in edge units). HONEST: spot-count only meaningful in the isolated-spots regime (size-law uses that; labyrinth/coral not counted as spots); graph Laplacian ≈ Laplace-Beltrami → qualitative pattern + size-scaling, not precise λ. DISTINCT from coatpattern (flat 2D taper) + reactiondiff (flat GS) — closed curved manifold + topological quantization. VISUAL: 3 coat-regime 3D balls (Poly3DCollection) + spot-count-vs-size + lon-lat unwrap + far side + 30-frame rotating GIF |
| R144 | **GENESIS Stage-2: signalling substrate + emergence protocol (honest NEGATIVE)** — each prey emits an evolved scalar UTTERANCE (one extra brain output) and senses its nearest neighbour's utterance (new input channel) over the kin-adjacency. Additive; `signalling=False` byte-identical to R143 (n_in 13/n_out 3 → 14/4 when on). The deliverable is a **four-control emergence protocol**: scrambled-MI null · **frozen-genome control** · **causal lesion** · **intact-vs-deaf survival**. REAL-VERIFY (3 seeds × 3 cond × 8000 steps, panel + utterance-coloured 3D GIF eye-verified): genuine alarm communication did NOT emerge — evolved signal-danger MI **0.0037 ≤ frozen 0.0152** (sensory-reaction artifact), HEAR pop 2002 vs DEAF 2086 (**ratio 0.96, no survival benefit**), causal flee intact 0.148 ≈ deaf 0.149 (no adaptive listening), MI flat over time. The protocol correctly CAUGHT the artifact (禁止造假 working). 9 tests (809 total). Diagnosis → R145: deaf survives as well as hearing ⇒ no listening gradient ⇒ no honest-emission pressure; need real informational asymmetry (sender sees danger receiver can't) + kin-selection/cost for honest emission, then re-run the SAME protocol. |
| R143 | **GENESIS Stage-1: co-evolutionary ARMS RACE** — a second evolved-neural PREDATOR species hunts the prey; prey gain a predator-sense channel (brain n_in 9→13) and evolve EVASION. Additive; n_predators0=0 byte-identical to R141/R142. REAL-VERIFY (16k-step 3D run): living predator-prey ecology with **boom-bust cycles**, **coexists 3/3 seeds** (no extinction); prey flee-directedness evolves windowed **+0.231 vs +0.090 frozen** (every seed), foraging still evolves under predation. 4 tests (800 total). HONEST: coexistence is a knife-edge (cap 1200→prey extinct, 350→pred extinct, 550 coexists); arms race one-sided (predators pin at cap in prey-rich phases — R34 limit), prey evasion evolves but not a clean symmetric escalation. Stage 1 (foundation→niches→arms race) complete. |
| R142 | **GENESIS Stage-1: monoculture BROKEN via resource niches** — `n_food_types` food types + heritable `diet` trait (each agent senses/eats only its own type = the trade-off) -> distinct specialist niches coexist (Gause competitive exclusion). Additive; n_food_types=1 byte-identical to R141. REAL-VERIFY: 16k-step K=3 run, **3D GIF eye-verified (red+green+blue diet specialists coexist)**, diet diversity locks at **3.00**, directedness still evolves to **+0.106**, lineage diversity ~1.9 (≈2× monoculture). RED-TEAM 3 seeds: K=1 diet-div 1.00/1.00/1.00 vs K=3 3.00/3.00/3.00. 4 tests (796 total). Seeds Stage-3 division of labour. HONEST negative: spatial food patchiness (food_mode="patches") tried FIRST and did NOT break monoculture (identical patches + migration → still swept) + broke the directedness readout; resource partitioning is what worked. |
| R141 | **GENESIS Stage-1 foundation** (`alife/genesis/`) — a persistent, real 3D living world with embodied agents driven ENTIRELY by evolved `brain.py` genomes (no GA, no fitness function, no scripted movement); in-situ selection via food scarcity, kin-adjacent reproduction, fixed body, checkpoint/resumable. Built ON brain/world3d/render3d/bigworld3d(KD-tree)/coevo3d/evolve3d. REAL-VERIFY: 16k-step run, **3D GIF eye-verified** (lineage-coloured agents, diverse→monoculture colour-convergence), foraging directedness evolves 0→**+0.166**, food-limited pop ~2400 (<6000 cap), **65 generations** deep. RED-TEAM 3 seeds: evolve +0.170/+0.153/+0.211 vs frozen +0.063/+0.104/+0.078 (every seed positive, mean delta +0.096) — heritable, not a metric artifact. 11 tests (792 total). HONEST: evolution sweeps to MONOCULTURE (lineage diversity →1.0 vs frozen 2.8) — diversity/niches is R142's target. First rung of the staged ladder to civilization. |
| R140 | **REVIEW round** (milestone, 130 modules / 781 tests). (1) Full suite ALONE: 781 passed in 14m57s, 0 fail. (2) Adversarial fresh-seed re-verify of R131-R139 headlines on UNSEEN seeds (primes ≥41, tests use {0-4,7,11}): 17/17 survived — BZ spiral+rings, wolf-sheep coexist+boom-bust (lag-sign honestly excluded — not seed-robust, test rewritten to assert the robust CV signature instead), termite stigmergy-vs-random, murmuration 273-vs-2 catches (137× protection), Faraday k*=resonance + subharmonic Ω/2, grain power-law + greedy-pin control, Fisher c≈2√(rD) + symmetric Allee sign-change ±0.282, Turing-sphere 18→41 spots size-law, dendrite arm=j + 4× anisotropy growth. (3) Milestone gallery (run_gallery_r140.py) rendered + eye-verified — all 9 signatures correct. (4) De-slop: deleted 5 stale per-round gallery stubs + review_r2.workflow.js, fixed 5 dead `if False` branches, refreshed R1-frozen __init__ docstring. (5) Docs: README/CODEBASE_GUIDE/QUICKSTART counts → 130/781, README trimmed to CEO-R91 (no per-round catalog). (6) Architecture audit: HEALTHY (acyclic DAG, no god-objects, largest 237L); one deferred dedup (5-pt Laplacian copy-pasted ×12 → a future alife/stencil.py). (7) Ambition-critic verdict drove the next direction (below). |
| R139 | Dendritic solidification (dendrite.py) — a snowflake crystal from an undercooled melt (Kobayashi 1993 phase field). Phase p (1=solid) couples to temperature T; anisotropic gradient energy ε(θ)=ε̄(1+δ cos(j(θ-θ0))) + latent heat K∂p/∂t; Mullins-Sekerka tip instability + lattice anisotropy → j sharp primary arms + side branches. Eye+data: 6-fold (ice) + 4-fold (cubic) dendrites + side-branched (noise) crystal + latent-heat HALO in T. QUANT: arm count = anisotropy mode j (angular-FFT of tip-radius profile; j=4→4, j=6→6 = measured equals set parameter); anisotropy DRIVES growth (δ=0.04 solid-frac 0.40 vs δ=0 0.10). HONEST: 'fat' dendrites not fine needles; square-grid Laplacian → spurious 4-fold at δ=0 and j≥8 (claim only j=4,6 physical cases); signs validated empirically vs saved probe. DISTINCT mechanism from snowflake (Reiter hexagonal vapour-CA) + dla (random-walk aggregation) — continuum PDE w/ latent-heat coupling + tunable anisotropy; retires deferred dendrite frontier. VISUAL: 6-fold+4-fold+side-branched crystals + T halo + arm=j bars + growth-vs-δ + 35-frame growth GIF |

## Honest notes (what did NOT work, recorded so they aren't re-tried blindly)
- **Liesegang periodic precipitation rings — clean Jablczynski spacing law would NOT form robustly (R136, 3 probes, PIVOTED to grain growth).** The Ostwald supersaturation / Keller-Rubinow model (outer ion a diffuses into gel of inner ion b, a+b→c, c precipitates above a nucleation threshold then grows) is notoriously parameter-sensitive. With weak autocatalysis + easy nucleation I got ~5 bands but BUNCHED near the source with irregular spacing (ratios 0.22/1/1, not the increasing geometric progression); with strong autocatalysis + hard nucleation the first band's growth consumed the whole moving reaction front → 1-2 continuous bands, no banding. The clean √t time-law + geometric spacing regime is narrow and likely needs a better-formulated model (explicit moving-front + Ostwald ripening, or the 2D radial induced-precipitation model). DEFERRED — revisit with a literature-faithful precipitation model, not the simple autocatalytic-deposition tweak.
- **Viscous fingering / Saffman-Taylor via discrete DBM + surface tension did NOT work (R133).** Adding a neighbour-count "surface tension" bonus to the dielectric (DBM) growth weight barely changed the morphology — all stayed DLA-fractal (D~1.6), because the harmonic-field SCREENING of fjords dominates the local curvature bonus. Proper Saffman-Taylor needs a continuum phase-field / curvature-based interface advance, not a discrete-DBM tweak. PIVOTED to termite stigmergy. (Viscous fingering deferred — needs a real moving-interface solver.)
- **Termite stigmergy gives irregular mounds, not regular pillars (R133).** Pure positive-feedback deposition COARSENS (rich-get-richer) into irregular mounds; height-saturation to force lateral spacing instead went uniform. Regular 3D-nest pillars need an activator-inhibitor (short-range build + long-range inhibit) — frontier. The clumping-vs-flat (stigmergy on/off) result is solid and shipped.
- **Couzin (2002) zonal model would NOT mill (R123).** 3 parameter sweeps (zoo/zoa/θ_max, then + a rear blind-spot perception cone) never produced a coherent milling torus — got cohesive disordered swarms or fragmentation (best M~0.18). The Couzin torus is a genuinely narrow/finicky regime (depends on N, density, exact params). PIVOTED to the D'Orsogna self-propelled-particle model which mills robustly (M~0.96 across params) — use that for milling, not Couzin.
- **In-situ ecosystem selection on brains (R3 negative — RESOLVED in R33).** R3 found in-situ
  selection too noisy *in a cap-limited, food-dense regime* (population pins at the cap, eating is
  opportunistic, skill stops mattering). R33's capstone (alife/ecosim.py) shows it works once the
  ecology is strictly **energy-limited**: a generous pop cap so food is the real limiter, scarce food,
  movement costs energy, expensive reproduction. Directed foraging then evolves with no GA at all —
  directedness 0.08→0.33, population self-regulates well below the cap, lineages 25 generations deep.
  The R3 negative was about the *regime*, not in-situ selection per se.
- **R31 morphology — locomotion is mostly but not purely gait-driven.** Muscle-ablation (R32 review):
  an evolved creature travels 48.7 with muscles vs 11.6 with muscles zeroed, so ~24% of the distance
  is passive (largely the initial fall/settle, plus some asymmetric-body creep). The gait dominates
  (2nd-half-of-rollout movement of ~26 units can't be passive), but the headline distance is not 100%
  gait. Reported as-is; a cleaner metric would subtract a passive-body baseline.
- **R6 memory (resolved in R26):** evolved recurrence did not beat a memoryless control on the R6
  *foraging* tasks because those tasks didn't *require* memory — reactive policies stayed competitive.
  R26 settles it with a task that provably requires memory (delayed-cue latch, alife/memory_task.py):
  RNN reaches 1.0 held-out, FF is pinned at exactly 0.5 by construction. The R6 negative was about
  the task, not the architecture.
- **Predator–prey balance is a knife-edge** (R5/R10/R14): max predator intake
  (energy_per_catch / handling) must exceed upkeep; predators capped/limited below prey. Stable
  coexistence is easy; sustained cycles needed the R15 refuge-floor mechanism.

## Frontier / next

### CEO DIRECTION SHIFT (2026-06-20, R140) — GENESIS: a living 3D world that grows a civilization
Yusen steered the loop to a new major frontier: **build a real, alive 3D world that — just by running
locally or in the cloud — freely develops toward a CIVILIZATION, populated by genuinely autonomous
creatures (evolved minds, not scripts).** This is now the STANDING direction; the single-phenomenon
demo arc is retired.

**Progress: GENESIS Stages 1, 3, 4 & 5 COMPLETE — the full ambition ladder is done (Stage 2 signalling parked).** R141 foundation (3D evolved-neural world, behaviour evolves) →
R142 niches (resource partitioning → 3 coexisting diet specialists, monoculture broken) → R143 arms race
(co-evolving predator, boom-bust coexistence 3/3 seeds, prey evolve evasion +0.231 vs +0.090). The world
now evolves, sustains diverse strategies, and stays alive under predation. Lessons banked: spatial
patchiness alone fails (need DIFFERENT resources + a trade-off, Gause); predator coexistence is a knife-edge
(cap ~0.2× prey); a clean two-sided arms race is hard (R34 limit).
**Stage 2 = EMERGENT SIGNALLING → language. [R144 + R145: substrate + 4-control protocol built; emergence
NOT achieved — TWO honest negatives. Rung PARKED, loop PIVOTS to Stage 3.]** The channel + protocol work and
demonstrably *catch the artifact*. R144 (no relatedness) and R145 (clonal demes, r=0.90) both returned clean
negatives across seeds: evolved MI ≤ frozen (sensory-reaction artifact), hear≈deaf survival, causal lesion
flat/negative. **Key finding: relatedness is necessary-but-not-sufficient** — at r=0.90 emergence still did
not happen, so the wall is the **signalling bootstrap deadlock** (no honest signal → no listening gradient →
no emission payoff), which kin selection alone doesn't break because the marginal benefit of one alarm is
swamped by foraging/evasion noise. **Breaking it needs a SUBSTRATE change, not another parameter sweep:** a
sharp synchronous selective-event structure (discrete predation "rounds" where a missed warning is reliably
lethal and a heeded one reliably saves — the Floreano/Mitri foraging-arena design), or explicit fitness
coupling. This is deferred as a future Stage-2 redesign. When Stage 2 is revisited, believe emergence ONLY if
it beats frozen AND deaf AND causal, ≥3 seeds, red-team.

**Stage 3 = COOPERATION / DIVISION OF LABOUR. [R146 attempt 1 NEGATIVE → R147 attempt 2 POSITIVE — STAGE 3
DONE.]** R146's two-stage economy worked but generalists dominated (no specialization trade-off). R147 added a
heritable caste trait `spec` with **CONVEX returns** (harvest `(1-spec)^4`, process-reach `∝spec` so volume
`∝spec³`, plus a wage `process_payment` paid to whoever ripened a harvested mote) and the population split into
a genuine **bimodal processor/harvester caste** (BC 0.90), with the role↔caste alignment **built by selection**
(caste-gap 0→+0.32 over the run, ~0 frozen; `spec` is not even a brain input) and the specialised economy
out-producing force-generalist (evolve 2451 > frozen > forcegen 1753). Red-teamed: 5/5 seeds, castes spatially
INTERMIXED (NN same-caste ≈ random = real DoL not segregation), interdependence confirmed. **Key lesson:
specialization only pays under STEEP convexity (gamma=4) — at gamma=2 generalists still win (the population
collapses to one intermediate spec); shallow increasing-returns is not enough to split a caste.** Current
ceiling = a two-caste trading economy.

**Stage 4 = BUILDING / NICHE CONSTRUCTION. [R148 POSITIVE — STAGE 4 DONE.]** `building=True` (requires
`processing`) lets an agent deposit/reinforce a PERSISTENT hearth structure (a fixed-capacity SoA pool, free-slot
reuse) via the evolved process-gate output (reused as a BUILD gate), paying `build_cost`. Raw food ripens ONLY
near a hearth, with **CONVEX reach** (`reach = min(cap, ~3·strength)` so ripened volume ~strength³ — the R147
convexity lesson re-applied) so concentrated building beats scattered deposits. Hearths DECAY unless re-invested,
so a standing hearth OUTLIVES its builder = **ecological inheritance** (Odling-Smee). REAL-VERIFY (2500-step
hearth-coloured 3D + 3-seed controls, panel.png + GIF eye-verified): population bootstraps (dips ~640 as unsettled
agents starve) then recovers to ~2200 living almost entirely ON hearths (`near_frac` 0.96); `inherit_ratio` 6.2
(hearths 6× older than the realized lifespan), `inherit_frac` 1.0. **PERSISTENCE PAYS** — persistent built world
pop 1947 vs a `build_persist=False` ablation 1075 (1.8×); without persistence the settlement collapses
(`near_frac` 0.96→0.00). **RED-TEAM (passed):** hearths that ripen nothing → pop 0 (the food-ripening feedback is
CAUSAL, not epiphenomenal); 100% of tall hearths are maintained by builders ~17 generations LATER than their
founder (ACTIVE cross-generation inheritance, not just old structures sitting there). **HONEST caveats / lessons:**
(a) hearths TILE the world (the pool saturates at 600; the population settles uniformly, NO discrete villages —
Clark-Evans R≈1.26 = dispersed). There is a hard tension: broad food coverage (population viable) ⟂ few clustered
hearths (discrete settlements) — many tiny hearths starve the population, few hearths can't feed it. Discrete
villages need food to FOLLOW hearths (regrowth biased to settlements) or a much smaller capacity with a survivable
coverage floor — deferred. (b) building is STRUCTURALLY beneficial (frozen ≈ evolve): the niche-construction +
inheritance phenomenon does NOT require selection to appear — it is an ecological consequence of the build
mechanism, reported honestly rather than dressed up as an "evolved" win.

**Stage 5 = CUMULATIVE CULTURE. [R149 POSITIVE — STAGE 5 DONE; the full ladder is complete.]** `culture=True`
(requires building) makes the Stage-4 hearths a CULTURAL REPOSITORY. Each agent carries a LIFETIME-learned scalar
`tech` (a foraging technique) that is **NOT genetic** — a separate `Population.tech` array, never touched by
`mutate_brains`. A newborn ACQUIRES it in `_acquire_tech`: it copies (×`culture_fidelity`) the best technique
recorded at the nearest strong hearth (an artifact carrying ancestral knowledge) or its parent, then adds ONE
positive innovation step `max(0, N(innov_mean, innov_sigma))`. Higher `tech` multiplies harvest energy
(`1+tech_gain·tech`) so it is selected — but every generation must RE-LEARN it, so the accumulation lives in
transmission + the built world, not the genome. A build act WRITES the builder's tech into the hearth record
(keeping the max), so the record RATCHETS across generations (Tomasello). Brain shape is UNCHANGED vs building
(tech is automatic, not a brain output), so culture=False is the R148 world byte-identical. REAL-VERIFY
(scripts/run_genesis_culture.py, 2500-step technique-coloured 3D + controls; panel.png + GIF EYE-VERIFIED — the
population visibly BRIGHTENS dark-indigo→bright-gold as culture accumulates, mean frame brightness 24→51):
**FALSIFIABLE headline tech_mean cumulative 12.93 vs ASOCIAL (learn=False) 0.19 = 66.6×**, 3/3 seeds — and the
asocial mean sits pinned EXACTLY at innov_mean (0.19), i.e. one innovation, zero accumulation. **CULTURAL NOT
GENETIC:** with evolve=False (frozen genome, exact-copy children) tech_mean still climbs to 12.98. **FIDELITY
THRESHOLD (Lewis & Laland):** monotone dose-response 0.99→23.1, 0.90→5.85, 0.70→2.62, 0.50→1.82 — below a
critical fidelity copy-loss > innovation and the ratchet collapses to the asocial ceiling. **RED-TEAM
(independent general-purpose agent, refutation-first): CONFIRMED.** (a) the asocial ceiling is STRUCTURAL not a
small-N artifact — it's a max-order-statistic ~√logN that only reaches ~1.25 even at N=5×10⁵, never the cumulative
~13; (b) NO genetic leakage — `tech` is structurally disjoint from `brains`, written only in `_acquire_tech`; (c)
the fidelity dose-response cannot be faked by a circular metric (at fidelity 0 the learning path is exercised but
transmits nothing → falls to the asocial value). **HONEST caveats (applied to the writeup):** the headline now
LEADS the FALSIFIABLE `tech_mean` (which COLLAPSES toward the asocial ceiling within a few generations if
transmission stops — red-team measured 2.53→0.69) rather than the near-monotone `tech_max`/`hearth_tech_max`
high-water mark (a record that one surviving high-tech agent or one never-reset hearth slot can pin). And
"OPEN-ENDED / keeps climbing" was OVERSTATED — the ratchet is fidelity-BOUNDED, climbing toward a finite fixed
point ~innov/(1-fidelity) (high — tens — but saturating), softened throughout. Genuinely open-ended culture
(combinatorial innovation, ideas-beget-ideas) is a future frontier. Believe any stage positive ONLY if the
signature is robust ≥3 seeds AND beats the right control, red-teamed (the R146 8× clonal fluke is the cautionary
tale).

Locked decisions (CEO, R140):
- **Civilization bar = BOTH, staged** (the full living world, longest road, richest result). Ambition ladder:
  1. **Foundation + niches** [R141 foundation · R142 niches · R143 arms race DONE] — a persistent 3D world with embodied agents driven by **evolved neural brains**;
     sensing, movement, metabolism/energy, reproduction, death; behaviour genuinely EVOLVES as it runs.
  2. **Emergent signalling → language** [R144 + R145: substrate + 4-control protocol built; emergence NOT
     achieved across TWO honest negatives (no-kin + high-kin r=0.90) — rung PARKED for a substrate redesign] —
     agents evolve a shared communication code from scratch (Lewis/Skyrms signalling, naming-game / iterated
     learning); measure mutual-information / compositionality rising above frozen+deaf+causal controls.
  3. **Cooperation + division of labour** [R146 attempt 1 negative → R147 attempt 2 POSITIVE, DONE — convex
     specialization trade-off → bimodal processor/harvester caste, selection-built role alignment, mix > monomorphic] — roles + specialisation emerged.
  4. **Building / niche construction / economy** [R148 POSITIVE, DONE — evolved persistent hearths; population
     reshapes its world to eat and lives on a self-built, INHERITED environment maintained across ~17 generations;
     persistence pays 1.8× pop; red-teamed causal. Caveat: tiles the world, not discrete villages] — agents reshape
     the 3D world; an inherited built environment the population depends on (niche construction, beyond R133 stigmergy).
  5. **Cumulative culture** [R149 POSITIVE, DONE — non-genetic lifetime `tech` socially learned through the built
     world (hearths = repository); tech_mean cumulative 66.6× the asocial one-lifetime ceiling, 3/3 seeds; climbs
     with frozen genes (cultural not genetic); Lewis-Laland fidelity threshold; red-teamed CONFIRMED. Caveat:
     fidelity-BOUNDED ratchet (~innov/(1-fidelity)), not literally unbounded] — learned knowledge passes across
     generations (a cultural ratchet) → proto-civilization. **THE FULL LADDER (1,3,4,5) IS NOW COMPLETE; Stage 2
     signalling parked.**
- **Mind substrate = evolved neural brains** (brain.py lineage): each agent = a NN genome, evolves across
  generations via mutation/recombination, plus light lifetime adaptation (Hebbian / small RL tweak).
  Scales to 1e3–1e5 agents on CPU/GPU. Open-endedness comes from evolution + niche construction, not scripting.
  Hybrid escalation allowed later: graft heavier learned cognition (RL / world-model) onto successful lineages once the world is alive.
- **3D + visually-checkable + genuine emergence.** Acceptance = run the world, render 3D, WATCH behaviour
  evolve, measure it, and red-team every "it's really evolving / a convention crystallised / culture
  accumulates" claim before believing it. NEVER scripted theatre (Yusen: 不是简单的测试，真的有自主意识的生物发展).

### Frontier (post-R150 — full ladder built AND culture now open-ended; what raises the ceiling now)
Current ceiling: each ladder rung (foundation/niches/arms-race/DoL/niche-construction/culture) is proven IN
ISOLATION via its own flag, and culture is now OPEN-ENDED (R150 combinatorial tech tree — accelerating, no
dynamical fixed point). The next leaps in KIND:
- **(default next) INTEGRATED CAPSTONE — one world, all stages at once.** Turn building+specialize(DoL)+culture
  (now combinatorial) ON together (they already compose: culture⊂building⊂processing; specialize⊂processing)
  and verify the phenomena COEXIST — a settled, caste-divided population accumulating open-ended culture on an
  inherited built world. This is the actual "living civilization," not six separate demos. Risk: the regimes may
  interfere (caste convexity vs the tech-level harvest multiplier); needs a viable joint regime + multi-panel.
- **COUPLE the tech tree to the 3D WORLD (make culture MATTER physically).** Today a technique only multiplies
  harvest energy (a scalar payoff). Next: techniques that UNLOCK new world-actions — new build types, food
  processing recipes, tools, faster movement — so cultural DEPTH changes what agents physically DO and the
  combinatorial frontier reshapes the world (a real tech-driven economy), not just a number. Highest ambition.
- **GENUINELY UNBOUNDED tech space (lift the deliberate cap).** R150's ceiling is `max_techniques` (a fixed
  pre-enumerated tree). Make techniques GENERATIVE — a new technique IS the pair of its parents, created on
  combination — so the space is unbounded by construction (combinations of combinations). Gate: bounded memory
  via a hashed/interned id pool + a complexity metric (max depth) that provably keeps climbing; red-team for
  numeric explosion vs genuine structure.
- **Stage-2 SIGNALLING redesign (the one parked rung).** Two honest negatives (R144/R145) traced to the
  signalling-bootstrap deadlock; the diagnosed fix is a SUBSTRATE change — synchronous, sharply lethal predation
  "rounds" where a missed warning reliably kills and a heeded one reliably saves (Floreano/Mitri arena). Only
  revisit with that redesign; believe emergence ONLY if it beats frozen AND deaf AND causal, ≥3 seeds, red-team.
- **Scale + discrete settlements:** the R148 hearth caveat (hearths TILE the world, no discrete villages) — make
  food regrowth FOLLOW hearths so settlements become discrete; and push N toward 1e4–1e5 via the GPU path.

Why this direction (ambition-critic, R140): the R120–R139 arc became a **physics demo zoo** — ~20 isolated
single-phenomenon PDE/CA renders, each verified once, breadth at the cost of depth; nothing OPEN-ENDED,
INTEGRATED, or EVOLVING. The project's alive peak — the R33 capstone `alife/ecosim.py` (brains + energy +
in-situ selection in one living world) — was abandoned at R34. GENESIS revives and massively extends it.

### Reusable substrate already in the repo (build ON these, don't restart)
- `ecosim.py` (R33) — the energy-limited living world where directed foraging evolves with no GA (the seed to revive/scale).
- `brain.py` / `neuro.py` / `sensors.py` — NN genomes (forward/mutate), recurrence, sensing.
- `world.py` / `world3d.py` / `render3d.py` — toroidal + 3D arenas, moderngl 3D rendering (fog/glow/shadows).
- `evolve3d.py` / `coevo3d.py` / `predprey3d.py` / `bigworld3d.py` — 3D embodied ecologies (foragers, arms race).
- `morphevo.py` — evolving bodies (for embodied agents later); `signals.py` — signalling primitives (lexicon seed).
- `openended.py` / `navqd.py` / `noveltymaze.py` — QD / novelty-archive machinery (the open-ended complexity instrument).
- GPU compute path (R54–R60): SSBO + ping-pong + atomics, 1M agents, correctness-gated vs numpy — the scale lever.

### Engineering carry-overs / open items
- **R33 nuance (R36):** in-situ directedness is genuine natural selection (sorts standing variation even with
  mutation off); cumulative mutation-driven innovation needs a longer horizon + the energy-limited regime. GENESIS must run LONG.
- **Arms-race knife-edge (R5/R10/R14/R34):** two-sided pursuit-vs-evasion escalation pins at population caps; GENESIS
  needs the energy-limited, refuge-structured regime + scale for open-ended coevolution to actually escalate.
- **Deferred tidy (R140 architecture audit):** 5-point toroidal Laplacian is copy-pasted verbatim in ~12 PDE
  modules → fold into a shared `alife/stencil.py` (lap5/lap9/grad/div) in a future round (a sign-typo in any copy
  is a silent physics bug). Low priority, do NOT destabilise the 12 verified modules in a tidy pass.
- **Fidelity/stack ladder:** numpy 2D → numpy 3D + moderngl GPU → KD-tree (~10k) → GPU compute shaders (1M agents).
  torch (CPU available, RTX 5080 / CUDA 13 local) is the lever for heavier per-agent cognition later.
- **Status: published & synced** (origin/master public through R140). Loop runs divergently under standing order;
  only push/publish/delete-other-projects gate (push pre-approved each round).
