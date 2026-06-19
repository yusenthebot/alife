# alife — progress

## Current state (Round 91 — 2026-06-18)

R90 was a review round: adversarial re-verification (fresh seeds/params) confirmed all four recent
headline claims hold; workspace tidy; R81–R89 milestone gallery at `runs/r90_review/gallery.png`.

An evolving artificial-life ecosystem built from zero over 91 autonomous rounds. The full stated
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
**R91: Evolved Particle Life — selection discovers self-propelled matter (the asymmetry is the engine)**.
**463 tests pass.** PUBLISHED & SYNCED through R91 on public
github.com/yusenthebot/alife (origin/master = 78f15df). A network-science arc runs R83 (scale-free)
→ R84 (epidemics) → R87 (small-world). An origin-of-life arc runs
R44 (error threshold) → R62 (autocatalytic sets) → R63 (hypercycles, Eigen's answer).

Status: well past the stated goal and into a long frontier tail (running divergently under standing
order to keep going until told to stop; each round commits + pushes). Each round adds a genuinely
distinct ALife phenomenon, real-run + eye-verified, never faked.

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

## Honest notes (what did NOT work, recorded so they aren't re-tried blindly)
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
- **The capstone (R33) ties the project together:** brains + sensing + energy + reproduction +
  in-situ natural selection in one living world, behavior evolving as you watch — the original vision
  realized as ONE system, not a collection of demos. Both big ambition-critic leaps (open-endedness
  R28–R30, morphology R31) and the longest-standing open problem (R3 in-situ selection) are now done.
- Ways to push the capstone further: **(a) put evolved MORPHOLOGY creatures in the living world**
  (body+brain+ecology in one); **(b) in-situ speciation / niches**; **(c) sexual reproduction +
  recombination**. (R34 added in-situ predators — coexistence + prey evasion robust; a clean
  two-sided arms race resisted tuning, see honest note.)
- **R33 red-team nuance (R36):** the in-situ directedness gain is genuine natural selection (a no-mutation
  run still rises by *sorting the initial random brains'* standing variation; R35's tracking, by contrast,
  fully collapses with mutation off — confirming that one needs heritable innovation). Over ~5k steps
  mutation adds little to R33 beyond selecting standing variation (and carries slight load). So R33 is
  honestly "selection acting in situ," with cumulative mutation-driven innovation a smaller effect on
  that horizon. Not an artifact — directedness depends on the energy-based life/death regime.
- **R34 honest note:** in-situ predator–prey coexists robustly via a Huffaker refuge and prey reliably
  evolve evasion, but a clean *two-sided* arms race (pursuit ALSO rising) did not materialize — the
  predator population pins at its cap and prey are abundant, so pursuit selection is weak; predators
  also get pursuit "for free" from a sensor that points at prey. Reported as the data shows it; this
  is the same R5/R10/R14 knife-edge the project has hit before.
- Remaining heavy leap: a **GPU-compute scale jump** (JAX/taichi → 1e5–1e6 agents / faster physics).
  Scripted-phenomenon modules are at deep diminishing returns; the live frontier is the integrated world.
- **R25 note:** pure-zero-start Fisher sits on the unstable equilibrium and does not bootstrap;
  a small seeded preference (the sensory-bias origin of ornaments) is needed to trigger runaway —
  this is the correct theoretical result, not a hack. Per-generation genetic correlation is small
  but persistently positive; the runaway and the dose-response are the robust signatures.
- **Fidelity/stack ladder:** numpy 2D → numpy 3D + moderngl GPU (fog/glow/shadows) → KD-tree scale
  (~10k+) → **GPU compute shaders (R54–R60): 1M agents, SSBO+ping-pong+memory_barrier+atomics,
  correctness-gated vs numpy.** Proven toolkit for any future megascale ALife.
- **Status: published & synced** through R61 (origin/master public). Loop runs divergently under
  standing order; only push/publish/delete-other-projects gate (push now pre-approved each round).
