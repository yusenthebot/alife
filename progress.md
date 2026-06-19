# alife — progress

## Current state (Round 117 — 2026-06-19)

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
**R117: Turing on a growing domain — stripes INSERT to hold their wavelength as the domain grows (n∝L)**.
**625 tests pass.** PUBLISHED & SYNCED through R117 on public
github.com/yusenthebot/alife. A real-fluid swimming arc runs R101
(lattice-Boltzmann) → R102 (undulatory swimmer) → R103 (evolved gait). A network-science arc runs R83 (scale-free)
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
