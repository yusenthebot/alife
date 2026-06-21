"""GenesisWorld — the persistent in-situ 3D living world.

Every step: each living agent senses (body-frame nearest food + nearest neighbour + own energy),
runs its evolved brain forward, accelerates and moves, pays metabolism, eats food it reaches,
dies of starvation or old age, and — if rich enough — reproduces by splitting its energy and
spawning a MUTATED-brain child in a free slot ADJACENT to itself (kin structure, pre-installed for
later signalling stages). Food regrows on a cap. There is no GA, no fitness function, no scripted
movement: selection is purely in-situ via food scarcity, so competence is *evolved*.

`evolve=False` freezes the genome (children are exact copies, no mutation) — the red-team control:
foraging skill should rise under evolution and stay near the random baseline when frozen.

The world is checkpointable (save/load_checkpoint) and resumable, so it runs unattended for >=1e5
steps. Body parameters are fixed and identical for all agents (the neuro.py discipline), so any gain
is attributable to the brain. Stage 2 (R144) activates an emergent SIGNALLING channel — with
`signalling=True` each prey emits an evolved scalar utterance and hears its nearest neighbour's, so
predator-alarm communication can evolve from scratch (see signal_causal_test + metrics.signal_world_mi).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import numpy as np
from scipy.spatial import cKDTree

from .. import brain
from ..brain import BrainSpec
from ..bigworld3d import _resolve, _sense_kd
from ..coevo3d import _act
from ..evolve3d import _body_frame
from ..world3d import World3D
from . import metrics
from .agents import PopConfig, Population

N_IN = 9   # food body-dir(3)*prox + prox, neighbour body-dir(3)*prox + prox, own energy
N_OUT = 3  # 3D acceleration in the body frame


@dataclass(frozen=True)
class GenesisConfig:
    world: World3D = field(default_factory=lambda: World3D(size=140.0))
    capacity: int = 6000           # hard memory bound (food, not this, limits the population)
    n0: int = 1500
    # food economy — scarce so foraging skill matters (strong in-situ selection)
    food_cap: int = 900
    food_regrow: int = 22
    food_value: float = 26.0
    eat_radius: float = 3.0
    # life
    e_start: float = 60.0
    e_repro: float = 90.0
    e_max: float = 105.0           # can't hoard -> must keep foraging
    base_cost: float = 0.11        # existence costs -> idlers starve
    move_cost: float = 0.05
    max_age: int = 1600            # turnover -> continual selection
    birth_jitter: float = 2.0      # child spawns this close to the parent (kin adjacency)
    # fixed body (identical for all -> any gain is the brain)
    speed: float = 3.0
    force: float = 0.5
    min_speed: float = 0.6
    sense_range: float = 32.0
    # genetics
    mut_rate: float = 0.2
    mut_sigma: float = 0.35
    n_hidden: int = 10
    # food spatial structure: "uniform" (R141 baseline) or "patches" (R142 — clumped food at fixed
    # centers regrowing locally; with kin-adjacent reproduction this makes semi-isolated demes so
    # distinct lineages hold distinct patches -> a spatial mosaic instead of a monoculture sweep)
    food_mode: str = "uniform"
    n_patches: int = 10
    patch_radius: float = 8.0
    # resource partitioning (R142 — break the monoculture): n_food_types>1 splits food into types;
    # each agent has a heritable diet preference and eats/senses only its own type (the trade-off),
    # so distinct food types support distinct specialist lineages = coexisting niches (Gause). n=1
    # is the exact R141 single-resource world (no diet, no extra RNG draws).
    n_food_types: int = 1
    diet_mut_sigma: float = 0.12
    # co-evolutionary predator (R143 — arms race): n_predators0>0 adds a SECOND evolved-neural species
    # that hunts prey. Prey then gain a predator-sense channel (brain n_in 9->13) so they can evolve
    # EVASION; predators sense nearest prey and pursue. n_predators0=0 is the exact R141/R142 prey-only
    # world (prey n_in stays 9, no predator code path, byte-identical).
    n_predators0: int = 0
    pred_capacity: int = 550           # ~0.2x prey (predprey3d's coexistence ratio): low enough not to
                                       # overexploit, high enough to persist as prey evolve evasion
    pred_e_start: float = 140.0
    pred_e_repro: float = 200.0
    pred_e_max: float = 250.0
    pred_base_cost: float = 0.48       # starves without prey, but not faster than it can hunt
    pred_move_cost: float = 0.05
    pred_speed: float = 3.35           # faster than prey (3.0) so the chase is real (predprey3d ratio)
    pred_force: float = 0.34           # ...but less agile -> prey can juke (evasion can pay)
    pred_max_age: int = 2400
    catch_radius: float = 3.5
    prey_energy_value: float = 42.0    # a catch's energy: enough to persist, low conversion = Type-II
    pred_handling: int = 38            # digestion cooldown (Type-II stabilizer)
    # emergent signalling (R144 — Stage 2): signalling=True activates a communication channel — each
    # prey emits a scalar UTTERANCE (an evolved extra brain output) and senses its nearest neighbour's
    # previous-step utterance as a NEW input. Over the existing kin-adjacency this can evolve into
    # honest predator-alarm signalling (Floreano/Mitri kin-selection route). signalling=False keeps the
    # prey brain at its R143 shape, no utterance state, byte-identical.
    signalling: bool = False
    prey_pred_range: float = 0.0       # if >0, prey DIRECT predator-sense range, SHORTER than sense_range
                                       # -> a neighbour closer to the predator can warn earlier (the
                                       # sentinel value that makes an alarm call pay). 0 = full sense_range
                                       # (R143 behaviour, byte-identical).
    # kin selection (R145 — make an alarm call actually PAY). R144's honest negative traced to ~zero
    # relatedness: n0 distinct founder genomes mix freely, so warning a neighbour helps a stranger and the
    # signalling allele can't spread (Floreano & Mitri 2009: communication evolves under HIGH relatedness,
    # collapses without). n_founder_genomes>0 founds the prey as that many CLONAL demes — one random genome
    # per deme, all its members dropped in a tight spatial cluster sharing one lineage id — so a prey's
    # nearest neighbour is overwhelmingly its clone and warning it propagates the caller's OWN genes
    # (Hamilton's rb>c). 0 = R141..R144 founding (n0 distinct genomes), byte-identical.
    n_founder_genomes: int = 0
    founder_cluster_radius: float = 7.0
    # honest-signalling cost (R145): a small per-step energy cost proportional to |utterance| keeps SILENCE
    # the default, so an evolved non-zero signal is one selection actually paid to keep (Zahavi handicap /
    # cost-of-signalling) — guards against free noisy babble passing as meaning. 0 = signalling is free.
    emit_cost: float = 0.0
    signal_bins: int = 4               # quantile bins for the signal-MI read-out
    deaf: bool = False                 # functional control: channel present in the brain but heard is
                                       # forced silent. Compared against signalling=True (intact), this
                                       # is the ARTIFACT-IMMUNE test — does HEARING causally help, holding
                                       # brain shape fixed? (MI alone is fooled by sensory-reaction mimicry.)
    # division of labour (R146 — Stage 3): processing=True makes food spawn RAW (inedible); an agent
    # ripens nearby raw food into edible food via an evolved PROCESS output (an extra brain output), paying
    # process_cost. Ripe food is a LOCAL PUBLIC GOOD — any neighbour can harvest it — and decays back to raw
    # after ripe_ttl, so it is a continuous FLOW, not a stock. With clonal kin demes the costly processing
    # pays (Hamilton, rb>c), and a RESPONSE-THRESHOLD division of labour can emerge: agents process when
    # local ripe food is scarce and harvest when it is abundant (a self-organised processor/harvester mix).
    # Prey gain a nearest-RAW-food sense channel so they can navigate to processing sites. processing=False
    # is the R141..R145 world (all food edible, no extra channel), byte-identical. Assumes n_food_types==1.
    processing: bool = False
    process_radius: float = 7.0        # a process act ripens raw food within this radius of the processor
    process_cost: float = 2.5          # energy a successful process act costs (keeps harvesting attractive)
    ripe_ttl: int = 70                 # ripe food reverts to raw after this many uneaten steps (the flow)
    scramble_allocation: bool = False  # ablation: replace the evolved process gate with a Bernoulli draw at
                                       # the population's CURRENT mean gate rate -> identical processing
                                       # BUDGET, but allocation conditioning destroyed. Isolates the value
                                       # of the division of labour (conditional allocation) on productivity.
    # caste specialization (R147 — Stage 3, attempt 2). R146's honest negative diagnosed WHY no division of
    # labour emerged: processing was cheap and non-exclusive, so generalists doing both were optimal — there
    # was no SPECIALIZATION TRADE-OFF. specialize=True adds a heritable caste trait spec in [0,1] (0=pure
    # harvester, 1=pure processor) with CONVEX (accelerating) returns to specialization, so a generalist is
    # strictly worse at both than a mix of specialists (the condition for division of labour, à la Adam
    # Smith / increasing returns):
    #   - harvest gain  = food_value * (1-spec)^spec_gamma   (only pure harvesters eat at full value)
    #   - process reach = process_radius * spec              (ripened-volume ~ spec^3 -> strongly convex)
    #   - a processor earns process_payment when a HARVESTER eats a mote IT ripened (a wage / trade): so
    #     processors live on wages, harvesters on food -> genuine economic interdependence, not a free public
    #     good. With spec_gamma>1 individual selection under negative-frequency dependence should split the
    #     population into a bimodal processor/harvester CASTE. specialize=False is the exact R146 world
    #     (uniform efficiency, no spec, no caste), byte-identical. Requires processing=True.
    specialize: bool = False
    # the caste regime (found empirically R147): STEEP convexity (gamma=4) makes an intermediate generalist
    # bad at BOTH tasks, so disruptive selection splits the population into two specialist castes; a good wage
    # makes the processor caste viable on trade alone. At the shallower gamma=2 generalists still win (the
    # population collapses to one intermediate spec — no caste), so convexity must be strong enough.
    spec_gamma: float = 4.0            # convexity of the specialization returns (>1 = increasing returns)
    spec_mut_sigma: float = 0.1        # gaussian mutation of the heritable caste trait on reproduction
    process_payment: float = 18.0      # energy a processor earns per mote of ITS ripening that gets harvested
    force_generalist: bool = False     # productivity control: freeze every agent's spec at 0.5 (a forced
                                       # monomorphic generalist economy) -> isolates whether the EVOLVED
                                       # bimodal caste out-produces a non-specialized population.
    # niche construction / building (R148 — Stage 4). Beyond R147's TRANSIENT processor labour: building=True
    # lets an agent deposit a PERSISTENT structure (a "hearth") into the world via the evolved process-gate
    # output (reused as a BUILD gate), paying build_cost. A build act founds a new hearth at the agent's
    # position OR — if one is already within build_merge_radius — REINFORCES it (+build_gain strength), so
    # repeated building accretes into spatially clustered SETTLEMENTS (stigmergy without a scripted template).
    # Hearths DECAY (struct_decay/step): an un-maintained one fades over ~a lifespan, a continually re-invested
    # one persists indefinitely and so OUTLIVES its builder. The environmental feedback: raw food within
    # hearth_radius of a hearth strong enough (>=hearth_min_strength) ripens PASSIVELY each step — the
    # persistent structure does the labour a live processor did in R146/R147. Raw food ripens ONLY near hearths,
    # so the population must reshape its world to eat: niche construction with ecological inheritance (later
    # generations inherit and maintain ancestors' hearths). Requires processing=True (the raw/ripe economy +
    # raw-food sense); prey gain a nearest-hearth sense channel so they can navigate to settlements. The
    # process-gate output is REPURPOSED as the build gate (no extra output); _process (transient ripening) is
    # replaced by _build + passive hearth ripening. building=False is the R141..R147 world, byte-identical.
    building: bool = False
    struct_capacity: int = 600         # fixed hearth pool (bounded memory; reused free slots, never grows)
    build_cost: float = 2.0            # energy a build act costs (keeps pure harvesting attractive)
    build_gain: float = 1.0            # strength a build act adds (founds at this, or reinforces by it)
    struct_decay: float = 0.01         # strength lost/step: an unmaintained hearth fades over ~its strength*100
                                       # steps, so a tall settlement (strength~15) fades in ~1500 ~ a lifespan
                                       # if abandoned -> persistence REQUIRES cross-generation maintenance.
    build_merge_radius: float = 10.0   # build within this of a hearth reinforces it (stigmergic accretion ->
                                       # one tall settlement beats many scattered deposits, see reach below)
    # CONVEX returns to concentration (the R147 lesson applied to building): a hearth's ripening REACH grows
    # with its strength (reach = min(hearth_radius, hearth_reach_per_strength*strength)), so ripened VOLUME ~
    # strength^3. One settlement at strength 20 ripens far more than 20 scattered strength-1 deposits -> selection
    # concentrates building into few tall, shared, persistent settlements (not a uniform fertile sheet). A lone
    # deposit still ripens a small zone (a real reward), so there is no bootstrap deadlock.
    hearth_reach_per_strength: float = 1.6
    hearth_radius: float = 9.0         # MAX ripening reach of a hearth (the cap once it is tall enough)
    hearth_min_strength: float = 0.5   # below this a deposit is a dead ember: not sensed, ripens nothing
    build_persist: bool = True         # ablation: False -> hearths last a single step (NO ecological
                                       # inheritance) -> isolates the value of a PERSISTENT built environment.
    # division of labour AROUND niche construction (R152 — make Stages 3+4 COMPLEMENT, not substitute).
    # R151's capstone found that universal, caste-free building lets the persistent hearths ripen food for
    # free, so the processor caste is redundant and selected away — niche construction SUBSTITUTES for the
    # division of labour. build_specialized=True couples the two so a genuine BUILDER caste re-emerges and an
    # economy forms AROUND the built infrastructure:
    #   - build STRENGTH is convex in the caste trait (deposit = build_gain * spec^build_spec_gamma): a pure
    #     builder (spec=1) raises a strong hearth, a harvester (spec=0) deposits a dead ember -> only the
    #     builder caste can found/maintain settlements (the R147 convexity lesson applied to building);
    #   - a builder earns a WAGE (process_payment, reusing the R147 wage path) whenever a harvester eats food
    #     ripened by a hearth that builder last maintained -> builders live on maintenance wages, harvesters on
    #     the food itself, so value flows from the consumers back to the maintainers of the shared infrastructure.
    # The harvest convexity (builders eat ~0) + the maintenance wage split the population into a builder caste
    # that keeps the hearths and a harvester caste that exploits them -> the division of labour RE-EMERGES
    # around niche construction (Stages 3+4 COMPLEMENT). Requires building=True AND specialize=True.
    # build_specialized=False is the exact R148..R151 world (caste-free building), byte-identical.
    build_specialized: bool = False
    build_spec_gamma: float = 2.0      # convexity of build skill in the caste trait (>1: only high-spec build well)
    # cumulative culture (R149 — Stage 5). The Stage-4 hearths become a CULTURAL REPOSITORY. culture=True gives
    # each agent a LIFETIME-learned scalar `tech` (a foraging technique) that is NOT in the genome and is NOT
    # inherited genetically: a newborn ACQUIRES it by SOCIAL LEARNING — it copies (with `culture_fidelity`) the
    # best technique recorded at the nearest strong hearth (an artifact carrying ancestral knowledge) or its
    # parent, then adds ONE innovation step (max(0, N(innov_mean, innov_sigma))). A higher tech multiplies the
    # energy gained per mote (tech_gain), so good techniques are selected — but each generation must RE-LEARN
    # them, so the accumulation lives in the built world + transmission, not in the genome. A build act also
    # WRITES the builder's tech into the hearth's record (keeping the max), so hearths accumulate the best known
    # technique = a growing cultural record. With high fidelity the recorded tech RATCHETS up across generations
    # far beyond a single lifetime's innovation (Tomasello's ratchet), climbing toward a finite fidelity-set fixed
    # point ~innov/(1-fidelity) (cumulative + trans-generational, but bounded — not literally unbounded). The
    # FALSIFIABLE signal is the LIVING population's mean tech (tech_mean), which COLLAPSES toward the asocial
    # ceiling if transmission stops — unlike the hearth record, a never-reset high-water mark. Requires
    # building=True (hearths = the repository). Brain shape is UNCHANGED vs building (tech is automatic, not a
    # brain output), so culture=False is the R148 world byte-identical.
    culture: bool = False
    learn: bool = True                 # social-learning switch. False = ASOCIAL control: no copying (base tech
                                       # forced to 0), so each agent reaches only its own one-lifetime innovation
                                       # ceiling and the ratchet CANNOT form. The cumulative-culture acid test.
    culture_fidelity: float = 0.97     # fraction of a model's tech retained on copy. The Lewis-Laland ratchet
                                       # threshold: too low -> transmission loss > innovation -> no accumulation.
    innov_mean: float = 0.15           # mean of the one per-lifetime innovation step (only the positive part is
    innov_sigma: float = 0.25          # kept: tech = base + max(0, N(innov_mean, innov_sigma))).
    tech_gain: float = 0.35            # energy-per-mote multiplier is (1 + tech_gain*tech): tech pays, so it is
                                       # selected — but it must be re-learned each generation (it's not genetic).
    # OPEN-ENDED COMBINATORIAL culture (R150 — lifts R149's finite ceiling). combinatorial=True replaces the
    # scalar `tech` with a discrete REPERTOIRE of techniques on a fixed tech TREE (alife.genesis.combinatorial):
    # a technique k>=n_seed_tech is DISCOVERABLE only once both its prerequisite techniques are known (Kauffman's
    # adjacent possible / Arthur's combinatorial evolution). Newborns inherit a repertoire by social learning
    # (copy parent ∪ nearest-hearth record, each bit kept w.p. culture_fidelity) then make innov_steps discoveries
    # from their adjacent possible; `tech` (the harvest payoff) becomes the deepest LEVEL known, so mastery is
    # selected. Because the adjacent possible grows with the repertoire, discovery ACCELERATES and the population
    # repertoire (the open-ended complexity metric) keeps climbing — no intrinsic fixed point (only the deliberate
    # max_techniques cap). combo_prereqs=False is the ADDITIVE null on identical machinery (discover any unknown
    # technique, no gate -> a saturating ratchet). Requires culture=True. combinatorial=False is the R149 scalar
    # path, byte-identical.
    combinatorial: bool = False
    combo_prereqs: bool = True         # gate discovery on prerequisites (the combinatorial mechanism). False =
                                       # additive null: uniform discovery over all unknown techniques (saturates).
    max_techniques: int = 1500         # bounded tech-tree size (memory: capacity x this bits). Raise it and the
                                       # combinatorial climb keeps going — the ceiling is deliberate, not intrinsic.
    n_seed_tech: int = 6               # number of seed primitives (level-0, no-prerequisite techniques).
    innov_steps: int = 1               # discoveries attempted per newborn (from its adjacent possible).

    # --- R170: GENERATIVE (open-ended-by-construction) tech tree — open-endedness made CAUSAL in the live world ---
    # build_tech_tree pre-enumerates a FIXED random tree of max_techniques nodes whose deepest level is a
    # FROZEN ceiling: no matter how long the world runs the frontier cannot pass that pre-built max level.
    # generative_tree=True replaces it with combinatorial.GrowingTree — the live-world analogue of R164's
    # unbounded.TechSpace over the SAME dense rep: the tree starts with only the n_seed primitives and GROWS
    # FROM the living population's real compositions (compose two known techniques -> materialize a brand-new
    # deeper node on demand). The space is open-ended BY CONSTRUCTION; the only ceiling is the capacity
    # max_techniques (the memory cap). Cap it small and the frontier FREEZES once full; raise it and depth/
    # breadth keep climbing with run length — the decisive open-ended-vs-capped control, now causal in the
    # living evolved-neural world, not an offline analytical model. Every agent is guaranteed to know the
    # seed primitives (level-0 universals) so it can always compose. Requires combinatorial=True.
    # generative_tree=False is byte-identical to the fixed-tree path (build_tech_tree untouched). The fixed-node
    # recipe/capability gates (tech_actions/tech_capabilities, which designate SPECIFIC pre-built deep nodes ahead
    # of the run) cannot ride the generative tree (its deep nodes do not exist until the culture composes them) —
    # combining them raises ValueError; depth_gates (below) is the dynamic, open-ended replacement.
    generative_tree: bool = False

    # --- R171: DEPTH GATES — the open-ended grown tree CAUSALLY drives EMBODIED capability ---
    # R170 made the cultural repertoire open-ended (the grown tree's depth climbs with the cap, freezes when
    # capped) but left it an ABSTRACT scalar: nothing physical depended on how deep the culture had grown. The
    # fixed-node gates can't bridge that on a generative tree (their pre-designated node ids do not exist yet).
    # depth_gates instead gates physical capability on the agent's REALIZED CULTURAL DEPTH (pop.tech == its
    # deepest known technique LEVEL), which needs no pre-built node:
    #   - food tier t>=1 is edible ONLY by an agent whose culture has reached level >= recipe_level_step * t
    #     (a deeper tier demands a strictly deeper culture; tier 0 is the free resource);
    #   - capability axis i unlocks at level >= cap_level_step * (i+1) (axis 0 = locomotion speed, 1 = reach).
    # Because the generative tree's depth is OPEN-ENDED, the embodied diet/capability CEILING is open-ended too:
    # cap the tree small and depth freezes -> only the low tiers/axes ever unlock; raise the cap and the embodied
    # ceiling keeps climbing with it. This is the R170 caveat's next rung — open-ended culture is now CAUSAL on
    # the body, not just the repertoire. Requires generative_tree=True. depth_gates=False is byte-identical
    # (food_tier all-zero, no extra RNG, the eat/speed/reach paths unchanged). Mutually exclusive with the
    # fixed-node gates (it IS their generative replacement).
    depth_gates: bool = False

    # --- R156: emergent divergent cultural TRADITIONS over the open-ended tree ---
    # The combinatorial tree is open-ended, but R150-R155 only ever measured ONE global frontier. A real
    # civilization is not one monoculture of knowledge — it is MANY divergent cultural traditions. R156 asks
    # whether the EXISTING substrate already produces them: because oblique transmission copies the NEAREST
    # strong hearth (a spatial cultural store), a region that happens to climb one BRANCH of the adjacent
    # possible reinforces it locally (founder effect + path dependence), while another region climbs another
    # -> divergent traditions, measured as Wright's F_ST over the boolean repertoire (tradition_test).
    # panmictic_culture is the causal NULL: keep the SAME learners (same nearest-hearth in-range gate) but
    # copy a UNIFORMLY RANDOM strong hearth instead of the nearest one — destroying the place<->tradition
    # correlation, so F_ST collapses toward 0. The only manipulated variable is WHICH hearth you copy.
    # Requires combinatorial=True. panmictic_culture=False is byte-identical to R150 (exact nearest-hearth path).
    panmictic_culture: bool = False

    # --- R157: LOSSY / DECAYING cultural MEMORY (cultural loss — the Tasmania / Henrich effect) ---
    # R156 found traditions are real but MODEST (F_ST ~0.03). The cause: the hearth record is a UNION
    # accumulator (struct_rep |= every deposited technique; never forgets), so over a long run any
    # well-visited hearth drifts toward knowing the union of ALL branches -> the oblique channel HOMOGENIZES
    # and washes regional divergence out. culture_decay=True replaces the boolean union with a per-technique
    # floating MEMORY that DECAYS each step (memory_decay) and is REINFORCED (memory_reinforce) each time a
    # builder re-deposits that technique; a technique stays in the sensed/copyable record only while its
    # memory >= memory_threshold. So a hearth's record reflects what is ACTIVELY PRACTISED locally, not its
    # entire accumulated history: knowledge that is not maintained is LOST (cultural loss). A region that keeps
    # climbing branch A keeps A alive while a disused branch B fades below threshold, so local transmission
    # SHARPENS into discrete divergent cultures instead of a homogenized union. Requires combinatorial=True.
    # culture_decay=False is byte-identical to R156/R150 (the exact bitwise-or union path, no struct_memory).
    culture_decay: bool = False
    memory_decay: float = 0.02         # per-step fractional decay of each technique's hearth memory strength
    memory_reinforce: float = 1.0      # strength added to a technique's memory each time a builder deposits it
    memory_threshold: float = 0.5      # a technique is in the sensed/copyable record iff its memory >= this

    # --- R153: CULTURE UNLOCKS WORLD-ACTIONS (techniques gate what an agent can physically eat) ---
    # Until R153 the learned `tech` only multiplied a harvest SCALAR (1+tech_gain*tech): cultural depth
    # changed a number, not what an agent DID. R153 makes culture change a physical action: food spawns in
    # TIERS, and a tier-t mote (t>=1) is edible ONLY by an agent whose repertoire contains that tier's RECIPE
    # technique (a deep tech-tree node, see combinatorial.recipe_techniques). So a deeper culture physically
    # UNLOCKS richer food the world otherwise denies you — the realized diet widens with cultural depth, and
    # only transmission (not one asocial lifetime) reaches the deep recipes. tech_actions=False is byte-
    # identical to R150/R151 (food_tier is all-zero, no extra RNG, the eat path is unchanged).
    tech_actions: bool = False
    n_food_tiers: int = 4              # tier 0 (free) + (n_food_tiers-1) recipe-locked tiers
    recipe_level_step: int = 3        # tier t's recipe sits at tree-level >= recipe_level_step*t (deeper = harder)
    tier_value_bonus: float = 1.0     # a tier-t mote is worth food_value*(1+tier_value_bonus*t) (locked food is richer)
    tier0_frac: float = 0.4           # fraction of spawned food that is the free tier 0; the rest is locked tiers

    # --- R157: SPATIAL niches -> ECOLOGICALLY-SELECTED divergent traditions ---
    # R156's traditions are NEUTRAL DRIFT in a spatially-homogeneous world, so they stay MODEST (F_ST ~0.03)
    # and (verified R157) naive forgetting cannot sharpen them — with no force maintaining divergence, decay
    # only erodes the deep techniques that define a tradition. The missing ingredient is SELECTION. When
    # spatial_tiers=True a recipe-locked mote's TIER is set by its SPATIAL REGION (x-axis slab) instead of
    # uniformly at random: region r yields only tier-(r+1) locked food, edible (via tech_actions) ONLY by
    # holders of that tier's recipe branch. So each region ECONOMICALLY REWARDS one branch — recipe-r holders
    # accumulate energy and reproduce in region r while a wrong-branch wanderer starves on its locked food, so
    # selection LOCKS each region to its own tradition: discrete, spatially-structured, economically-distinct
    # cultures MAINTAINED by local adaptation (gene-culture coevolution), not drift. The causal NULL is
    # spatial_tiers=False (the R153 random-tier world, same tech_actions gate) — same learners + same recipes,
    # only the region<->branch correlation is cut. Requires tech_actions=True; off is byte-identical to R153.
    spatial_tiers: bool = False
    # Knowledge has UPKEEP: each step an agent pays recipe_upkeep per LOCKED-tier recipe it carries (the
    # cognitive/maintenance cost of a technique). With cheap, freely-transmitted branches every agent learns
    # EVERY branch (R154's convergence trap) and no region differentiates. A real upkeep makes carrying a branch
    # you don't use a net LOSS, so in region r holding recipe r pays (you eat tier r+1) but holding the others is
    # pure cost -> selection purifies each region to its OWN branch. This is what turns spatial_tiers from "no
    # effect" into genuine ecological selection of discrete traditions. recipe_upkeep=0.0 = byte-identical (no cost).
    recipe_upkeep: float = 0.0
    # The keystone: a newborn can carry at most recipe_budget LOCKED-tier recipe branches (the R155 capability-
    # budget mechanism applied to recipes). With cheap transmission every agent otherwise learns EVERY branch (a
    # generalist) and no region differentiates. A hard budget FORCES each agent to be a branch SPECIALIST, so in
    # region r only recipe-r specialists can eat -> selection sorts each branch into its own region: SHARP,
    # spatially-locked, economically-distinct traditions. Kept branches PREFER the parent's (heritable cultural
    # lineage). recipe_budget=0 = unlimited (no-op, byte-identical to R153/R156). Requires tech_actions.
    recipe_budget: int = 0

    # --- R158: TRADE between region-specialists -> an inter-group ECONOMY (the civilization leap) ---
    # R157 locked each region to its own branch by SELECTION but the traditions stayed MODEST, and the SHARP
    # regime (recipe_budget=1) CRASHED: a pure specialist that holds only branch q starves wherever its OWN
    # tier is absent (the wrong region, or before its branch has sorted in) — a bootstrap chicken-and-egg.
    # The missing mechanism is EXCHANGE. When trade=True, the SURPLUS of a locked-tier (t>=1) harvest flows to
    # the nearest HUNGRY agent within trade_radius that LACKS this tier's recipe (a COMPLEMENTARY specialist
    # who physically could not have eaten this food). Because every region's specialists do the same, two
    # complementary specialists meeting at a region BORDER feed each other -> reciprocal exchange of surplus
    # = an inter-group economy that rescues pure specialists and lets the SHARP recipe_budget=1 regime live.
    # The surplus is modeled as otherwise-spoiled (the giver keeps its full harvest), so trade is positive-sum
    # and unconditionally beneficial — like food ripening (R148) it is a WORLD MECHANIC, not faked behaviour;
    # what is EMERGENT is the spatially-structured economy it produces over the evolved specialists.
    trade: bool = False               # requires tech_actions. off = byte-identical (no extra RNG, no transfer).
    trade_radius: float = 12.0        # a surplus share reaches a partner within this distance (a local market)
    trade_share: float = 0.5          # fraction of a locked-tier harvest offered to a complementary partner
    trade_gain: float = 1.0           # gains-from-trade multiplier on the delivered share (>=1 = positive-sum)
    trade_need_frac: float = 1.0      # a partner is HUNGRY (eligible to receive) if energy < e_repro*this
    # The causal NULL: deliver each share to a UNIFORMLY-RANDOM hungry agent (any branch, any location) instead
    # of the nearest complementary neighbour. Same energy injected; only WHO receives changes (locality +
    # complementarity destroyed). If trade's benefit were mere energy, the scramble would match real trade.
    trade_scramble: bool = False      # requires trade=True.

    # R159: PRODUCTIVE goods trade — the answer to R158's honest negative (redistributing energy is INERT because
    # it doesn't relax the binding constraint). The binding constraint here is the FOOD-SLOT ceiling (food_cap):
    # ripe locked food that NO living agent in reach can eat (wrong-branch wanderers physically can't; the local
    # specialist eats only one mote/step) CLOGS food slots -> starves regrowth -> low realized carrying capacity.
    # trade_goods relaxes exactly that: a tier-t>=1 specialist, after eating its own mote, HARVESTS up to
    # goods_max ADDITIONAL ripe tier-t motes within trade_radius and ships each as an edible GOOD to a nearby
    # HUNGRY COMPLEMENTARY partner (lacks tier t's recipe). The mote is CONSUMED (removed -> frees a food slot for
    # regrowth) and its value (energy-conserving, no free injection) feeds the partner -> otherwise-wasted locked
    # food becomes population. This is positive-sum via DIVISION OF LABOUR (the specialist's comparative advantage
    # is harvesting a tier others can't), and unlike R158 it changes the OUTCOME: pop rises, locked_food_frac falls.
    trade_goods: bool = False         # requires tech_actions; mutually exclusive with trade. off = byte-identical.
    goods_max: int = 2                # extra wasted tier-t motes a specialist harvests-for-trade per step (bounded labour)
    seed_specialists: bool = False    # R159: a minority of founders born holding ONE random recipe (an already-
                                      # specialized population per R157), isolating the economy from the emergence bootstrap.
    seed_specialist_frac: float = 0.25  # fraction of founders seeded as producers; the rest are naive (free-tier only).

    # --- R154: MULTI-AXIS culture-gated PHYSICAL capabilities (techniques reshape MOVEMENT + harvest REACH) ---
    # R153 made culture gate ONE physical action (what an agent can EAT). R154 generalises that to a
    # multi-dimensional capability VECTOR: deep tech-tree nodes also unlock LOCOMOTION (a higher max speed)
    # and HARVEST REACH (a larger eat radius), so cultural depth reshapes the agent's whole physical
    # phenotype — a tech-driven capability economy, not a single switch. Each axis is gated on its own deep
    # node (combinatorial.capability_techniques, levels cap_level_step*1, *2, ...) and is categorically
    # physical (you hold the node or you don't). Requires combinatorial=True. tech_capabilities=False is
    # byte-identical (no nodes designated, speed cap = cfg.speed, reach = cfg.eat_radius, no extra RNG).
    tech_capabilities: bool = False
    n_capabilities: int = 2           # axis 0 = locomotion (max speed), axis 1 = harvest reach (eat radius)
    cap_level_step: int = 4           # axis i's node sits at tree-level >= cap_level_step*(i+1) (deeper = harder)
    cap_speed_mult: float = 1.0       # locomotion node -> max speed cfg.speed*(1+cap_speed_mult)
    cap_reach_mult: float = 1.0       # reach node -> eat radius cfg.eat_radius*(1+cap_reach_mult)

    # --- R155: COSTLY/BOUNDED capabilities -> emergent SPECIALIZATION (a division of labour through the tech tree) ---
    # R154's capabilities are FREE, so social transmission converges the WHOLE population to the full vector
    # (everyone learns every axis -> no specialization). R155 makes each capability EXCLUDABLE and BOUNDED so
    # distinct lineages specialize, attacking the R152 public-good negative from the EXCLUDABLE door:
    #   - each of the n_capabilities deep nodes is the EXCLUSIVE harvesting KEY to one PARALLEL food NICHE
    #     (a ripe mote in niche i is edible ONLY by an agent holding capability node i). A fraction
    #     niche_free_frac of food stays FREE (niche -1, edible by anyone) so culturally-naive founders survive
    #     while the keys bootstrap; keyed motes are richer (niche_value_bonus) so holding a key PAYS.
    #   - a finite somatic BUDGET cap_budget bounds how many capability keys an agent may carry, so it CANNOT
    #     hold every key -> it must specialize. On acquisition a newborn keeps its PARENT's keys first (the
    #     capability profile is heritable = a cultural lineage), then fills the remaining budget.
    #   - resource depletion makes a crowded niche pay less -> negative frequency dependence -> a STABLE
    #     polymorphism of capability profiles (a division of labour), where R154 gave convergence; and a
    #     freely-specializing MIXED population out-survives a forced MONOCULTURE (cap_force_mono) that wastes
    #     the other niches' food.
    # Requires tech_capabilities=True. cap_niches=False is byte-identical to R154 (all motes free, no niche RNG
    # draw, no budget enforced). cap_skew_key0 (>=0) seeds founders' keys skewed for the frequency-dependence
    # probe; -1 (default) keeps founders culturally naive (the standard invariant).
    cap_niches: bool = False
    cap_budget: int = 1               # max capability keys an agent may hold (somatic budget) -> forces a choice
    niche_free_frac: float = 0.5      # fraction of food that is FREE (edible by anyone); rest split among keyed niches
    niche_value_bonus: float = 1.0    # a keyed mote is worth food_value*(1+niche_value_bonus) (specializing pays)
    cap_force_mono: bool = False      # CONTROL: force every agent to key 0 only (a monoculture) -> wastes niche>0 food
    cap_skew_key0: float = -1.0       # PROBE: seed founders key0 w.p. this, else key1 (>=0 grants founder keys); -1 off
    # R161 GROUND-TRUTH cladistics: log the BIRTH genealogy (a parent-pointer forest) so the reconstructed
    # cultural cladogram can be tested for whether it RECOVERS the true line of descent (genealogy_phylogeny_test).
    # track_genealogy=True is a passive observer: it consumes NO RNG and changes NO sim state, so the trajectory
    # is byte-identical to off (the log just grows append-only). Analysis-only instrumentation — for bounded
    # verification runs, not multi-day persistent worlds (the log is unbounded by design, like a tracer).
    track_genealogy: bool = False
    # R161 causal contrast for the ground-truth test: vertical_only=True disables OBLIQUE (nearest-hearth)
    # transmission so a newborn inherits ONLY its parent's repertoire (+ innovation) — pure VERTICAL descent.
    # The default (horizontal/oblique copying ON) decouples culture from ancestry; vertical-only should let
    # the reconstructed cladogram recover the true birth genealogy. No RNG in the skipped oblique block, so
    # vertical_only=False is byte-identical to R150..R160.
    vertical_only: bool = False
    # R163 TEMPORAL phylogeny / open-endedness: log the world step at which each technique FIRST appears in the
    # living population — the time-ladder of cumulative descent. track_tech_history=True is a passive observer
    # (reads self.rep, consumes NO RNG, mutates NO sim state -> byte-identical to off). temporal_phylogeny_test
    # then asks whether that first-appearance order RECOVERS the generative tech tree (precedence: a technique
    # appears after its prereqs; level<->time Spearman) vs a label-permutation null. Requires combinatorial=True.
    track_tech_history: bool = False
    # metric
    persist_steps: int = 200


class GenesisWorld:
    def __init__(self, cfg: GenesisConfig | None = None, seed: int = 0, evolve: bool = True):
        self.cfg = cfg or GenesisConfig()
        self.rng = np.random.default_rng(seed)
        self.evolve = evolve
        self.has_predators = self.cfg.n_predators0 > 0
        self.signalling = self.cfg.signalling
        self.processing = self.cfg.processing
        self.specialize = self.cfg.specialize
        self.building = self.cfg.building
        self.build_specialized = self.cfg.build_specialized
        self.culture = self.cfg.culture
        self.combinatorial = self.cfg.combinatorial
        self.generative_tree = self.cfg.generative_tree
        self.tech_actions = self.cfg.tech_actions
        self.tech_capabilities = self.cfg.tech_capabilities
        self.depth_gates = self.cfg.depth_gates
        self.cap_niches = self.cfg.cap_niches
        self.culture_decay = self.cfg.culture_decay
        if self.combinatorial and not self.culture:
            raise ValueError("combinatorial (R150 open-ended culture) requires culture=True")
        if self.generative_tree and not self.combinatorial:
            raise ValueError("generative_tree (R170 open-ended-by-construction tree) requires combinatorial=True")
        if self.generative_tree and (self.tech_actions or self.tech_capabilities):
            raise ValueError("generative_tree (R170) has no pre-built deep nodes, so tech_actions/"
                             "tech_capabilities (fixed-deep-node recipe gates) are not yet wired onto it")
        if self.depth_gates and not self.generative_tree:
            raise ValueError("depth_gates (R171 embodied capability gated on realized cultural DEPTH) requires "
                             "generative_tree=True (it gates on the open-ended grown tree's depth)")
        if self.tech_actions and not self.combinatorial:
            raise ValueError("tech_actions (R153 culture unlocks world-actions) requires combinatorial=True")
        if self.tech_capabilities and not self.combinatorial:
            raise ValueError("tech_capabilities (R154 culture-gated physical capabilities) requires combinatorial=True")
        if self.cap_niches and not self.tech_capabilities:
            raise ValueError("cap_niches (R155 capability specialization) requires tech_capabilities=True")
        if self.cfg.panmictic_culture and not self.combinatorial:
            raise ValueError("panmictic_culture (R156 traditions null) requires combinatorial=True")
        if self.culture_decay and not self.combinatorial:
            raise ValueError("culture_decay (R157 lossy cultural memory) requires combinatorial=True")
        if self.cfg.track_tech_history and not self.combinatorial:
            raise ValueError("track_tech_history (R163 temporal phylogeny) requires combinatorial=True")
        if self.cfg.spatial_tiers and not self.tech_actions:
            raise ValueError("spatial_tiers (R157 ecologically-selected traditions) requires tech_actions=True")
        if (self.cfg.recipe_budget > 0 or self.cfg.recipe_upkeep > 0.0) and not self.tech_actions:
            raise ValueError("recipe_budget/recipe_upkeep (R157) require tech_actions=True")
        self.trade = self.cfg.trade
        if self.trade and not self.tech_actions:
            raise ValueError("trade (R158 inter-group economy) requires tech_actions=True")
        self.trade_goods = self.cfg.trade_goods
        if self.trade_goods and not self.tech_actions:
            raise ValueError("trade_goods (R159 productive economy) requires tech_actions=True")
        if self.trade_goods and self.trade:
            raise ValueError("trade_goods and trade are alternative economy modes; enable at most one")
        if self.cfg.trade_scramble and not (self.trade or self.trade_goods):
            raise ValueError("trade_scramble is the trade/goods null; requires trade=True or trade_goods=True")
        if self.processing and self.cfg.n_food_types > 1:
            raise ValueError("processing (R146 division of labour) assumes a single food type")
        if self.specialize and not self.processing:
            raise ValueError("specialize (R147 caste trade-off) requires processing=True")
        if self.building and not self.processing:
            raise ValueError("building (R148 niche construction) requires processing=True")
        if self.culture and not self.building:
            raise ValueError("culture (R149 cumulative culture) requires building=True (hearths = the repository)")
        if self.build_specialized and not (self.building and self.specialize):
            raise ValueError("build_specialized (R152 builder caste) requires building=True AND specialize=True")
        prey_in = (N_IN + (4 if self.has_predators else 0)   # +nearest-predator sense channel (R143)
                   + (1 if self.signalling else 0)           # +heard-neighbour-utterance channel (R144)
                   + (4 if self.processing else 0)           # +nearest-RAW-food sense channel (R146)
                   + (4 if self.building else 0))            # +nearest-HEARTH sense channel (R148)
        prey_out = (N_OUT + (1 if self.signalling else 0)    # +utterance output (R144); _act ignores it
                    + (1 if self.processing else 0))         # +process gate output (R146); _act ignores it
        # index of the process-gate output (after movement and the optional utterance output)
        self._proc_out = N_OUT + (1 if self.signalling else 0)
        self.spec = BrainSpec(n_in=prey_in, n_hidden=self.cfg.n_hidden, n_out=prey_out)
        self.pop = Population(PopConfig(self.cfg.capacity, self.spec.n_weights))
        self.step_count = 0
        self.lineage_first_step: dict[int, int] = {}
        self._seed_population()
        if self.cfg.track_genealogy:                         # R161: passive birth-genealogy log (no RNG, no state)
            self._gen_parent: list[int] = []                 # node -> parent node id (-1 for a founder/root)
            self._gen_node = np.full(self.cfg.capacity, -1, dtype=np.int64)  # live slot -> its genealogy node id
            for slot in self.pop.active():                   # each founder is a distinct root lineage
                self._gen_node[slot] = len(self._gen_parent)
                self._gen_parent.append(-1)
        if self.combinatorial:                               # R150: build the tech tree + repertoire pools
            from . import combinatorial as cb
            K, ns = self.cfg.max_techniques, self.cfg.n_seed_tech
            if self.generative_tree:                          # R170: GENERATIVE open-ended tree, grown on demand
                self._tree = cb.GrowingTree(K, ns)            # from the population's real compositions (no pre-build)
                self._tree_pa, self._tree_pb, self._tree_level = self._tree.pa, self._tree.pb, self._tree.level
            else:
                self._tree = None
                self._tree_pa, self._tree_pb, self._tree_level = cb.build_tech_tree(K, ns)
            self.rep = np.zeros((self.cfg.capacity, K), dtype=bool)       # per-agent repertoire (World-owned)
            act = self.pop.active()                                       # founders are culturally NAIVE: empty
            seed_rep = np.zeros((act.size, K), dtype=bool)                # repertoire, a few discoveries each
            if self.generative_tree:
                seed_rep[:, :ns] = True                       # everyone knows the level-0 primitives -> can compose
                self._tree.discover_inplace(seed_rep, self.rng, self.cfg.innov_steps)
            else:
                cb.discover_inplace(seed_rep, self._tree_pa, self._tree_pb, ns,
                                    self.cfg.combo_prereqs, self.rng, self.cfg.innov_steps)
            self.rep[act] = seed_rep
            self.pop.tech[act] = cb.max_level_known(seed_rep, self._tree_level)
            if self.cfg.track_tech_history:                  # R163: passive first-appearance log (no RNG, no state)
                self._tech_first_step = np.full(K, -1, dtype=np.int64)
                self._update_tech_history()                  # stamp the founders' seed repertoire at step 0
            if self.depth_gates:                             # R171: gates on realized cultural DEPTH (pop.tech),
                self._tier_eat_count = np.zeros(self.cfg.n_food_tiers, dtype=np.int64)  # no pre-designated nodes
            if self.tech_actions:                            # R153: which deep node unlocks each locked food tier
                self._recipe_tech = cb.recipe_techniques(
                    self._tree_level, ns, self.cfg.n_food_tiers, self.cfg.recipe_level_step)
                self._tier_eat_count = np.zeros(self.cfg.n_food_tiers, dtype=np.int64)
                self._trade_count = 0          # R158 diagnostics (lifetime; never feeds selection)
                self._trade_volume = 0.0
                self._trade_dist_sum = 0.0
                self._trade_compl = 0
                self._trade_cross = 0
                self._goods_count = 0          # R159 productive-goods diagnostics (lifetime; never feeds selection)
                self._goods_volume = 0.0
                self._goods_dist_sum = 0.0
                self._goods_motes = 0          # wasted tier-t motes consumed-for-trade (= slots freed)
                if self.cfg.seed_specialists:  # R159: start from an ALREADY-SPECIALIZED population (R157 result),
                    # isolating the economic question from the cultural-emergence bootstrap. A seed_specialist_frac
                    # MINORITY is born each holding ONE uniformly-random recipe tier (a producer who can harvest a
                    # locked tier); the rest stay culturally NAIVE (eat only the free tier 0). So most locked food
                    # has no nearby mouth -> it clogs food slots uneaten (the binding constraint), and the naive
                    # majority starves -> exactly the hungry complementary partners productive goods trade feeds.
                    is_spec = self.rng.random(act.size) < self.cfg.seed_specialist_frac
                    one = self.rng.integers(1, self.cfg.n_food_tiers, size=act.size)
                    self.rep[act[is_spec], self._recipe_tech[one[is_spec]]] = True
            if self.tech_capabilities:                       # R154: which deep node unlocks each PHYSICAL axis
                self._cap_tech = cb.capability_techniques(
                    self._tree_level, ns, self.cfg.n_capabilities, self.cfg.cap_level_step)
                if self.cap_niches and self.cfg.cap_skew_key0 >= 0.0:  # R155 probe: seed founder keys skewed
                    key0 = self.rng.random(act.size) < self.cfg.cap_skew_key0    # else key1 (only for C>=2)
                    self.rep[act[key0], self._cap_tech[0]] = True
                    if self.cfg.n_capabilities >= 2:
                        self.rep[act[~key0], self._cap_tech[1]] = True
                    self.pop.tech[act] = cb.max_level_known(self.rep[act], self._tree_level)
        elif self.culture:                                   # R149 scalar: founders are culturally NAIVE: one
            act = self.pop.active()                           # innovation each, no ancestors to copy -> start ~0
            self.pop.tech[act] = np.maximum(0.0, self.rng.normal(self.cfg.innov_mean, self.cfg.innov_sigma,
                                                                 size=act.size))
        w = self.cfg.world
        self.patch_centers = None
        if self.cfg.food_mode == "patches":            # fixed clumps; drawn only in patch mode
            self.patch_centers = self.rng.uniform(w.size * 0.12, w.size * 0.88,
                                                  size=(self.cfg.n_patches, 3))
        self.food = self._spawn_food(self.cfg.food_cap)
        self.food_type = self._food_types(self.cfg.food_cap)
        self.food_tier = self._food_tiers(self.food)             # R153 recipe-locked tiers (all-zero when off)
        self.food_niche = self._food_niches(self.food.shape[0])  # R155 capability-keyed niches (all -1 when off)
        # ripeness state (R146): food is edible only when ripe. processing OFF -> all ripe always (the
        # R141..R145 world, byte-identical); processing ON -> food spawns RAW and is ripened by processors.
        self.food_ripe = np.zeros(self.food.shape[0], dtype=bool) if self.processing \
            else np.ones(self.food.shape[0], dtype=bool)
        self.ripe_age = np.zeros(self.food.shape[0], dtype=np.int32)
        # which agent slot last ripened each mote (R147 caste wage attribution); -1 = none/raw
        self.food_proc = np.full(self.food.shape[0], -1, dtype=np.int64)
        # predators (R143) — a second evolved-neural species; absent unless n_predators0>0
        self.pred_spec = BrainSpec(n_in=5, n_hidden=self.cfg.n_hidden, n_out=N_OUT)  # nearest prey(4)+energy(1)
        self.pred = None
        if self.has_predators:
            self.pred = Population(PopConfig(self.cfg.pred_capacity, self.pred_spec.n_weights))
            self._seed_predators()
        # persistent hearth structures (R148 niche construction) — a fixed-capacity SoA, free-slot reuse
        # so a multi-day run can't grow memory. Empty until agents build. strength<=0 frees the slot.
        m = self.cfg.struct_capacity
        self.struct_pos = np.zeros((m, 3))
        self.struct_strength = np.zeros(m)
        self.struct_birth = np.zeros(m, dtype=np.int64)     # step the hearth was founded (-> its age)
        self.struct_founder_gen = np.zeros(m, dtype=np.int32)
        self.struct_max_gen = np.zeros(m, dtype=np.int32)   # latest builder generation that maintained it
        self.struct_last_builder = np.full(m, -1, dtype=np.int64)  # R152: agent slot that last built/maintained
                                                             # the hearth (-> paid the maintenance wage); -1 = none
        self.struct_tech = np.zeros(m)                       # best technique recorded at the hearth (R149 culture
                                                             # repository): the growing cultural record
        if self.combinatorial:                               # R150: each hearth stores an accumulating REPERTOIRE
            self.struct_rep = np.zeros((m, self.cfg.max_techniques), dtype=bool)  # (union of builders' techniques)
            if self.culture_decay:                           # R157: a decaying per-technique cultural MEMORY backs
                self.struct_memory = np.zeros((m, self.cfg.max_techniques), dtype=np.float32)  # the record (lossy)
        self.struct_alive = np.zeros(m, dtype=bool)
        self._death_age_sum = 0.0                            # realized-lifespan accumulator (R148 inheritance)
        self._death_count = 0

    # --- setup ---
    def _seed_population(self) -> None:
        cfg, w, p = self.cfg, self.cfg.world, self.pop
        n0 = cfg.n0
        slots = p.alloc(n0)
        if cfg.n_founder_genomes > 0:
            # clonal demes (R145): G genomes, each cloned into a tight spatial cluster sharing a lineage id
            # -> high spatial relatedness (a prey's nearest neighbour is its clone) for kin selection. This
            # path is reached only when explicitly enabled, so it does not perturb R141..R144 RNG order.
            G = min(cfg.n_founder_genomes, n0)
            deme = self.rng.integers(0, G, size=n0)                 # which deme each founder belongs to
            genomes = brain.random_brains(G, self.spec, self.rng)
            centers = self.rng.uniform(0, w.size, size=(G, 3))
            colors = self.rng.uniform(0.25, 1.0, size=(G, 3))
            p.pos[slots] = w.clamp(centers[deme]
                                   + self.rng.normal(0, cfg.founder_cluster_radius, size=(n0, 3)))
            d = self.rng.normal(size=(n0, 3))
            p.vel[slots] = d / np.linalg.norm(d, axis=1, keepdims=True) * cfg.speed
            p.energy[slots] = cfg.e_start
            p.brains[slots] = genomes[deme]
            p.lineage[slots] = deme.astype(np.int32)
            p.generation[slots] = 0
            p.color[slots] = colors[deme]
            if cfg.n_food_types > 1:                                 # one diet per deme (specialist clones)
                diets = self.rng.uniform(0, cfg.n_food_types, size=G)
                p.diet[slots] = diets[deme]
            if cfg.specialize:                                       # standing caste variation (R147)
                p.spec[slots] = 0.5 if cfg.force_generalist else self.rng.uniform(0, 1, size=n0)
            self.lineage_first_step = {int(g): 0 for g in range(G)}
            return
        p.pos[slots] = self.rng.uniform(0, w.size, size=(n0, 3))
        d = self.rng.normal(size=(n0, 3))
        p.vel[slots] = d / np.linalg.norm(d, axis=1, keepdims=True) * cfg.speed
        p.energy[slots] = cfg.e_start
        p.brains[slots] = brain.random_brains(n0, self.spec, self.rng)
        p.lineage[slots] = np.arange(n0, dtype=np.int32)        # each founder a distinct bloodline
        p.generation[slots] = 0
        p.color[slots] = self.rng.uniform(0.25, 1.0, size=(n0, 3))
        if cfg.n_food_types > 1:                          # founders spread across diet niches
            p.diet[slots] = self.rng.uniform(0, cfg.n_food_types, size=n0)
        if cfg.specialize:                                # standing caste variation -> selection can split it
            p.spec[slots] = 0.5 if cfg.force_generalist else self.rng.uniform(0, 1, size=n0)
        self.lineage_first_step = {int(i): 0 for i in range(n0)}

    def _seed_predators(self) -> None:
        cfg, w, pr = self.cfg, self.cfg.world, self.pred
        n = cfg.n_predators0
        slots = pr.alloc(n)
        pr.pos[slots] = self.rng.uniform(0, w.size, size=(n, 3))
        d = self.rng.normal(size=(n, 3))
        pr.vel[slots] = d / np.linalg.norm(d, axis=1, keepdims=True) * cfg.pred_speed
        pr.energy[slots] = cfg.pred_e_start
        pr.brains[slots] = brain.random_brains(n, self.pred_spec, self.rng)
        pr.lineage[slots] = np.arange(n, dtype=np.int32)
        pr.color[slots] = np.array([0.95, 0.15, 0.15])     # red hunters (render)

    def _food_types(self, n: int) -> np.ndarray:
        """Type label per food mote. Single type (R142 off, no RNG draw) keeps R141 determinism."""
        if self.cfg.n_food_types <= 1:
            return np.zeros(n, dtype=np.int64)
        return self.rng.integers(0, self.cfg.n_food_types, size=n)

    def _food_tiers(self, pos: np.ndarray) -> np.ndarray:
        """Recipe-tier label per food mote (R153). Off (or single tier) -> all tier 0, NO RNG draw (so
        tech_actions=False is byte-identical to R150/R151). On -> tier 0 with prob tier0_frac (the free,
        always-edible resource), else a LOCKED tier in 1..n_food_tiers-1. R157 spatial_tiers: a locked mote's
        tier is its SPATIAL-REGION index (x-axis slab) so each region yields ONE branch (ecological selection);
        off (R153) it is uniformly random. The tier0_frac RNG draw is identical in both, so spatial_tiers=False
        is byte-identical to R153 (the spatial branch consumes no RNG)."""
        cfg = self.cfg
        n = pos.shape[0]
        if not (self.tech_actions or self.depth_gates) or cfg.n_food_tiers <= 1:
            return np.zeros(n, dtype=np.int64)
        tiers = np.zeros(n, dtype=np.int64)
        locked = self.rng.random(n) >= cfg.tier0_frac
        n_locked = int(locked.sum())
        if n_locked:
            if cfg.spatial_tiers:                                 # R157: tier = spatial region -> region<->branch map
                ntiers = cfg.n_food_tiers - 1
                slab = np.clip((pos[locked, 0] / cfg.world.size * ntiers).astype(int), 0, ntiers - 1)
                tiers[locked] = 1 + slab                          # region r yields only tier r+1 (no RNG)
            else:                                                 # R153: uniformly random locked tier
                tiers[locked] = self.rng.integers(1, cfg.n_food_tiers, size=n_locked)
        return tiers

    def _food_niches(self, n: int) -> np.ndarray:
        """Capability-niche label per food mote (R155). -1 = FREE (edible by anyone). cap_niches OFF (or no
        capability axes) -> all -1, NO RNG draw (so cap_niches=False is byte-identical to R154). ON -> FREE with
        prob niche_free_frac, else a uniformly random KEYED niche in 0..n_capabilities-1 (edible only by a holder
        of that niche's capability node). The free niche lets culturally-naive founders survive while the deep
        capability keys bootstrap via transmission; the keyed niches are the excludable specialist resources."""
        cfg = self.cfg
        if not self.cap_niches or cfg.n_capabilities < 1:
            return np.full(n, -1, dtype=np.int64)
        niche = np.full(n, -1, dtype=np.int64)
        keyed = self.rng.random(n) >= cfg.niche_free_frac
        nk = int(keyed.sum())
        if nk:
            niche[keyed] = self.rng.integers(0, cfg.n_capabilities, size=nk)
        return niche

    # --- sensing ---
    def _sense_neighbours(self, pos, right, up, fwd, sense_range):
        """Body-frame sense of the nearest neighbour -> (sense(P,4), neighbour-idx, proximity).

        The neighbour index + proximity are returned so the signalling channel (R144) can read that
        same nearest neighbour's utterance for free (no second KD-tree). idx indexes the active subset."""
        n = pos.shape[0]
        if n < 2:
            return np.zeros((n, 4)), None, np.zeros(n)
        dist, idx = cKDTree(pos).query(pos, k=2)        # k=2: self (col 0) + nearest other (col 1)
        nd, ni = dist[:, 1], idx[:, 1]
        nearest = pos[ni] - pos
        unit = nearest / np.maximum(np.linalg.norm(nearest, axis=1, keepdims=True), 1e-9)
        prox = np.where(nd < sense_range, 1.0 - nd / sense_range, 0.0)
        sense = np.stack([(unit * right).sum(1) * prox, (unit * up).sum(1) * prox,
                          (unit * fwd).sum(1) * prox, prox], axis=1)
        return sense, ni, prox

    def _agent_types(self, act):
        return np.clip(np.round(self.pop.diet[act]).astype(int), 0, self.cfg.n_food_types - 1)

    def _heard(self, act, ni, nprox):
        """The signal each prey hears: its nearest neighbour's previous-step utterance, gated to 0 when
        no neighbour is in range (R144). Returns (P,1). ni indexes the active subset (from _sense_neighbours)."""
        if ni is None or self.cfg.deaf:               # deaf control: brain has the input, hears only silence
            return np.zeros((act.size, 1))
        return (self.pop.utterance[act][ni] * (nprox > 0)).reshape(-1, 1)

    def _sense_food(self, pos, r, u, f, act):
        """Nearest food in the body frame. With resource types each agent senses only its own type."""
        cfg = self.cfg
        if cfg.n_food_types <= 1:
            return _sense_kd(pos, r, u, f, self.food, cfg.sense_range)
        out = np.zeros((pos.shape[0], 4))
        types = self._agent_types(act)
        for t in range(cfg.n_food_types):
            am = types == t
            food_t = self.food[self.food_type == t]
            if am.any() and food_t.shape[0]:
                out[am] = _sense_kd(pos[am], r[am], u[am], f[am], food_t, cfg.sense_range)
        return out

    def _pred_detect_range(self) -> float:
        """Prey direct predator-sense range. Shortened (prey_pred_range>0) in the signalling scenario so
        a neighbour closer to the predator can warn earlier; 0 -> full sense_range (R143 byte-identical)."""
        return self.cfg.prey_pred_range if self.cfg.prey_pred_range > 0 else self.cfg.sense_range

    def _sense_predators(self, pos, r, u, f):
        """Prey body-frame sense of the nearest predator (R143) -> (P,4). Drives evolved evasion."""
        if self.pred is None:
            return np.zeros((pos.shape[0], 4))
        pred_pos = self.pred.pos[self.pred.active()]
        return _sense_kd(pos, r, u, f, pred_pos, self._pred_detect_range())

    # --- the step ---
    def step(self) -> None:
        cfg, w, p = self.cfg, self.cfg.world, self.pop
        act = p.active()
        if act.size:
            pos, vel = p.pos[act], p.vel[act]
            r, u, f = _body_frame(vel)
            if self.processing:                             # harvest target = ripe (edible) food only
                fs = _sense_kd(pos, r, u, f, self.food[self.food_ripe], cfg.sense_range)
            else:
                fs = self._sense_food(pos, r, u, f, act)
            ns, ni, nprox = self._sense_neighbours(pos, r, u, f, cfg.sense_range)
            e = (p.energy[act] / cfg.e_repro).reshape(-1, 1)
            parts = [fs, ns]
            if self.has_predators:                          # +predator-sense channel (R143)
                parts.append(self._sense_predators(pos, r, u, f))
            if self.signalling:                             # +heard-neighbour-utterance channel (R144)
                parts.append(self._heard(act, ni, nprox))
            if self.processing:                             # +nearest-RAW-food sense channel (R146)
                parts.append(_sense_kd(pos, r, u, f, self.food[~self.food_ripe], cfg.sense_range))
            if self.building:                               # +nearest-HEARTH sense channel (R148)
                parts.append(self._sense_hearths(pos, r, u, f))
            parts.append(e)
            out = brain.forward(p.brains[act], self.spec, np.concatenate(parts, axis=1))
            hi = self._cap_speed(act)                        # R154: per-agent max speed (culture-gated locomotion)
            newvel = _act(out, r, u, f, vel, cfg.force, cfg.min_speed, hi)  # _act reads out[:,:3]
            p.vel[act] = newvel
            p.pos[act] = w.clamp(pos + newvel)
            emit = np.zeros(act.size)
            if self.signalling:                             # the evolved extra output IS the utterance
                p.utterance[act] = np.tanh(out[:, N_OUT])   # bounded [-1,1]; heard by neighbours next step
                emit = cfg.emit_cost * np.abs(p.utterance[act])  # honest-signalling cost -> silence default
            speed = np.linalg.norm(newvel, axis=1)
            upkeep = 0.0
            if self.tech_actions and cfg.recipe_upkeep > 0.0:    # R157: metabolic cost of carried recipe knowledge
                upkeep = cfg.recipe_upkeep * self.rep[act][:, self._recipe_tech[1:]].sum(axis=1)
            p.energy[act] = np.minimum(p.energy[act] - (cfg.base_cost + cfg.move_cost * speed + emit + upkeep),
                                       cfg.e_max)
            if self.building:                               # deposit/reinforce a persistent hearth (R148)
                self._build(act, out)
            elif self.processing:                           # ripen nearby raw food (the costly labour)
                self._process(act, out)
            p.age[act] += 1
        if self.building:                                   # hearths ripen nearby raw food, then decay
            self._ripen_hearths()
            self._decay_structures()
            self._decay_memory()                            # R157: cultural loss (before reproduction learns)
        self._eat()
        if self.processing:
            self._decay_ripe()
        if self.has_predators:
            self._step_predators()
        self._die()
        self._reproduce()
        self._regrow()
        self.step_count += 1
        if self.cfg.track_tech_history:                      # R163: passive observer (after this step's births)
            self._update_tech_history()

    def _keep_food(self, keep: np.ndarray) -> None:
        """Filter all per-mote food arrays by the same boolean mask (keeps ripeness state in sync)."""
        self.food = self.food[keep]
        self.food_type = self.food_type[keep]
        self.food_tier = self.food_tier[keep]
        if self.cap_niches:                                 # R155 niche labels: only live (and kept in sync) when on
            self.food_niche = self.food_niche[keep]
        self.food_ripe = self.food_ripe[keep]
        self.ripe_age = self.ripe_age[keep]
        self.food_proc = self.food_proc[keep]

    def _harvest_gain(self, eaters: np.ndarray, base: np.ndarray | None = None) -> np.ndarray:
        """Per-eater energy gained from harvesting one mote (R151 — the COMPOSED harvest payoff).

        The two harvest modifiers MULTIPLY, so they coexist in the integrated capstone world:
          - caste convexity (R147): pure harvesters (spec=0) eat at full value, processors (spec=1) at ~0;
          - learned technique (R149/R150): a deeper repertoire multiplies the intake (mastery pays).
        Before R151 these were an if/elif, so with BOTH on the culture payoff was silently dropped and the
        cumulative-culture ratchet lost its selective gradient under caste. Each modifier is gated on its own
        flag, so a single-flag config is byte-identical to R147/R149/R150 (only the both-on case changes).
        `base` (R153) overrides the per-eater base value with the eaten mote's TIER value; None -> food_value."""
        cfg, p = self.cfg, self.pop
        gain = np.full(eaters.size, cfg.food_value) if base is None else np.asarray(base, dtype=float).copy()
        if self.specialize:                                 # convex harvest skill: pure harvesters eat full
            gain = gain * np.power(1.0 - p.spec[eaters], cfg.spec_gamma)
        if self.culture:                                    # learned technique multiplies the harvest
            gain = gain * (1.0 + cfg.tech_gain * p.tech[eaters])
        return gain

    def _cap_speed(self, act: np.ndarray):
        """R154 locomotion axis: per-active-agent max speed. An agent whose repertoire holds the locomotion
        node (self._cap_tech[0]) moves at cfg.speed*(1+cap_speed_mult); everyone else at cfg.speed. Returns a
        scalar when tech_capabilities is off (byte-identical) or as a column vector for _limit_speed."""
        cfg = self.cfg
        if self.depth_gates:                                 # R171: locomotion unlocks at cultural DEPTH >= step
            fast = self.pop.tech[act] >= cfg.cap_level_step  # axis 0 threshold (level units)
            return (cfg.speed * (1.0 + cfg.cap_speed_mult * fast)).reshape(-1, 1)
        if not self.tech_capabilities:
            return cfg.speed
        fast = self.rep[act, self._cap_tech[0]]              # bool per active agent (the locomotion node)
        return (cfg.speed * (1.0 + cfg.cap_speed_mult * fast)).reshape(-1, 1)

    def _cap_reach(self, eaters_act: np.ndarray):
        """R154 harvest-reach axis: per-eater eat radius. An agent whose repertoire holds the reach node
        (self._cap_tech[1]) harvests within cfg.eat_radius*(1+cap_reach_mult); others within cfg.eat_radius.
        Returns the scalar cfg.eat_radius when off (byte-identical)."""
        cfg = self.cfg
        if self.depth_gates:                                 # R171: reach (axis 1) unlocks at depth >= 2*step
            if cfg.n_capabilities < 2:
                return cfg.eat_radius
            far = self.pop.tech[eaters_act] >= cfg.cap_level_step * 2
            return cfg.eat_radius * (1.0 + cfg.cap_reach_mult * far)
        if not self.tech_capabilities or cfg.n_capabilities < 2:
            return cfg.eat_radius
        far = self.rep[eaters_act, self._cap_tech[1]]        # bool per candidate eater (the reach node)
        return cfg.eat_radius * (1.0 + cfg.cap_reach_mult * far)

    def _eat(self) -> None:
        cfg, p = self.cfg, self.pop
        act = p.active()
        if act.size == 0 or self.food.shape[0] == 0:
            return
        if self.depth_gates:                                # R171: ripe AND DEPTH-unlocked tier (generative tree)
            self._eat_depth_gates()
            return
        if self.cap_niches:                                 # R155: ripe AND capability-key-gated niche
            self._eat_cap_niches()
            return
        if self.tech_actions:                               # R153: ripe AND recipe-unlocked tier
            self._eat_tech_actions()
            return
        if self.processing:                                 # only RIPE food is edible (R146)
            edible = np.where(self.food_ripe)[0]
            if edible.size == 0:
                return
            dist, idx = cKDTree(self.food[edible]).query(p.pos[act], k=1)
            winners, eaten = _resolve(dist, idx, cfg.eat_radius)   # eaten indexes into `edible`
            if winners.size:
                eaters = act[winners]
                p.energy[eaters] += self._harvest_gain(eaters)
                if self.specialize:                         # wage to whoever ripened each eaten mote (trade)
                    self._pay_processors(edible[eaten])
                keep = np.ones(self.food.shape[0], dtype=bool)
                keep[edible[eaten]] = False
                self._keep_food(keep)
            return
        if cfg.n_food_types <= 1:
            dist, idx = cKDTree(self.food).query(p.pos[act], k=1)
            winners, eaten = _resolve(dist, idx, cfg.eat_radius)   # winners index into `act`
            if winners.size:
                p.energy[act[winners]] += cfg.food_value
                keep = np.ones(self.food.shape[0], dtype=bool)
                keep[eaten] = False
                self._keep_food(keep)
            return
        # typed: each agent eats only food of its own diet type (the resource-partitioning trade-off)
        types = self._agent_types(act)
        keep = np.ones(self.food.shape[0], dtype=bool)
        for t in range(cfg.n_food_types):
            am = np.where(types == t)[0]                # rows in act
            fm = np.where(self.food_type == t)[0]       # rows in food
            if am.size == 0 or fm.size == 0:
                continue
            dist, idx = cKDTree(self.food[fm]).query(p.pos[act[am]], k=1)
            winners, eaten = _resolve(dist, idx, cfg.eat_radius)
            if winners.size:
                p.energy[act[am[winners]]] += cfg.food_value
                keep[fm[eaten]] = False
        if not keep.all():
            self._keep_food(keep)

    def _eat_tech_actions(self) -> None:
        """R153 eat: ripe food is harvested only from a tier the eater's CULTURE has unlocked. Tier 0 is
        free; tier t>=1 requires the recipe technique self._recipe_tech[t] in the agent's repertoire. So a
        culturally deeper agent can physically convert food the world denies a naive one — culture changes
        what an agent DOES, not just a payoff scalar. Tiers are resolved high->low (richer first), each agent
        eats at most one mote/step, and the tier's value (food_value*(1+tier_value_bonus*t)) feeds the usual
        caste/technique multipliers via _harvest_gain. Locked motes simply persist (the visible signature)."""
        cfg, p = self.cfg, self.pop
        act = p.active()
        ripe = np.where(self.food_ripe)[0]
        if ripe.size == 0:
            return
        keep = np.ones(self.food.shape[0], dtype=bool)
        eaten_agent = np.zeros(act.size, dtype=bool)         # at most one harvest per agent per step
        ripe_tier = self.food_tier[ripe]
        for t in range(cfg.n_food_tiers - 1, -1, -1):
            fm = ripe[(ripe_tier == t) & keep[ripe]]         # ripe, this tier, not already eaten this step
            if fm.size == 0:
                continue
            if t == 0:
                elig = np.where(~eaten_agent)[0]             # tier 0 is the free resource
            else:
                elig = np.where(self.rep[act, self._recipe_tech[t]] & ~eaten_agent)[0]  # recipe-knowers only
            if elig.size == 0:
                continue
            dist, idx = cKDTree(self.food[fm]).query(p.pos[act[elig]], k=1)
            reach = self._cap_reach(act[elig])               # R154: per-eater harvest reach (culture-gated)
            winners, eaten = _resolve(dist, idx, reach)      # winners index into elig; eaten into fm
            if winners.size == 0:
                continue
            eaters = act[elig[winners]]
            base = np.full(eaters.size, cfg.food_value * (1.0 + cfg.tier_value_bonus * t))
            gain = self._harvest_gain(eaters, base=base)
            p.energy[eaters] += gain
            if self.trade and t >= 1:                        # R158: share locked-tier surplus to a complementary partner
                self._do_trade(eaters, gain, t)
            if self.specialize:                              # wage to whoever ripened each eaten mote (trade)
                self._pay_processors(fm[eaten])
            keep[fm[eaten]] = False
            eaten_agent[elig[winners]] = True
            if self.trade_goods and t >= 1:                  # R159: harvest WASTED tier-t motes -> goods to partners
                self._do_goods_trade(eaters, fm, keep, t)
            self._tier_eat_count[t] += int(eaten.size)
        if not keep.all():
            self._keep_food(keep)

    def _eat_depth_gates(self) -> None:
        """R171 eat: ripe food is harvested only from a tier the eater's CULTURAL DEPTH has reached. Tier 0 is
        free; tier t>=1 is edible only by an agent whose deepest known technique level (pop.tech, the realized
        depth of its repertoire on the GENERATIVE grown tree) is >= recipe_level_step * t. So embodied diet is
        gated DIRECTLY on how deep the open-ended culture has grown — no pre-designated recipe node, and the
        diet CEILING is open-ended because the grown tree's depth is (cap the tree -> depth freezes -> the high
        tiers can NEVER become edible). Tiers resolve high->low (richer first), each agent eats at most one
        mote/step, and the tier value (food_value*(1+tier_value_bonus*t)) feeds the usual harvest multipliers
        via _harvest_gain. Mirrors _eat_tech_actions; the ONLY change is the eligibility gate (depth, not node)."""
        cfg, p = self.cfg, self.pop
        act = p.active()
        ripe = np.where(self.food_ripe)[0]
        if ripe.size == 0:
            return
        keep = np.ones(self.food.shape[0], dtype=bool)
        eaten_agent = np.zeros(act.size, dtype=bool)         # at most one harvest per agent per step
        ripe_tier = self.food_tier[ripe]
        depth = p.tech[act]                                  # realized cultural depth per active agent (level units)
        for t in range(cfg.n_food_tiers - 1, -1, -1):
            fm = ripe[(ripe_tier == t) & keep[ripe]]         # ripe, this tier, not already eaten this step
            if fm.size == 0:
                continue
            if t == 0:
                elig = np.where(~eaten_agent)[0]             # tier 0 is the free resource (any depth)
            else:                                            # tier t needs cultural depth >= recipe_level_step*t
                elig = np.where((depth >= cfg.recipe_level_step * t) & ~eaten_agent)[0]
            if elig.size == 0:
                continue
            dist, idx = cKDTree(self.food[fm]).query(p.pos[act[elig]], k=1)
            reach = self._cap_reach(act[elig])               # R171: per-eater reach (depth-gated capability axis 1)
            winners, eaten = _resolve(dist, idx, reach)      # winners index into elig; eaten into fm
            if winners.size == 0:
                continue
            eaters = act[elig[winners]]
            base = np.full(eaters.size, cfg.food_value * (1.0 + cfg.tier_value_bonus * t))
            p.energy[eaters] += self._harvest_gain(eaters, base=base)
            keep[fm[eaten]] = False
            eaten_agent[elig[winners]] = True
            self._tier_eat_count[t] += int(eaten.size)
        if not keep.all():
            self._keep_food(keep)

    def diet_capability_ceiling(self) -> tuple[int, int]:
        """R171 read-out (read-only; no RNG, no state change): the living population's REALIZED embodied
        ceiling under depth_gates. Returns (max_diet_tier, n_axes_unlocked):
          - max_diet_tier  = the deepest food tier ANY living agent can currently eat
                             (max over agents of min(floor(depth / recipe_level_step), n_food_tiers-1));
          - n_axes_unlocked = the most capability axes any living agent has unlocked
                             (max over agents of count of i in 0..n_capabilities-1 with depth >= step*(i+1)).
        Both are bounded above by the grown tree's depth, so they FREEZE when the tree is capped and CLIMB when
        it is not — the embodied signature of open-endedness. (0, 0) when no agent is alive."""
        cfg = self.cfg
        act = self.pop.active()
        if act.size == 0:
            return 0, 0
        depth = self.pop.tech[act]
        max_tier = int(np.clip(np.floor(depth / cfg.recipe_level_step), 0, cfg.n_food_tiers - 1).max())
        axes = np.array([(depth >= cfg.cap_level_step * (i + 1)).any() for i in range(cfg.n_capabilities)])
        return max_tier, int(axes.sum())

    def _do_trade(self, givers: np.ndarray, gain: np.ndarray, t: int) -> None:
        """R158 trade: each giver (just harvested a tier-t>=1 mote it alone could eat) offers trade_share of its
        gain to the nearest HUNGRY COMPLEMENTARY agent (lacks tier t's recipe -> physically could not eat this
        food) within trade_radius. Complementary specialists at a region BORDER thus feed each other -> a local
        inter-group economy that rescues pure specialists. The giver keeps its full harvest (surplus modeled as
        otherwise-spoiled), so the transfer is positive-sum. trade_scramble is the NULL: same shares delivered to
        UNIFORMLY-RANDOM hungry agents (locality + complementarity cut), isolating the economic content of WHO
        trades with whom from raw energy injection. Diagnostics only; never feeds selection."""
        cfg, p = self.cfg, self.pop
        if givers.size == 0:
            return
        act = p.active()
        recipe_t = self._recipe_tech[t]                          # this tier's branch (givers all hold it)
        hungry = p.energy[act] < cfg.e_repro * cfg.trade_need_frac
        share = cfg.trade_share * np.asarray(gain, dtype=float)  # per-giver surplus
        if cfg.trade_scramble:                                   # NULL: random hungry recipient, any branch/place
            cand = np.where(hungry)[0]
            if cand.size == 0:
                return
            pick = self.rng.integers(0, cand.size, size=givers.size)
            recv = act[cand[pick]]
            dist = np.linalg.norm(p.pos[givers] - p.pos[recv], axis=1)
        else:                                                    # REAL: nearest hungry COMPLEMENTARY neighbour
            compl = np.where(hungry & ~self.rep[act, recipe_t])[0]
            if compl.size == 0:
                return
            dist, idx = cKDTree(p.pos[act[compl]]).query(p.pos[givers], k=1)
            ok = dist < cfg.trade_radius
            if not ok.any():
                return
            givers, share, dist = givers[ok], share[ok], dist[ok]
            recv = act[compl[idx[ok]]]
        deliver = share * cfg.trade_gain
        np.add.at(p.energy, recv, deliver)                       # a recipient may be fed by several givers
        self._trade_count += int(recv.size)
        self._trade_volume += float(deliver.sum())
        self._trade_dist_sum += float(dist.sum())
        self._trade_compl += int((~self.rep[recv, recipe_t]).sum())  # recipients lacking tier t's recipe
        R = self.cfg.n_food_tiers - 1                            # cross-region (inter-group): giver vs receiver x-slab
        size = self.cfg.world.size
        gx = np.clip((p.pos[givers][:, 0] / size * R).astype(int), 0, R - 1)
        rx = np.clip((p.pos[recv][:, 0] / size * R).astype(int), 0, R - 1)
        self._trade_cross += int((gx != rx).sum())

    def _do_goods_trade(self, eaters: np.ndarray, fm: np.ndarray, keep: np.ndarray, t: int) -> None:
        """R159 PRODUCTIVE goods trade. Each eater (a tier-t>=1 specialist that just ate) acts as a HARVESTER FOR
        OTHERS: it claims up to goods_max of the still-uneaten ripe tier-t motes near it (within trade_radius) and
        ships each as an edible GOOD to the nearest HUNGRY COMPLEMENTARY partner (lacks tier t's recipe -> could
        never have harvested it). The mote is CONSUMED (keep=False -> a freed food slot regrows next step) and its
        full tier value is delivered (energy-conserving — no free injection; the food's energy simply reaches a
        mouth that could not reach it). Without this, those motes clog food slots uneaten -> the binding food-cap
        constraint that R158's energy-redistribution could not relax. trade_scramble is the NULL: same motes
        consumed and same energy delivered, but to UNIFORMLY-RANDOM hungry agents (locality + complementarity cut),
        isolating the division-of-labour content from raw food-slot freeing. Diagnostics only; never feeds selection."""
        cfg, p = self.cfg, self.pop
        if eaters.size == 0 or cfg.goods_max <= 0:
            return
        avail = fm[keep[fm]]                                     # ripe tier-t motes not yet eaten this step
        if avail.size == 0:
            return
        act = p.active()
        recipe_t = self._recipe_tech[t]
        # 1) assign each available mote to its NEAREST eater (harvester); keep only motes within trade_radius
        gd, gi = cKDTree(p.pos[eaters]).query(self.food[avail], k=1)
        within = gd < cfg.trade_radius
        if not within.any():
            return
        avail, gi = avail[within], gi[within]
        # 2) cap each harvester to goods_max motes (rank within giver-group, keep the first goods_max)
        order = np.argsort(gi, kind="stable")
        gi_s = gi[order]
        starts = np.concatenate(([0], np.where(gi_s[1:] != gi_s[:-1])[0] + 1))
        grp_start = np.repeat(starts, np.diff(np.append(starts, gi_s.size)))
        rank = np.arange(gi_s.size) - grp_start
        claimed = avail[order[rank < cfg.goods_max]]
        if claimed.size == 0:
            return
        # 3) ship each claimed mote to a hungry partner (complementary nearest, or scramble = random hungry)
        if cfg.trade_scramble:
            cand = np.where(p.energy[act] < cfg.e_repro * cfg.trade_need_frac)[0]
            if cand.size == 0:
                return
            recv = act[cand[self.rng.integers(0, cand.size, size=claimed.size)]]
            dist = np.linalg.norm(self.food[claimed] - p.pos[recv], axis=1)
        else:
            compl = np.where((p.energy[act] < cfg.e_repro * cfg.trade_need_frac) & ~self.rep[act, recipe_t])[0]
            if compl.size == 0:
                return
            dist, idx = cKDTree(p.pos[act[compl]]).query(self.food[claimed], k=1)
            ok = dist < cfg.trade_radius
            if not ok.any():
                return
            claimed, dist = claimed[ok], dist[ok]
            recv = act[compl[idx[ok]]]
        value = cfg.food_value * (1.0 + cfg.tier_value_bonus * t)
        np.add.at(p.energy, recv, value)
        np.minimum(p.energy, cfg.e_max, out=p.energy)            # can't hoard past e_max (same ceiling as eating)
        keep[claimed] = False                                    # mote consumed -> food slot freed for regrowth
        self._goods_count += int(recv.size)
        self._goods_motes += int(claimed.size)
        self._goods_volume += float(value * recv.size)
        self._goods_dist_sum += float(dist.sum())

    def _eat_cap_niches(self) -> None:
        """R155 eat: ripe food in a KEYED niche is harvestable ONLY by an agent holding that niche's capability
        node; the FREE niche (-1) is edible by anyone. Each agent eats at most one mote/step. Keyed motes are
        richer (food_value*(1+niche_value_bonus)) so holding a key PAYS, and the harvest flows through the usual
        caste/technique multipliers via _harvest_gain and pays the processor wage when specialize is on. Because
        an agent's capability budget bounds how many keys it can hold (see _enforce_cap_budget), different
        lineages exploit different niches -> a division of labour; the free niche keeps naive founders alive
        while the keys bootstrap. Per-eater reach is the R154 culture-gated radius. Keyed niches are resolved
        before the free one so a specialist gets first claim on its own resource."""
        cfg, p = self.cfg, self.pop
        act = p.active()
        ripe = np.where(self.food_ripe)[0]
        if ripe.size == 0:
            return
        keep = np.ones(self.food.shape[0], dtype=bool)
        eaten_agent = np.zeros(act.size, dtype=bool)         # at most one harvest per agent per step
        ripe_niche = self.food_niche[ripe]
        for nv in list(range(cfg.n_capabilities)) + [-1]:    # keyed niches first, then the free niche
            fm = ripe[(ripe_niche == nv) & keep[ripe]]       # ripe, this niche, not already eaten this step
            if fm.size == 0:
                continue
            if nv < 0:
                elig = np.where(~eaten_agent)[0]             # free resource: anyone may harvest
            else:
                elig = np.where(self.rep[act, self._cap_tech[nv]] & ~eaten_agent)[0]  # key-holders only
            if elig.size == 0:
                continue
            dist, idx = cKDTree(self.food[fm]).query(p.pos[act[elig]], k=1)
            reach = self._cap_reach(act[elig])               # R154: per-eater harvest reach (culture-gated)
            winners, eaten = _resolve(dist, idx, reach)      # winners index into elig; eaten into fm
            if winners.size == 0:
                continue
            eaters = act[elig[winners]]
            bonus = 0.0 if nv < 0 else cfg.niche_value_bonus
            base = np.full(eaters.size, cfg.food_value * (1.0 + bonus))
            p.energy[eaters] += self._harvest_gain(eaters, base=base)
            if self.specialize:                              # wage to whoever ripened each eaten mote (trade)
                self._pay_processors(fm[eaten])
            keep[fm[eaten]] = False
            eaten_agent[elig[winners]] = True
        if not keep.all():
            self._keep_food(keep)

    # --- division of labour (R146) ---
    def _process(self, act: np.ndarray, out: np.ndarray) -> None:
        """Processors ripen nearby RAW food into edible food (a local public good), paying process_cost.

        The evolved process-gate output decides who processes; scramble_allocation replaces it with a
        Bernoulli draw at the same mean rate (the allocation-ablation control). A single process act
        ripens every raw mote within process_radius — a strong public good (one processor can feed many
        harvesters), so the kin-structured division of labour has a real fitness gradient to climb."""
        cfg, p = self.cfg, self.pop
        gate = out[:, self._proc_out] > 0.0                 # tanh>0 -> intends to process
        if cfg.scramble_allocation:                         # same budget, conditioning destroyed
            rate = float(gate.mean()) if gate.size else 0.0
            gate = self.rng.random(act.size) < rate
        procs = np.where(gate)[0]                            # rows in act
        raw = np.where(~self.food_ripe)[0]
        if procs.size == 0 or raw.size == 0:
            return
        d, near = cKDTree(p.pos[act[procs]]).query(self.food[raw], k=1)  # nearest processor per raw mote
        if self.specialize:                                  # reach scales with caste -> ripened volume ~spec^3
            reach = cfg.process_radius * p.spec[act[procs]]
            in_range = d < reach[near]
        else:
            in_range = d < cfg.process_radius
        if not in_range.any():
            return
        ripened = raw[in_range]
        self.food_ripe[ripened] = True
        self.ripe_age[ripened] = 0
        if self.specialize:                                  # record who ripened each mote (for the wage)
            self.food_proc[ripened] = act[procs[near[in_range]]]
        workers = np.unique(near[in_range])                  # processors that ripened >=1 mote -> pay cost
        p.energy[act[procs[workers]]] -= cfg.process_cost

    def _pay_processors(self, eaten_global: np.ndarray) -> None:
        """Pay the processor that ripened each just-harvested mote (R147 wage / trade). Processors live on
        these wages, harvesters on the food itself -> genuine producer/consumer interdependence."""
        proc = self.food_proc[eaten_global]
        valid = proc[(proc >= 0) & self.pop.alive[proc]]    # only credit still-living processors
        if valid.size:
            np.add.at(self.pop.energy, valid, self.cfg.process_payment)

    # --- cumulative culture (R149) ---
    def _acquire_tech(self, slots: np.ndarray, parents: np.ndarray) -> None:
        """A newborn ACQUIRES its lifetime technique (R149). Social learning: copy (with culture_fidelity) the best
        model available — the technique recorded at the nearest STRONG hearth (an artifact carrying ancestral
        knowledge) or the parent — then add ONE innovation step (only its positive part). learn=False is the
        ASOCIAL control: base is forced to 0, so each agent reaches only its own one-lifetime innovation ceiling
        and the cross-generation ratchet cannot form. tech is NOT genetic and NOT mutated from the genome."""
        cfg, p = self.cfg, self.pop
        n = slots.size
        if self.combinatorial:
            self._acquire_repertoire(slots, parents)
            return
        if cfg.learn:
            source = p.tech[parents].copy()                  # vertical transmission baseline (the parent's tech)
            strong = self._strong_hearths()
            if strong.size and not cfg.vertical_only:         # oblique transmission via the built world (hearths)
                d, idx = cKDTree(self.struct_pos[strong]).query(p.pos[slots], k=1)
                in_range = d < cfg.hearth_radius
                hearth_tech = np.where(in_range, self.struct_tech[strong][idx], 0.0)
                source = np.maximum(source, hearth_tech)     # copy the BEST model in reach
            base = cfg.culture_fidelity * source             # imperfect copy -> transmission loss
        else:
            base = np.zeros(n)                               # asocial: no copying, reinvent from scratch
        innov = np.maximum(0.0, self.rng.normal(cfg.innov_mean, cfg.innov_sigma, size=n))
        p.tech[slots] = base + innov

    # --- open-ended combinatorial culture (R150) ---
    def _acquire_repertoire(self, slots: np.ndarray, parents: np.ndarray) -> None:
        """A newborn ACQUIRES a combinatorial REPERTOIRE (R150). Social learning: copy (each bit kept w.p.
        culture_fidelity) the union of its parent's repertoire and the nearest STRONG hearth's accumulated
        record, then make innov_steps discoveries from its ADJACENT POSSIBLE (techniques whose prerequisites
        it now knows). learn=False is the ASOCIAL control: no copying, so each agent explores only from an
        empty repertoire in one lifetime and the trans-generational frontier cannot form. The repertoire is
        NOT genetic. `tech` (the harvest payoff) is set to the deepest technique LEVEL known, so mastery pays."""
        from . import combinatorial as cb
        cfg = self.cfg
        K = cfg.max_techniques
        if cfg.learn:
            source = self.rep[parents].copy()                # vertical transmission: the parent's repertoire
            strong = self._strong_hearths()
            if strong.size and not cfg.vertical_only:         # oblique transmission via the built world (hearths)
                d, idx = cKDTree(self.struct_pos[strong]).query(self.pop.pos[slots], k=1)
                in_range = d < cfg.hearth_radius
                if in_range.any():
                    rows = np.where(in_range)[0]
                    if cfg.panmictic_culture:                # R156 NULL: same learners, but copy a RANDOM global
                        src = self.rng.integers(0, strong.size, size=rows.size)   # hearth (place<->tradition link cut)
                        source[rows] |= self.struct_rep[strong][src]
                    else:
                        source[rows] |= self.struct_rep[strong][idx[rows]]   # learn the BEST record in reach (nearest)
            child = cb.copy_with_fidelity(source, cfg.culture_fidelity, self.rng)
        else:
            child = np.zeros((slots.size, K), dtype=bool)    # asocial: no copying, reinvent from scratch
        if self.generative_tree:                             # R170: grow the open-ended tree from real compositions
            child[:, :cfg.n_seed_tech] = True                # the level-0 primitives are universal -> can compose
            self._tree.discover_inplace(child, self.rng, cfg.innov_steps)
        else:
            cb.discover_inplace(child, self._tree_pa, self._tree_pb, cfg.n_seed_tech,
                                cfg.combo_prereqs, self.rng, cfg.innov_steps)
        if self.cap_niches:                                  # R155: bound the capability keys to the somatic budget
            child = self._enforce_cap_budget(child, parents)
        if self.tech_actions and cfg.recipe_budget > 0:      # R157: bound carried recipe BRANCHES -> specialists
            child = self._enforce_recipe_budget(child, parents)
        self.rep[slots] = child
        self.pop.tech[slots] = cb.max_level_known(child, self._tree_level)

    def _enforce_recipe_budget(self, child: np.ndarray, parents: np.ndarray) -> np.ndarray:
        """R157: bound each newborn to at most recipe_budget LOCKED-tier recipe branches so it cannot be a
        generalist holding every branch — the keystone that lets spatial selection sort branches into regions.
        Kept branches PREFER the parent's (a heritable cultural lineage), filling any remaining budget from
        newly-acquired branches (random tie-break). Only the recipe columns are touched. Mirrors R155's
        _enforce_cap_budget exactly, on self._recipe_tech[1:] instead of the capability nodes."""
        cfg = self.cfg
        rec = self._recipe_tech[1:]                            # locked-tier recipe ids, len n_food_tiers-1
        held = child[:, rec]                                  # [n, B] branches the child acquired
        budget = cfg.recipe_budget
        if budget >= rec.size:
            return child
        over = held.sum(axis=1) > budget
        if not over.any():
            return child
        parent_held = self.rep[parents][:, rec]              # [n, B] the parent's branches (heritable preference)
        jitter = 1e-3 * self.rng.random(held.shape)
        score = np.where(held, (1.0 + parent_held.astype(float)) + jitter, -1.0)
        for r in np.where(over)[0]:
            keep_idx = np.argsort(score[r])[::-1][:budget]   # the budget highest-priority HELD branches
            newrow = np.zeros(rec.size, dtype=bool)
            newrow[keep_idx] = True
            child[r, rec] = newrow & held[r]                 # never resurrect a branch the child did not acquire
        return child

    def _enforce_cap_budget(self, child: np.ndarray, parents: np.ndarray) -> np.ndarray:
        """R155: bound each newborn to at most cap_budget capability KEYS, so it cannot carry every key and
        must specialize. The kept keys PREFER the parent's keys (the capability profile is heritable -> a
        cultural lineage), filling any remaining budget from newly-acquired keys (random tie-break). Only the
        capability columns are touched; the rest of the repertoire is left intact. cap_force_mono is the
        MONOCULTURE control: every agent keeps ONLY key 0 (so niche>0 food is wasted -> a smaller population
        than the freely-specializing mixed world). With cap_budget >= n_capabilities and no force_mono this is
        a no-op."""
        cfg = self.cfg
        cap = self._cap_tech                                  # capability node ids, len n_capabilities
        held = child[:, cap]                                  # [n, C] keys the child acquired
        if cfg.cap_force_mono:                                # control: collapse to key 0 only
            newcols = np.zeros_like(held)
            newcols[:, 0] = held[:, 0]
            child[:, cap] = newcols
            return child
        budget = cfg.cap_budget
        if budget >= cap.size:
            return child
        over = held.sum(axis=1) > budget
        if not over.any():
            return child
        parent_held = self.rep[parents][:, cap]              # [n, C] the parent's keys (heritable preference)
        # priority of a HELD key: parent's keys score ~2, other acquired keys ~1, with a small random jitter
        # to break ties; non-held keys score -1 so they are never kept.
        jitter = 1e-3 * self.rng.random(held.shape)
        score = np.where(held, (1.0 + parent_held.astype(float)) + jitter, -1.0)
        for r in np.where(over)[0]:
            keep_idx = np.argsort(score[r])[::-1][:budget]   # the budget highest-priority HELD keys
            newrow = np.zeros(cap.size, dtype=bool)
            newrow[keep_idx] = True
            child[r, cap] = newrow & held[r]                 # never resurrect a key the child did not acquire
        return child

    def combinatorial_test(self) -> dict:
        """The R150 open-ended-culture read-out (in situ; never feeds selection). The headline complexity
        metric is the LIVING population's repertoire SIZE — distinct techniques collectively known — which
        keeps climbing under combinatorial discovery and collapses without transmission.
          - pop_distinct   : techniques known by >=1 living agent (the open-ended complexity metric).
          - hearth_distinct: techniques in the hearth records (the built cultural store).
          - max_level      : deepest tech-tree level reached by the living population (frontier depth).
          - mean_level     : mean deepest-level-known across living agents (= mean tech, the payoff).
          - mean_gen       : mean generation depth (the climb is read against this).
        """
        if not self.combinatorial:
            return {}
        p = self.pop
        act = p.active()
        if act.size < 20:
            return {}
        pop_union = self.rep[act].any(axis=0)
        strong = self._strong_hearths()
        hearth_union = (self.struct_rep[strong].any(axis=0) if strong.size
                        else np.zeros(self.cfg.max_techniques, dtype=bool))
        return {
            "pop_distinct": int(pop_union.sum()),
            "hearth_distinct": int(hearth_union.sum()),
            "max_level": int(self._tree_level[pop_union].max()) if pop_union.any() else 0,
            "mean_level": float(p.tech[act].mean()),
            "mean_gen": float(p.generation[act].mean()),
            "n": int(act.size),
        }

    def _update_tech_history(self) -> None:
        """R163 passive observer: stamp the current step as the FIRST appearance of any technique now present
        in the living population but never seen before. Reads self.rep only — no RNG, no state mutation, so
        track_tech_history is byte-identical to off."""
        act = self.pop.active()
        if act.size == 0:
            return
        present = self.rep[act].any(axis=0)
        newly = present & (self._tech_first_step < 0)
        self._tech_first_step[newly] = self.step_count

    def temporal_phylogeny_test(self, n_perm: int = 200) -> dict:
        """R163 read-out: does the population's first-appearance TIME of each technique RECOVER the generative
        tech tree (the time-ladder of cumulative descent)? Reuses the passive track_tech_history log. Returns
        the temporal-ladder signal (precedence + level<->time Spearman vs a label-permutation null) plus the
        open-ended complexity snapshot (max_level / pop_distinct). Requires track_tech_history; in situ."""
        from . import phylogeny as ph
        if not self.combinatorial or not self.cfg.track_tech_history:
            return {}
        first = self._tech_first_step
        if int((first >= 0).sum()) < 4:
            return {}
        sig = ph.temporal_ladder_signal(first, self._tree_level, self._tree_pa, self._tree_pb,
                                        self.cfg.n_seed_tech, n_perm)
        act = self.pop.active()
        pop_union = (self.rep[act].any(axis=0) if act.size
                     else np.zeros(self.cfg.max_techniques, dtype=bool))
        sig["max_level"] = int(self._tree_level[pop_union].max()) if pop_union.any() else 0
        sig["pop_distinct"] = int(pop_union.sum())
        sig["n"] = int(act.size)
        return sig

    def tradition_test(self, grid: int = 2, min_deme: int = 15) -> dict:
        """R156 read-out: do distinct spatial groups climb distinct BRANCHES of the open-ended tree ->
        divergent cultural TRADITIONS? Partitions the living population into a grid^3 spatial lattice of
        demes and measures Wright's F_ST over the boolean technique repertoire (cultural traits):
        F_ST = (H_T - H_S)/H_T, where H_T is the pooled and H_S the mean within-deme gene-diversity
        (2 p (1-p)). F_ST ~ 0 = one global tradition (panmictic mixing); F_ST > 0 = spatially structured
        traditions. Also reports how many DISTINCT deme-dominant deepest techniques exist (distinct
        traditions) and each deme's dominant deep technique. In situ; never feeds selection."""
        if not self.combinatorial:
            return {}
        p = self.pop
        act = p.active()
        if act.size < min_deme * 2:
            return {}
        pos = p.pos[act]
        rep = self.rep[act]                                       # [n, K] bool repertoires
        size = self.cfg.world.size
        cell = np.clip((pos / size * grid).astype(int), 0, grid - 1)   # [n, 3] lattice cell
        deme_id = (cell[:, 0] * grid + cell[:, 1]) * grid + cell[:, 2]  # 0..grid^3-1
        freqs, counts = [], []
        for d in np.unique(deme_id):
            rows = np.where(deme_id == d)[0]
            if rows.size < min_deme:
                continue
            freqs.append(rep[rows].mean(axis=0))                 # [K] per-technique freq in this deme
            counts.append(rows.size)
        if len(freqs) < 2:
            return {"n_demes": len(freqs), "fst": 0.0, "n_distinct_traditions": len(freqs)}
        freqs = np.array(freqs)                                   # [D, K]
        w = np.array(counts, dtype=float)
        w = w / w.sum()
        p_bar = (freqs * w[:, None]).sum(axis=0)                 # pooled per-technique freq [K]
        H_T = float((2.0 * p_bar * (1.0 - p_bar)).mean())
        H_S = float((w[:, None] * (2.0 * freqs * (1.0 - freqs))).sum(axis=0).mean())
        fst = float(np.clip((H_T - H_S) / H_T, 0.0, 1.0)) if H_T > 1e-12 else 0.0
        level = self._tree_level                                  # deepest-technique signature per deme
        dom = [int(np.where(f >= 0.5, level, -1).argmax()) if (f >= 0.5).any() else -1 for f in freqs]
        return {
            "fst": fst, "n_demes": int(len(freqs)), "n_distinct_traditions": int(len(set(dom))),
            "dom_tech": dom, "H_T": H_T, "H_S": H_S, "n": int(act.size),
        }

    def phylogeny_test(self, grid: int = 3, min_deme: int = 15, n_shuffle: int = 20) -> dict:
        """R160 read-out: is the cultural divergence HIERARCHICALLY structured — a reconstructable cladogram
        of traditions (descent-with-modification), not a flat divergence? Partitions the living population
        into a grid^3 spatial lattice of demes (the taxa), builds the deme x technique frequency matrix
        (the character matrix), and measures two tree-signal statistics on the inter-deme L1 distances:
          - treelikeness : 1 - mean Holland delta-Q over deme quartets (1 = perfectly tree-additive).
          - coph_corr    : cophenetic correlation of the UPGMA tree (how well one nested hierarchy fits).
        The load-bearing NULL is a COLUMN-SHUFFLE (alife.genesis.phylogeny.column_shuffle_null): permute
        each technique independently across demes, preserving per-technique divergence but destroying the
        cross-technique covariance that bundles a tree branch into a clade -> real > shuffle isolates a
        genuine PHYLOGENETIC signal, not mere divergence. Also returns the inter-deme distance matrix and
        each deme's dominant deepest technique (for the cladogram render). In situ; never feeds selection."""
        from . import phylogeny as ph
        if not self.combinatorial:
            return {}
        p = self.pop
        act = p.active()
        if act.size < min_deme * 2:
            return {}
        pos = p.pos[act]
        rep = self.rep[act]                                       # [n, K] bool repertoires
        size = self.cfg.world.size
        cell = np.clip((pos / size * grid).astype(int), 0, grid - 1)
        deme_id = (cell[:, 0] * grid + cell[:, 1]) * grid + cell[:, 2]
        freqs, counts = [], []
        for d in np.unique(deme_id):
            rows = np.where(deme_id == d)[0]
            if rows.size < min_deme:
                continue
            freqs.append(rep[rows].mean(axis=0))                 # [K] per-technique freq in this deme
            counts.append(int(rows.size))
        if len(freqs) < 4:                                       # need >=4 taxa for quartet treelikeness
            return {"n_demes": int(len(freqs)), "n_informative": 0, "treelikeness": float("nan"),
                    "coph_corr": float("nan"), "shuffle_treelikeness": float("nan"),
                    "shuffle_coph": float("nan"), "dist": [], "dom_tech": [], "counts": counts,
                    "n": int(act.size)}
        freqs = np.array(freqs)                                   # [D, K]
        info = ph.informative_columns(freqs)
        f_inf = freqs[:, info]
        dist = ph.l1_distance_matrix(f_inf)
        null = ph.column_shuffle_null(freqs, n_shuffle)
        level = self._tree_level
        dom = [int(np.where(f >= 0.5, level, -1).argmax()) if (f >= 0.5).any() else -1 for f in freqs]
        return {
            "n_demes": int(len(freqs)),
            "n_informative": int(info.sum()),
            "treelikeness": ph.treelikeness(dist),
            "coph_corr": ph.cophenetic_corr(dist),
            "shuffle_treelikeness": null["treelikeness"],
            "shuffle_coph": null["coph_corr"],
            "dist": dist.tolist(),
            "dom_tech": dom,
            "counts": counts,
            "n": int(act.size),
        }

    def genealogy_phylogeny_test(self, grid: int = 3, min_deme: int = 15, sample_per_deme: int = 12,
                                 n_perm: int = 999, seed: int = 20250621) -> dict:
        """R161 GROUND-TRUTH read-out: does the reconstructed cultural cladogram RECOVER the true line of descent?
        Requires track_genealogy. Partitions the living pop into a grid^3 spatial lattice of demes (the taxa) and
        builds two inter-deme distance matrices: (a) RECONSTRUCTED CULTURAL distance = mean-L1 over the informative
        technique columns (the same character distance R160's cladogram is built from); (b) TRUE GENEALOGICAL
        distance = mean pairwise patristic (birth-forest) distance between up to sample_per_deme members of each
        pair of demes (the diagonal is each deme's mean WITHIN-deme patristic distance). Headline = a Mantel
        correlation between the two against a label-permutation null: does cultural similarity track REAL descent?
        This upgrades R160's "tree-like vs a flat shuffle" to "recovers the TRUE tree". In situ; never feeds selection."""
        from . import genealogy as gn
        from . import phylogeny as ph
        if not self.combinatorial or not self.cfg.track_genealogy:
            return {}
        p = self.pop
        act = p.active()
        if act.size < min_deme * 2:
            return {}
        pos = p.pos[act]
        rep = self.rep[act]
        size = self.cfg.world.size
        cell = np.clip((pos / size * grid).astype(int), 0, grid - 1)
        deme_id = (cell[:, 0] * grid + cell[:, 1]) * grid + cell[:, 2]
        gnode = self._gen_node[act]                              # genealogy node id per living agent
        parent = np.array(self._gen_parent, dtype=np.int64)
        rng = np.random.default_rng(seed)
        freqs, samp_nodes, counts, centroids = [], [], [], []
        for d in np.unique(deme_id):
            rows = np.where(deme_id == d)[0]
            if rows.size < min_deme:
                continue
            freqs.append(rep[rows].mean(axis=0))
            centroids.append(pos[rows].mean(axis=0))            # R162: deme centroid -> inter-deme spatial dist
            nd = gnode[rows]
            if nd.size > sample_per_deme:                       # subsample members for the O(S^2) patristic block
                nd = rng.choice(nd, size=sample_per_deme, replace=False)
            samp_nodes.append(nd)
            counts.append(int(rows.size))
        D = len(freqs)
        empty = {"n_demes": D, "n_informative": 0, "mantel_corr": float("nan"),
                 "mantel_null_mean": float("nan"), "mantel_null_std": float("nan"), "mantel_z": float("nan"),
                 "mantel_p": float("nan"), "n_perm": 0, "treelikeness": float("nan"),
                 "shuffle_treelikeness": float("nan"), "d_cult": [], "d_gen": [], "d_spatial": [],
                 "partial_mantel_corr": float("nan"), "partial_mantel_p": float("nan"),
                 "partial_mantel_z": float("nan"), "dom_tech": [], "counts": counts, "n": int(act.size)}
        if D < 4:
            return empty
        freqs = np.array(freqs)
        info = ph.informative_columns(freqs)
        d_cult = ph.l1_distance_matrix(freqs[:, info])
        allnodes = np.concatenate(samp_nodes)
        P = gn.patristic_distance_matrix(parent, allnodes)      # [S, S] patristic distance among sampled members
        idx = np.concatenate([np.full(len(samp_nodes[i]), i) for i in range(D)])
        d_gen = np.zeros((D, D))
        for i in range(D):
            for j in range(i, D):
                block = P[np.ix_(idx == i, idx == j)]
                if i == j:
                    m = block.shape[0]
                    vals = block[np.triu_indices(m, k=1)] if m > 1 else np.zeros(1)
                    val = float(vals.mean()) if vals.size else 0.0
                else:
                    val = float(block.mean())
                d_gen[i, j] = d_gen[j, i] = val
        mt = gn.mantel_test(d_cult, d_gen, n_perm=n_perm, seed=seed)
        cen = np.array(centroids)                               # R162: inter-deme spatial (centroid) distances
        d_spatial = np.linalg.norm(cen[:, None, :] - cen[None, :, :], axis=-1)
        pmt = gn.partial_mantel_test(d_cult, d_gen, d_spatial, n_perm=n_perm, seed=seed)  # control for space
        null = ph.column_shuffle_null(freqs, 20)
        level = self._tree_level
        dom = [int(np.where(f >= 0.5, level, -1).argmax()) if (f >= 0.5).any() else -1 for f in freqs]
        return {
            "n_demes": D, "n_informative": int(info.sum()),
            "mantel_corr": mt["corr"], "mantel_null_mean": mt["null_mean"], "mantel_null_std": mt["null_std"],
            "mantel_z": mt["z"], "mantel_p": mt["p"], "n_perm": mt["n_perm"],
            "treelikeness": ph.treelikeness(d_cult), "shuffle_treelikeness": null["treelikeness"],
            "partial_mantel_corr": pmt["corr"], "partial_mantel_p": pmt["p"], "partial_mantel_z": pmt["z"],
            "d_cult": d_cult.tolist(), "d_gen": d_gen.tolist(), "d_spatial": d_spatial.tolist(),
            "dom_tech": dom, "counts": counts, "n": int(act.size),
        }

    def ecological_traditions_test(self, min_region: int = 20) -> dict:
        """R157 read-out: does ECOLOGICAL selection lock each spatial REGION to its OWN recipe BRANCH? Partitions
        the living population into n_food_tiers-1 x-axis slabs (the same regions spatial_tiers uses to assign
        food) and, per region r, measures the fraction of agents holding region r's OWN branch (recipe for tier
        r+1) vs the mean fraction holding the OTHER regions' branches. ALIGNMENT = own - other (averaged over
        regions): >0 means each region is enriched for its own branch (a spatially-locked, economically-distinct
        tradition); ~0 means branches are spatially mixed (drift). `aligned_regions` = regions whose own branch
        is their MODAL branch. In situ; never feeds selection. Requires tech_actions."""
        if not self.tech_actions:
            return {}
        p = self.pop
        act = p.active()
        recipes = self._recipe_tech[1:]                          # recipe id for tier 1..T-1; region r -> tier r+1
        R = recipes.size
        if act.size < min_region * 2 or R < 2:
            return {}
        pos = p.pos[act]
        held = self.rep[np.ix_(act, recipes)]                    # [n, R] which branch each agent holds
        size = self.cfg.world.size
        region = np.clip((pos[:, 0] / size * R).astype(int), 0, R - 1)   # x-slab region per agent
        own, other, modal_own, n_reg = [], [], 0, 0
        for r in range(R):
            rows = np.where(region == r)[0]
            if rows.size < min_region:
                continue
            frac = held[rows].mean(axis=0)                       # [R] fraction holding each branch in region r
            own.append(float(frac[r]))
            other.append(float((frac.sum() - frac[r]) / (R - 1)))
            if frac.argmax() == r and frac[r] > 0:
                modal_own += 1
            n_reg += 1
        if not own:
            return {"n_regions": 0, "alignment": 0.0, "aligned_regions": 0, "n_branches": int(R)}
        own_m, other_m = float(np.mean(own)), float(np.mean(other))
        return {
            "n_regions": int(n_reg), "n_branches": int(R), "own_frac": own_m, "other_frac": other_m,
            "alignment": own_m - other_m, "aligned_regions": int(modal_own), "n": int(act.size),
        }

    def trade_test(self) -> dict:
        """R158 read-out: the inter-group ECONOMY's structure (in situ; never feeds selection). Cumulative over
        the run; diff across windows for a rate. The discriminators between a real economy and the scrambled
        null are SPATIAL (real trades are local) and ECONOMIC (real partners are complementary):
          - trade_count        : number of surplus transfers executed.
          - trade_volume       : total energy delivered via trade.
          - mean_partner_dist  : mean giver<->receiver distance (small = a LOCAL market; large = scrambled).
          - complementary_frac : fraction of transfers whose receiver LACKS the traded tier's recipe (1.0 by
                                 construction for real trade; ~random for the scramble) = genuine exchange of
                                 a good the receiver could not have produced itself.
          - cross_region_frac  : fraction of transfers connecting agents in DIFFERENT x-regions. NOT enforced by
                                 the trade rule (which never reads region) -> it EMERGES from R157's spatial
                                 sorting (complementary branches sit in different regions): segregated groups
                                 coupled by exchange across their borders = the inter-group economy signature.
        """
        if not self.trade:
            return {}
        n = self._trade_count
        return {
            "trade_count": int(n),
            "trade_volume": float(self._trade_volume),
            "mean_partner_dist": float(self._trade_dist_sum / n) if n else 0.0,
            "complementary_frac": float(self._trade_compl / n) if n else 0.0,
            "cross_region_frac": float(self._trade_cross / n) if n else 0.0,
        }

    def goods_test(self) -> dict:
        """R159 read-out: the PRODUCTIVE goods economy (in situ; never feeds selection). Cumulative over the run.
          - goods_count        : number of goods deliveries (a harvested mote shipped to a hungry partner).
          - goods_motes        : wasted tier-t motes consumed-for-trade = food slots FREED for regrowth (the
                                 mechanism by which trade relaxes the food-cap constraint).
          - goods_volume       : total energy delivered as goods (energy-conserving = goods_motes x tier value).
          - mean_partner_dist  : mean mote<->receiver distance (small = a LOCAL market; large = scrambled).
        Empty when trade_goods is off."""
        if not self.trade_goods:
            return {}
        n = self._goods_count
        return {
            "goods_count": int(n),
            "goods_motes": int(self._goods_motes),
            "goods_volume": float(self._goods_volume),
            "mean_partner_dist": float(self._goods_dist_sum / n) if n else 0.0,
        }

    def tech_actions_test(self) -> dict:
        """The R153 read-out: how far culture has UNLOCKED physical world-actions (food tiers). In situ.
          - realized_tiers   : 1 + number of locked tiers whose recipe >=1 LIVING agent knows (the headline:
                               how much of the world the population can physically exploit; climbs with culture).
          - max_tiers        : the ceiling (n_food_tiers).
          - mean_edible_tiers: mean per-agent count of edible tiers (the realized DIET BREADTH of an individual).
          - locked_food_frac : fraction of standing RIPE food that no living agent can eat (high when culture is
                               shallow -> rich food rots uneaten; falls as the population unlocks tiers).
          - tier_eats        : cumulative harvested-mote count per tier (lifetime; diff across windows for a rate).
        """
        if not self.tech_actions:
            return {}
        p = self.pop
        act = p.active()
        T = self.cfg.n_food_tiers
        recipes = self._recipe_tech[1:]                          # recipe technique id per locked tier 1..T-1
        if act.size:
            per_agent = self.rep[np.ix_(act, recipes)]           # [n, T-1] which locked tiers each agent unlocks
            known_any = per_agent.any(axis=0)
            mean_edible_tiers = 1.0 + float(per_agent.sum(axis=1).mean())
        else:
            known_any = np.zeros(T - 1, dtype=bool)
            mean_edible_tiers = 0.0
        ripe = self.food_ripe
        if ripe.any():
            tier_known = np.ones(T, dtype=bool)
            tier_known[1:] = known_any
            locked_food_frac = float((~tier_known[self.food_tier[ripe]]).mean())
        else:
            locked_food_frac = 0.0
        return {
            "realized_tiers": 1 + int(known_any.sum()),
            "max_tiers": int(T),
            "mean_edible_tiers": mean_edible_tiers,
            "locked_food_frac": locked_food_frac,
            "tier_eats": self._tier_eat_count.tolist(),
            "n": int(act.size),
        }

    def tech_capabilities_test(self) -> dict:
        """The R154 read-out: how far culture has unlocked each PHYSICAL capability axis, and the REALIZED
        physical phenotype it produces. In situ; never feeds selection.
          - realized_axes      : number of capability axes >=1 LIVING agent has unlocked (the headline).
          - n_axes             : the ceiling (n_capabilities).
          - frac_unlocked      : per-axis fraction of living agents holding that node [list, len n_axes].
          - mean_axes          : mean per-agent count of unlocked axes (capability breadth of an individual).
          - mean_speed_cap     : mean per-agent MAX speed actually in force (physical: base when no locomotion).
          - mean_reach         : mean per-agent eat radius actually in force (physical: base when no reach node).
          - mean_realized_speed: mean per-agent realized |velocity| (the locomotion node should raise it).
        """
        if not self.tech_capabilities:
            return {}
        cfg, p = self.cfg, self.pop
        act = p.active()
        C = cfg.n_capabilities
        if act.size == 0:
            return {"realized_axes": 0, "n_axes": int(C), "frac_unlocked": [0.0] * C,
                    "mean_axes": 0.0, "mean_speed_cap": cfg.speed, "mean_reach": cfg.eat_radius,
                    "mean_realized_speed": 0.0, "n": 0}
        held = self.rep[np.ix_(act, self._cap_tech)]             # [n, C] which axes each agent holds
        frac = held.mean(axis=0)
        speed_cap = np.asarray(self._cap_speed(act)).reshape(-1)  # per-agent max speed in force
        reach = np.asarray(self._cap_reach(act)).reshape(-1) if C >= 2 else np.full(act.size, cfg.eat_radius)
        return {
            "realized_axes": int(held.any(axis=0).sum()),
            "n_axes": int(C),
            "frac_unlocked": [float(x) for x in frac],
            "mean_axes": float(held.sum(axis=1).mean()),
            "mean_speed_cap": float(speed_cap.mean()),
            "mean_reach": float(reach.mean()),
            "mean_realized_speed": float(np.linalg.norm(p.vel[act], axis=1).mean()),
            "n": int(act.size),
        }

    def cap_specialize_test(self) -> dict:
        """The R155 read-out: has a DIVISION OF LABOUR over capability keys emerged in the LIVING population?
        In situ; never feeds selection.
          - frac_per_key    : fraction of living agents holding each capability key [list, len C].
          - mean_keys       : mean keys held per agent (the budget bounds this; R154/free converges to C).
          - profile_entropy : Shannon entropy (bits) of the distribution of capability PROFILES (the held-key
                              subset) across agents -> 0 when everyone shares one profile (monoculture /
                              R154 convergence), high when many distinct profiles coexist (a division of labour).
          - frac_keyed      : fraction holding >=1 key (vs naive agents living on free food only).
          - balance         : 1 - mean|frac_per_key - mean(frac_per_key)| normalised -> 1 when the keyed
                              niches are evenly covered (a balanced polymorphism), 0 when one key dominates.
          - keyed_food_frac : fraction of RIPE food sitting in keyed niches (the exploitable specialist resource).
        """
        if not self.cap_niches:
            return {}
        cfg, p = self.cfg, self.pop
        act = p.active()
        C = cfg.n_capabilities
        ripe = self.food_ripe
        keyed_food_frac = float((self.food_niche[ripe] >= 0).mean()) if ripe.any() else 0.0
        if act.size == 0:
            return {"frac_per_key": [0.0] * C, "mean_keys": 0.0, "profile_entropy": 0.0,
                    "frac_keyed": 0.0, "balance": 0.0, "keyed_food_frac": keyed_food_frac, "n": 0}
        held = self.rep[np.ix_(act, self._cap_tech)]             # [n, C] which keys each agent holds
        frac = held.mean(axis=0)
        # profile = the integer bitmask of held keys; entropy over its distribution across agents
        weights = (1 << np.arange(C)).astype(np.int64)
        profiles = (held.astype(np.int64) * weights[None, :]).sum(axis=1)
        _, counts = np.unique(profiles, return_counts=True)
        pr = counts / counts.sum()
        entropy = float(-(pr * np.log2(pr)).sum())
        mean_frac = float(frac.mean())
        spread = float(np.abs(frac - mean_frac).mean())
        balance = float(1.0 - spread / mean_frac) if mean_frac > 0 else 0.0
        return {
            "frac_per_key": [float(x) for x in frac],
            "mean_keys": float(held.sum(axis=1).mean()),
            "profile_entropy": entropy,
            "frac_keyed": float(held.any(axis=1).mean()),
            "balance": balance,
            "keyed_food_frac": keyed_food_frac,
            "n": int(act.size),
        }

    def culture_test(self) -> dict:
        """The R149 cumulative-culture read-out: how high has the learned technique RATCHETED, in the living
        population and in the built cultural record (hearths). In situ; never feeds selection.
          - tech_mean / tech_max          : the learned technique across the living population.
          - hearth_tech_mean / _max       : the technique stored in the hearths = the cultural record (the
                                            OPEN-ENDED metric that keeps climbing across generations).
          - mean_gen                      : mean generation depth (the ratchet is read against this).
        """
        if not self.culture:
            return {}
        p = self.pop
        act = p.active()
        if act.size < 20:
            return {}
        strong = self._strong_hearths()
        htech = self.struct_tech[strong]
        return {
            "tech_mean": float(p.tech[act].mean()),
            "tech_max": float(p.tech[act].max()),
            "hearth_tech_mean": float(htech.mean()) if htech.size else 0.0,
            "hearth_tech_max": float(htech.max()) if htech.size else 0.0,
            "mean_gen": float(p.generation[act].mean()),
            "n": int(act.size),
        }

    def _decay_ripe(self) -> None:
        """Uneaten ripe food ages and reverts to raw after ripe_ttl — ripe food is a FLOW, not a stock."""
        self.ripe_age[self.food_ripe] += 1
        expired = self.food_ripe & (self.ripe_age >= self.cfg.ripe_ttl)
        self.food_ripe[expired] = False
        self.ripe_age[expired] = 0

    # --- niche construction / building (R148) ---
    def _strong_hearths(self) -> np.ndarray:
        """Global indices of hearths invested past hearth_min_strength (the ones that ripen food + are sensed)."""
        return np.where(self.struct_alive & (self.struct_strength >= self.cfg.hearth_min_strength))[0]

    def _sense_hearths(self, pos, r, u, f) -> np.ndarray:
        """Prey body-frame sense of the nearest STRONG hearth (R148) -> (P,4). Lets agents navigate to
        settlements (where food ripens). Only strong hearths are sensed — a faint deposit is not yet a site."""
        strong = self._strong_hearths()
        if strong.size == 0:
            return np.zeros((pos.shape[0], 4))
        return _sense_kd(pos, r, u, f, self.struct_pos[strong], self.cfg.sense_range)

    def _build(self, act: np.ndarray, out: np.ndarray) -> None:
        """Builders (process-gate>0) deposit/reinforce a persistent hearth, paying build_cost. A build act
        within build_merge_radius of an existing hearth REINFORCES it (stigmergic accretion -> settlements);
        otherwise it FOUNDS a new one in a free slot. Founder/maintainer generations are tracked so ecological
        inheritance (later generations maintaining ancestors' hearths) is measurable."""
        cfg, p = self.cfg, self.pop
        gate = out[:, self._proc_out] > 0.0                 # reuse the process-gate output as the build gate
        builders = np.where(gate)[0]                         # rows in act
        if builders.size == 0:
            return
        bpos = p.pos[act[builders]]
        bgen = p.generation[act[builders]]
        btech = p.tech[act[builders]] if self.culture else None
        brep = self.rep[act[builders]] if self.combinatorial else None
        if self.build_specialized:                           # R152: build skill is convex in the caste trait
            bgain = cfg.build_gain * np.power(p.spec[act[builders]], cfg.build_spec_gamma)  # harvester -> ~0
        else:
            bgain = np.full(builders.size, cfg.build_gain)   # R148..R151: caste-free, every builder equal
        alive = np.where(self.struct_alive)[0]
        if alive.size:
            d, near = cKDTree(self.struct_pos[alive]).query(bpos, k=1)
            reinforce = d < cfg.build_merge_radius
        else:
            d = np.full(builders.size, np.inf)
            near = np.zeros(builders.size, dtype=int)
            reinforce = np.zeros(builders.size, dtype=bool)
        # REINFORCE existing hearths (accumulate strength; raise the maintainer generation)
        if reinforce.any():
            tgt = alive[near[reinforce]]
            np.add.at(self.struct_strength, tgt, bgain[reinforce])
            np.maximum.at(self.struct_max_gen, tgt, bgen[reinforce])
            if self.build_specialized:                       # the maintainer earns this hearth's wage (R152)
                self.struct_last_builder[tgt] = act[builders[reinforce]]
            if self.culture:                                 # the hearth records the BEST technique deposited
                np.maximum.at(self.struct_tech, tgt, btech[reinforce])
            if self.combinatorial:                           # the hearth ACCUMULATES the deposited repertoires
                if self.culture_decay:                       # R157: reinforce the per-technique decaying memory
                    np.add.at(self.struct_memory, tgt, brep[reinforce] * self.cfg.memory_reinforce)
                else:                                        # R150: a never-forgetting union (a growing store)
                    np.bitwise_or.at(self.struct_rep, tgt, brep[reinforce])
        # FOUND new hearths for builders with no hearth nearby (bounded by free slots)
        founders = np.where(~reinforce)[0]
        if founders.size:
            free = np.where(~self.struct_alive)[0]
            k = min(founders.size, free.size)
            if k:
                slots = free[:k]
                who = founders[:k]
                self.struct_pos[slots] = bpos[who]
                self.struct_strength[slots] = bgain[who]
                self.struct_birth[slots] = self.step_count
                if self.build_specialized:                   # founder is the first maintainer (earns the wage)
                    self.struct_last_builder[slots] = act[builders[who]]
                self.struct_founder_gen[slots] = bgen[who]
                self.struct_max_gen[slots] = bgen[who]
                if self.culture:
                    self.struct_tech[slots] = btech[who]     # a new hearth opens its record at the founder's tech
                if self.combinatorial:                       # a new hearth opens with the founder's repertoire
                    if self.culture_decay:                   # R157: seed its memory at the founder's techniques
                        self.struct_memory[slots] = brep[who].astype(np.float32) * self.cfg.memory_reinforce
                    else:
                        self.struct_rep[slots] = brep[who]
                self.struct_alive[slots] = True
        p.energy[act[builders]] -= cfg.build_cost            # every build act pays, found or reinforce

    def _ripen_hearths(self) -> None:
        """Raw food within hearth_radius of a strong hearth ripens passively (the persistent built labour).
        Re-applied each step, so food near a hearth stays a usable flow; food away from any hearth stays raw."""
        cfg = self.cfg
        strong = self._strong_hearths()
        raw = np.where(~self.food_ripe)[0]
        if strong.size == 0 or raw.size == 0:
            return
        d, near = cKDTree(self.struct_pos[strong]).query(self.food[raw], k=1)
        reach = np.minimum(cfg.hearth_radius, cfg.hearth_reach_per_strength * self.struct_strength[strong])
        mask = d < reach[near]                                # convex: reach grows with hearth strength
        ripened = raw[mask]
        if ripened.size:
            self.food_ripe[ripened] = True
            self.ripe_age[ripened] = 0
            if self.build_specialized:                        # credit the hearth's last maintainer for the wage
                self.food_proc[ripened] = self.struct_last_builder[strong[near[mask]]]  # (R152); -1 if abandoned

    def _decay_structures(self) -> None:
        """Hearths lose strength each step; one drops dead (slot freed) at strength<=0. build_persist=False
        wipes every hearth each step (the no-ecological-inheritance ablation)."""
        if not self.cfg.build_persist:
            self.struct_alive[:] = False
            self.struct_strength[:] = 0.0
            return
        live = self.struct_alive
        self.struct_strength[live] -= self.cfg.struct_decay
        gone = live & (self.struct_strength <= 0.0)
        self.struct_alive[gone] = False
        self.struct_strength[gone] = 0.0

    def _decay_memory(self) -> None:
        """R157: cultural LOSS. Each hearth's per-technique memory decays (memory_decay/step); the sensed,
        copyable record (struct_rep) is re-derived as memory >= memory_threshold. So a technique stays in a
        hearth's record only while it is re-deposited often enough to hold its memory above threshold —
        knowledge that is not actively practised is FORGOTTEN. This replaces R156's never-forgetting union,
        letting disused branches fade locally so regional traditions sharpen into discrete cultures. Runs
        before _reproduce so the oblique channel transmits the current record. No-op when culture_decay=off."""
        if not self.culture_decay:
            return
        live = self.struct_alive
        self.struct_memory[live] *= (1.0 - self.cfg.memory_decay)
        self.struct_rep = self.struct_memory >= self.cfg.memory_threshold

    def _die(self) -> None:
        cfg, p = self.cfg, self.pop
        act = p.active()
        if act.size == 0:
            return
        dead = act[(p.energy[act] <= 0.0) | (p.age[act] >= cfg.max_age)]
        if dead.size:
            self._death_age_sum += float(p.age[dead].sum())   # realized lifespans (R148 inheritance comparator)
            self._death_count += int(dead.size)
            p.kill(dead)

    # --- predators (R143) ---
    def _step_predators(self) -> None:
        cfg, w, pr = self.cfg, self.cfg.world, self.pred
        act = pr.active()
        if act.size:
            pos, vel = pr.pos[act], pr.vel[act]
            r, u, f = _body_frame(vel)
            prey_pos = self.pop.pos[self.pop.active()]
            qs = _sense_kd(pos, r, u, f, prey_pos, cfg.sense_range)         # nearest prey (4)
            e = (pr.energy[act] / cfg.pred_e_repro).reshape(-1, 1)
            out = brain.forward(pr.brains[act], self.pred_spec, np.concatenate([qs, e], axis=1))
            newvel = _act(out, r, u, f, vel, cfg.pred_force, cfg.min_speed, cfg.pred_speed)
            pr.vel[act] = newvel
            pr.pos[act] = w.clamp(pos + newvel)
            speed = np.linalg.norm(newvel, axis=1)
            pr.energy[act] = np.minimum(pr.energy[act] - (cfg.pred_base_cost + cfg.pred_move_cost * speed),
                                        cfg.pred_e_max)
            pr.age[act] += 1
            pr.cooldown[act] = np.maximum(pr.cooldown[act] - 1, 0)
        self._pred_catch()
        act = pr.active()
        if act.size:
            dead = act[(pr.energy[act] <= 0.0) | (pr.age[act] >= cfg.pred_max_age)]
            if dead.size:
                pr.kill(dead)
        self._pred_reproduce()

    def _pred_catch(self) -> None:
        cfg, pr, prey = self.cfg, self.pred, self.pop
        pa, qa = pr.active(), prey.active()
        if pa.size == 0 or qa.size == 0:
            return
        dist, idx = cKDTree(prey.pos[qa]).query(pr.pos[pa], k=1)            # nearest prey per predator
        ready = np.where(pr.cooldown[pa] == 0, dist, np.inf)               # only non-digesting predators
        hunters, caught = _resolve(ready, idx, cfg.catch_radius)           # one prey per closest hunter
        if hunters.size:
            pr.energy[pa[hunters]] += cfg.prey_energy_value
            pr.cooldown[pa[hunters]] = cfg.pred_handling
            prey.kill(qa[caught])

    def _pred_reproduce(self) -> None:
        cfg, w, pr = self.cfg, self.cfg.world, self.pred
        act = pr.active()
        if act.size == 0:
            return
        parents = act[pr.energy[act] >= cfg.pred_e_repro]
        if parents.size == 0:
            return
        slots = pr.alloc(parents.size)
        if slots.size == 0:
            return
        if slots.size < parents.size:
            parents = self.rng.choice(parents, size=slots.size, replace=False)
        pr.energy[parents] *= 0.5
        pr.energy[slots] = pr.energy[parents]
        pr.brains[slots] = (brain.mutate_brains(pr.brains[parents], self.rng, cfg.mut_rate, cfg.mut_sigma)
                            if self.evolve else pr.brains[parents])
        offset = self.rng.normal(0, cfg.birth_jitter, size=(parents.size, 3))
        pr.pos[slots] = w.clamp(pr.pos[parents] + offset)
        d = self.rng.normal(size=(parents.size, 3))
        pr.vel[slots] = d / np.linalg.norm(d, axis=1, keepdims=True) * cfg.min_speed
        pr.lineage[slots] = pr.lineage[parents]
        pr.generation[slots] = pr.generation[parents] + 1
        pr.color[slots] = pr.color[parents]

    def _reproduce(self) -> None:
        cfg, w, p = self.cfg, self.cfg.world, self.pop
        act = p.active()
        if act.size == 0:
            return
        parents = act[p.energy[act] >= cfg.e_repro]
        if parents.size == 0:
            return
        slots = p.alloc(parents.size)
        if slots.size == 0:
            return
        if slots.size < parents.size:                 # capacity-limited: pick which parents breed
            parents = self.rng.choice(parents, size=slots.size, replace=False)
        p.energy[parents] *= 0.5                        # 50/50 energy split
        p.energy[slots] = p.energy[parents]
        if self.evolve:
            p.brains[slots] = brain.mutate_brains(p.brains[parents], self.rng, cfg.mut_rate, cfg.mut_sigma)
            p.color[slots] = np.clip(p.color[parents] + self.rng.normal(0, 0.02, (parents.size, 3)), 0, 1)
        else:                                           # frozen control: exact copies, no innovation
            p.brains[slots] = p.brains[parents]
            p.color[slots] = p.color[parents]
        offset = self.rng.normal(0, cfg.birth_jitter, size=(parents.size, 3))
        p.pos[slots] = w.clamp(p.pos[parents] + offset)
        d = self.rng.normal(size=(parents.size, 3))
        p.vel[slots] = d / np.linalg.norm(d, axis=1, keepdims=True) * cfg.min_speed
        p.lineage[slots] = p.lineage[parents]
        p.generation[slots] = p.generation[parents] + 1
        if self.cfg.track_genealogy:                          # R161: record each birth as a new genealogy node
            for ps, cs in zip(parents.tolist(), slots.tolist()):
                self._gen_node[cs] = len(self._gen_parent)
                self._gen_parent.append(int(self._gen_node[ps]))
        if self.signalling:
            p.utterance[slots] = 0.0                      # newborns start mute (don't inherit a stale slot's signal)
        if cfg.n_food_types > 1:                          # diet is heritable + mutable -> niches evolve
            p.diet[slots] = np.clip(p.diet[parents] + self.rng.normal(0, cfg.diet_mut_sigma, parents.size),
                                    0.0, cfg.n_food_types - 1e-6)
        if cfg.specialize:                                # caste trait is heritable -> a DoL can evolve
            if cfg.force_generalist:
                p.spec[slots] = 0.5                       # monomorphic control: no caste innovation
            elif self.evolve:
                p.spec[slots] = np.clip(p.spec[parents]
                                        + self.rng.normal(0, cfg.spec_mut_sigma, parents.size), 0.0, 1.0)
            else:
                p.spec[slots] = p.spec[parents]           # frozen: inherit exactly, standing variation only
        if self.culture:                                  # ACQUIRE tech: social learning (copy a model) + innovate
            self._acquire_tech(slots, parents)

    def _spawn_food(self, n: int) -> np.ndarray:
        """Place n food motes. Uniform (R141) or clumped in fixed patches (R142 niches)."""
        cfg, w = self.cfg, self.cfg.world
        if cfg.food_mode == "patches" and self.patch_centers is not None:
            which = self.rng.integers(0, cfg.n_patches, size=n)
            pts = self.patch_centers[which] + self.rng.normal(0, cfg.patch_radius, size=(n, 3))
            return np.clip(pts, 0.0, w.size)
        return self.rng.uniform(0, w.size, size=(n, 3))   # uniform: identical RNG call to R141

    def _regrow(self) -> None:
        cfg = self.cfg
        need = min(cfg.food_regrow, cfg.food_cap - self.food.shape[0])
        if need > 0:
            new_food = self._spawn_food(need)
            self.food = np.vstack([self.food, new_food])
            self.food_type = np.concatenate([self.food_type, self._food_types(need)])
            self.food_tier = np.concatenate([self.food_tier, self._food_tiers(new_food)])
            if self.cap_niches:                              # R155 niche labels for the new motes (in sync only when on)
                self.food_niche = np.concatenate([self.food_niche, self._food_niches(need)])
            new_ripe = np.zeros(need, dtype=bool) if self.processing else np.ones(need, dtype=bool)
            self.food_ripe = np.concatenate([self.food_ripe, new_ripe])
            self.ripe_age = np.concatenate([self.ripe_age, np.zeros(need, dtype=np.int32)])
            self.food_proc = np.concatenate([self.food_proc, np.full(need, -1, dtype=np.int64)])

    # --- read-outs (in situ, never feed selection) ---
    def snapshot(self) -> dict:
        cfg, p = self.cfg, self.pop
        act = p.active()
        snap = {
            "step": self.step_count,
            "population": float(act.size),
            "food": float(self.food.shape[0]),
            "mean_energy": float(p.energy[act].mean()) if act.size else 0.0,
            "max_gen": float(p.generation[act].max()) if act.size else 0.0,
            "directedness": metrics.food_directedness(p.pos[act], p.vel[act], self.food, cfg.sense_range),
            "diversity": metrics.effective_lineages(p.lineage[act], self.lineage_first_step,
                                                    self.step_count, cfg.persist_steps),
            "diet_diversity": metrics.diet_diversity(p.diet[act], cfg.n_food_types),
            "predators": float(self.pred.n_alive) if self.pred is not None else 0.0,
            "flee": (metrics.flee_directedness(p.pos[act], p.vel[act],
                     self.pred.pos[self.pred.active()], cfg.sense_range)
                     if self.pred is not None else 0.0),
            "signal_mi": self._signal_mi(act),
            "ripe_food": float(self.food_ripe.sum()) if self.processing else 0.0,
            "spec_bimodality": (metrics.bimodality(p.spec[act]) if self.specialize and act.size else 0.0),
            "spec_mean": (float(p.spec[act].mean()) if self.specialize and act.size else 0.0),
            "n_hearths": float(self._strong_hearths().size) if self.building else 0.0,
            "culture_tech": (float(self.struct_tech[self._strong_hearths()].max())
                             if self.culture and self._strong_hearths().size else 0.0),
        }
        if self.tech_actions:                               # R153: how far culture has unlocked world-actions
            ta = self.tech_actions_test()
            snap["realized_tiers"] = float(ta.get("realized_tiers", 0))
            snap["locked_food_frac"] = float(ta.get("locked_food_frac", 0.0))
            snap["mean_edible_tiers"] = float(ta.get("mean_edible_tiers", 0.0))
        if self.depth_gates:                                # R171/R172: embodied ceiling gated on the GROWN tree
            max_tier, n_axes = self.diet_capability_ceiling()  # persisted so the climb is visible on disk (R172)
            snap["mean_edible_tiers"] = float(max_tier)
            snap["realized_axes"] = float(n_axes)
        if self.tech_capabilities:                          # R154: culture-gated physical capability axes
            tc = self.tech_capabilities_test()
            snap["realized_axes"] = float(tc.get("realized_axes", 0))
            snap["mean_axes"] = float(tc.get("mean_axes", 0.0))
            snap["mean_speed_cap"] = float(tc.get("mean_speed_cap", cfg.speed))
            snap["mean_reach"] = float(tc.get("mean_reach", cfg.eat_radius))
            snap["mean_realized_speed"] = float(tc.get("mean_realized_speed", 0.0))
        if self.cap_niches:                                 # R155: emergent capability specialization
            cs = self.cap_specialize_test()
            snap["profile_entropy"] = float(cs.get("profile_entropy", 0.0))
            snap["mean_keys"] = float(cs.get("mean_keys", 0.0))
            snap["balance"] = float(cs.get("balance", 0.0))
            snap["frac_keyed"] = float(cs.get("frac_keyed", 0.0))
            snap["keyed_food_frac"] = float(cs.get("keyed_food_frac", 0.0))
        return snap

    def caste_test(self) -> dict:
        """The R147 division-of-labour read-out: caste structure of the living population (bimodality of the
        heritable spec trait) PLUS a behavioural check that the castes act their role — do high-spec agents
        actually process more than low-spec ones? In situ; never feeds selection."""
        if not self.specialize:
            return {}
        p = self.pop
        act = p.active()
        if act.size < 20:
            return {}
        out = metrics.caste_metrics(p.spec[act])
        gate, _ = self._gate_decision(act)                  # recompute current process decisions
        out["proc_spec"] = float(p.spec[act][gate].mean()) if gate.any() else 0.0   # caste of processors
        out["harv_spec"] = float(p.spec[act][~gate].mean()) if (~gate).any() else 0.0
        out["n"] = int(act.size)
        return out

    def _danger(self, act):
        """Binary per-prey world-state: a predator within the prey's DIRECT detect range (R144)."""
        if self.pred is None:
            return np.zeros(act.size, dtype=int)
        return metrics.danger_state(self.pop.pos[act], self.pred.pos[self.pred.active()],
                                    self._pred_detect_range())

    def _signal_mi(self, act) -> float:
        """In-situ I(utterance ; danger-state) in bits — the live signal-informativeness read-out (R144)."""
        if not (self.signalling and self.has_predators) or act.size == 0:
            return 0.0
        return metrics.signal_world_mi(self.pop.utterance[act], self._danger(act), self.cfg.signal_bins)

    def signal_causal_test(self, rng: np.random.Generator | None = None) -> dict:
        """Causal LISTENING test: recompute every prey's action with the heard channel intact vs lesioned
        (silenced to 0), on the SAME brains and state. If receivers actually USE the signal, lesioning
        changes behaviour. The adaptive read-out: among prey hearing a loud alarm from a neighbour that is
        itself near a predator, do they accelerate AWAY from that (alarming) neighbour MORE when they can
        hear it than when deaf? +delta = the signal causally drives evasion. In situ; never feeds selection.
        """
        if not (self.signalling and self.has_predators):
            return {}
        p, cfg = self.pop, self.cfg
        act = p.active()
        if act.size < 2:
            return {}
        pos, vel = p.pos[act], p.vel[act]
        r, u, f = _body_frame(vel)
        fs = self._sense_food(pos, r, u, f, act)
        ns, ni, nprox = self._sense_neighbours(pos, r, u, f, cfg.sense_range)
        ps = self._sense_predators(pos, r, u, f)
        e = (p.energy[act] / cfg.e_repro).reshape(-1, 1)
        heard = self._heard(act, ni, nprox)

        def action(h):
            out = brain.forward(p.brains[act], self.spec, np.concatenate([fs, ns, ps, h, e], axis=1))
            return _act(out, r, u, f, vel, cfg.force, cfg.min_speed, cfg.speed)

        v_intact = action(heard)
        v_deaf = action(np.zeros_like(heard))
        daccel = float(np.linalg.norm(v_intact - v_deaf, axis=1).mean())
        if ni is None:
            return {"daccel": daccel, "flee_intact": 0.0, "flee_deaf": 0.0, "n_alarmed": 0}
        # subset: neighbour is near a predator (honest alarm) AND prey hears it loudly
        ndist = np.full(act.size, np.inf)
        if self.pred.n_alive:
            ndist, _ = cKDTree(self.pred.pos[self.pred.active()]).query(pos, k=1)
        neigh_danger = ndist[ni] < self._pred_detect_range()
        loud = (np.abs(heard[:, 0]) > 0.3) & (nprox > 0) & neigh_danger
        # flee AWAY from the alarming neighbour = move opposite the neighbour bearing
        ndir = pos[ni] - pos
        ndir = ndir / np.maximum(np.linalg.norm(ndir, axis=1, keepdims=True), 1e-9)
        def flee_away(v):
            sp = np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)
            return -((v / sp) * ndir).sum(1)              # +1 = straight away from neighbour
        if loud.sum() < 5:
            return {"daccel": daccel, "flee_intact": 0.0, "flee_deaf": 0.0, "n_alarmed": int(loud.sum())}
        return {
            "daccel": daccel,
            "flee_intact": float(flee_away(v_intact)[loud].mean()),
            "flee_deaf": float(flee_away(v_deaf)[loud].mean()),
            "n_alarmed": int(loud.sum()),
        }

    def _gate_decision(self, act: np.ndarray):
        """Recompute the active agents' brain outputs and return (process-gate bool, out). In situ."""
        cfg, p = self.cfg, self.pop
        pos, vel = p.pos[act], p.vel[act]
        r, u, f = _body_frame(vel)
        fs = _sense_kd(pos, r, u, f, self.food[self.food_ripe], cfg.sense_range)
        ns, ni, nprox = self._sense_neighbours(pos, r, u, f, cfg.sense_range)
        parts = [fs, ns]
        if self.has_predators:
            parts.append(self._sense_predators(pos, r, u, f))
        if self.signalling:
            parts.append(self._heard(act, ni, nprox))
        parts.append(_sense_kd(pos, r, u, f, self.food[~self.food_ripe], cfg.sense_range))
        if self.building:
            parts.append(self._sense_hearths(pos, r, u, f))
        parts.append((p.energy[act] / cfg.e_repro).reshape(-1, 1))
        out = brain.forward(p.brains[act], self.spec, np.concatenate(parts, axis=1))
        return out[:, self._proc_out] > 0.0, out

    def process_allocation_test(self) -> dict:
        """The response-threshold DIVISION-OF-LABOUR read-out (R146). For each living agent, recompute its
        process decision and its LOCAL ripe-food proximity (nearest edible mote). Returns:
          - frac_processing: the processor/harvester split at this instant (a spatial division of labour
            shows as a stable interior fraction, not 0 or 1).
          - cond_ripe: corr(process-decision, local ripe proximity). NEGATIVE = agents process when ripe
            food is SCARCE nearby and harvest when it is abundant — i.e. role is allocated by local need.
          - cond_raw: corr(process-decision, local raw proximity). POSITIVE = they process where there is
            raw food to ripen. Under a frozen genome both correlations sit near 0 (no task allocation).
        In situ; never feeds selection."""
        if not self.processing:
            return {}
        p, cfg = self.pop, self.cfg
        act = p.active()
        if act.size < 20:
            return {}
        gate, _ = self._gate_decision(act)
        ripe = self.food[self.food_ripe]
        raw = self.food[~self.food_ripe]

        def prox(food):
            if food.shape[0] == 0:
                return np.zeros(act.size)
            d, _ = cKDTree(food).query(p.pos[act], k=1)
            return np.where(d < cfg.sense_range, 1.0 - d / cfg.sense_range, 0.0)

        return {
            "frac_processing": float(gate.mean()),
            "cond_ripe": metrics.point_biserial(prox(ripe), gate),
            "cond_raw": metrics.point_biserial(prox(raw), gate),
            "n": int(act.size),
        }

    def niche_test(self) -> dict:
        """The R148 niche-construction read-out: are the self-built hearths CLUSTERED into settlements, do they
        OUTLIVE their builders (ecological inheritance), and is the population settled around them? In situ."""
        if not self.building:
            return {}
        p = self.pop
        act = p.active()
        if act.size < 20:
            return {}
        lifespan = (self._death_age_sum / self._death_count) if self._death_count else float(p.age[act].mean())
        age = self.step_count - self.struct_birth
        return metrics.niche_metrics(self.struct_pos, np.where(self.struct_alive, self.struct_strength, -1.0),
                                     age, p.pos[act], p.age[act], self.cfg.world.size,
                                     self.cfg.hearth_radius, self.cfg.hearth_min_strength, lifespan)

    def hearth_arrays(self):
        """(pos, strength) of the standing STRONG hearths — for rendering settlements as built structures."""
        strong = self._strong_hearths()
        return self.struct_pos[strong], self.struct_strength[strong]

    def render_arrays(self):
        """(pos, vel, color, food) of the living agents — prey + predators — for render3d.Renderer3D."""
        p, act = self.pop, self.pop.active()
        pos, vel, col = p.pos[act], p.vel[act], p.color[act]
        if self.pred is not None:
            pa = self.pred.active()
            pos = np.vstack([pos, self.pred.pos[pa]])
            vel = np.vstack([vel, self.pred.vel[pa]])
            col = np.vstack([col, self.pred.color[pa]])
        return pos, vel, col, self.food

    # --- persistence ---
    def save_checkpoint(self, path: str) -> None:
        st = self.pop.state()
        combo = {"rep": self.rep, "struct_rep": self.struct_rep} if self.combinatorial else {}
        if self.generative_tree:                             # R172: the GROWN open-ended tree must survive
            ts = self._tree.state()                          # process death, else resumed depth collapses to
            combo["tree_pa"] = ts["pa"]                      # a fresh seed-only tree (rep's deep nodes -> level 0)
            combo["tree_pb"] = ts["pb"]
            combo["tree_level"] = ts["level"]
            combo["tree_n"] = ts["n"]
        if self.culture_decay:                               # R157: the decaying memory backs the record
            combo["struct_memory"] = self.struct_memory
        if self.cap_niches:                                  # R155 niche labels (kept in sync only when on)
            combo["food_niche"] = self.food_niche
        np.savez_compressed(
            path,
            step=np.int64(self.step_count),
            **combo,
            food=self.food,
            food_type=self.food_type,
            food_tier=self.food_tier,
            food_ripe=self.food_ripe,
            ripe_age=self.ripe_age,
            food_proc=self.food_proc,
            struct_pos=self.struct_pos,
            struct_strength=self.struct_strength,
            struct_birth=self.struct_birth,
            struct_founder_gen=self.struct_founder_gen,
            struct_max_gen=self.struct_max_gen,
            struct_last_builder=self.struct_last_builder,
            struct_tech=self.struct_tech,
            struct_alive=self.struct_alive,
            evolve=np.bool_(self.evolve),
            rng=np.array(json.dumps(self.rng.bit_generator.state)),
            lin_keys=np.array(list(self.lineage_first_step.keys()), dtype=np.int64),
            lin_vals=np.array(list(self.lineage_first_step.values()), dtype=np.int64),
            **{f"pop__{k}": v for k, v in st.items()},
        )

    def load_checkpoint(self, path: str) -> None:
        d = np.load(path, allow_pickle=False)
        self.step_count = int(d["step"])
        self.food = d["food"]
        self.food_type = d["food_type"]
        self.food_tier = (d["food_tier"] if "food_tier" in d.files
                          else np.zeros(self.food.shape[0], dtype=np.int64))
        self.food_niche = (d["food_niche"] if "food_niche" in d.files
                           else np.full(self.food.shape[0], -1, dtype=np.int64))
        self.food_ripe = (d["food_ripe"] if "food_ripe" in d.files
                          else np.ones(self.food.shape[0], dtype=bool))
        self.ripe_age = (d["ripe_age"] if "ripe_age" in d.files
                         else np.zeros(self.food.shape[0], dtype=np.int32))
        self.food_proc = (d["food_proc"] if "food_proc" in d.files
                          else np.full(self.food.shape[0], -1, dtype=np.int64))
        if "struct_pos" in d.files:                          # hearths (R148); absent in pre-R148 checkpoints
            self.struct_pos = d["struct_pos"]
            self.struct_strength = d["struct_strength"]
            self.struct_birth = d["struct_birth"]
            self.struct_founder_gen = d["struct_founder_gen"]
            self.struct_max_gen = d["struct_max_gen"]
            self.struct_last_builder = (d["struct_last_builder"] if "struct_last_builder" in d.files
                                        else np.full(self.struct_pos.shape[0], -1, dtype=np.int64))
            self.struct_tech = (d["struct_tech"] if "struct_tech" in d.files
                                else np.zeros(self.struct_pos.shape[0]))
            self.struct_alive = d["struct_alive"]
        if self.combinatorial and "rep" in d.files:          # R150 repertoire pools
            self.rep = d["rep"]
            self.struct_rep = d["struct_rep"]
            if self.generative_tree and "tree_n" in d.files:  # R172: restore the grown open-ended tree IN PLACE
                self._tree.restore(d["tree_pa"], d["tree_pb"],  # (keeps the _tree_pa/_tree_pb/_tree_level binding)
                                   d["tree_level"], int(d["tree_n"]))
            if self.culture_decay:                           # R157: restore the decaying memory (record derives from it)
                self.struct_memory = (d["struct_memory"] if "struct_memory" in d.files
                                      else self.struct_rep.astype(np.float32) * self.cfg.memory_reinforce)
        self.evolve = bool(d["evolve"])
        self.rng.bit_generator.state = json.loads(str(d["rng"]))
        st = {k[len("pop__"):]: d[k] for k in d.files if k.startswith("pop__")}
        self.pop.load(st)
        self.lineage_first_step = {int(k): int(v) for k, v in zip(d["lin_keys"], d["lin_vals"])}
