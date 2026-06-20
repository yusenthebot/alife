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
        self.tech_actions = self.cfg.tech_actions
        if self.combinatorial and not self.culture:
            raise ValueError("combinatorial (R150 open-ended culture) requires culture=True")
        if self.tech_actions and not self.combinatorial:
            raise ValueError("tech_actions (R153 culture unlocks world-actions) requires combinatorial=True")
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
        if self.combinatorial:                               # R150: build the fixed tech tree + repertoire pools
            from . import combinatorial as cb
            K, ns = self.cfg.max_techniques, self.cfg.n_seed_tech
            self._tree_pa, self._tree_pb, self._tree_level = cb.build_tech_tree(K, ns)
            self.rep = np.zeros((self.cfg.capacity, K), dtype=bool)       # per-agent repertoire (World-owned)
            act = self.pop.active()                                       # founders are culturally NAIVE: empty
            seed_rep = np.zeros((act.size, K), dtype=bool)                # repertoire, a few discoveries each
            cb.discover_inplace(seed_rep, self._tree_pa, self._tree_pb, ns,
                                self.cfg.combo_prereqs, self.rng, self.cfg.innov_steps)
            self.rep[act] = seed_rep
            self.pop.tech[act] = cb.max_level_known(seed_rep, self._tree_level)
            if self.tech_actions:                            # R153: which deep node unlocks each locked food tier
                self._recipe_tech = cb.recipe_techniques(
                    self._tree_level, ns, self.cfg.n_food_tiers, self.cfg.recipe_level_step)
                self._tier_eat_count = np.zeros(self.cfg.n_food_tiers, dtype=np.int64)
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
        self.food_tier = self._food_tiers(self.food.shape[0])    # R153 recipe-locked tiers (all-zero when off)
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

    def _food_tiers(self, n: int) -> np.ndarray:
        """Recipe-tier label per food mote (R153). Off (or single tier) -> all tier 0, NO RNG draw (so
        tech_actions=False is byte-identical to R150/R151). On -> tier 0 with prob tier0_frac (the free,
        always-edible resource), else a uniformly random LOCKED tier in 1..n_food_tiers-1."""
        cfg = self.cfg
        if not self.tech_actions or cfg.n_food_tiers <= 1:
            return np.zeros(n, dtype=np.int64)
        tiers = np.zeros(n, dtype=np.int64)
        locked = self.rng.random(n) >= cfg.tier0_frac
        n_locked = int(locked.sum())
        if n_locked:
            tiers[locked] = self.rng.integers(1, cfg.n_food_tiers, size=n_locked)
        return tiers

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
            newvel = _act(out, r, u, f, vel, cfg.force, cfg.min_speed, cfg.speed)  # _act reads out[:,:3]
            p.vel[act] = newvel
            p.pos[act] = w.clamp(pos + newvel)
            emit = np.zeros(act.size)
            if self.signalling:                             # the evolved extra output IS the utterance
                p.utterance[act] = np.tanh(out[:, N_OUT])   # bounded [-1,1]; heard by neighbours next step
                emit = cfg.emit_cost * np.abs(p.utterance[act])  # honest-signalling cost -> silence default
            speed = np.linalg.norm(newvel, axis=1)
            p.energy[act] = np.minimum(p.energy[act] - (cfg.base_cost + cfg.move_cost * speed + emit),
                                       cfg.e_max)
            if self.building:                               # deposit/reinforce a persistent hearth (R148)
                self._build(act, out)
            elif self.processing:                           # ripen nearby raw food (the costly labour)
                self._process(act, out)
            p.age[act] += 1
        if self.building:                                   # hearths ripen nearby raw food, then decay
            self._ripen_hearths()
            self._decay_structures()
        self._eat()
        if self.processing:
            self._decay_ripe()
        if self.has_predators:
            self._step_predators()
        self._die()
        self._reproduce()
        self._regrow()
        self.step_count += 1

    def _keep_food(self, keep: np.ndarray) -> None:
        """Filter all per-mote food arrays by the same boolean mask (keeps ripeness state in sync)."""
        self.food = self.food[keep]
        self.food_type = self.food_type[keep]
        self.food_tier = self.food_tier[keep]
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

    def _eat(self) -> None:
        cfg, p = self.cfg, self.pop
        act = p.active()
        if act.size == 0 or self.food.shape[0] == 0:
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
            winners, eaten = _resolve(dist, idx, cfg.eat_radius)   # winners index into elig; eaten into fm
            if winners.size == 0:
                continue
            eaters = act[elig[winners]]
            base = np.full(eaters.size, cfg.food_value * (1.0 + cfg.tier_value_bonus * t))
            p.energy[eaters] += self._harvest_gain(eaters, base=base)
            if self.specialize:                              # wage to whoever ripened each eaten mote (trade)
                self._pay_processors(fm[eaten])
            keep[fm[eaten]] = False
            eaten_agent[elig[winners]] = True
            self._tier_eat_count[t] += int(eaten.size)
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
            if strong.size:                                  # oblique transmission via the built world (hearths)
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
            if strong.size:                                  # oblique transmission via the built world (hearths)
                d, idx = cKDTree(self.struct_pos[strong]).query(self.pop.pos[slots], k=1)
                in_range = d < cfg.hearth_radius
                if in_range.any():
                    rows = np.where(in_range)[0]
                    source[rows] |= self.struct_rep[strong][idx[rows]]   # learn the BEST record in reach
            child = cb.copy_with_fidelity(source, cfg.culture_fidelity, self.rng)
        else:
            child = np.zeros((slots.size, K), dtype=bool)    # asocial: no copying, reinvent from scratch
        cb.discover_inplace(child, self._tree_pa, self._tree_pb, cfg.n_seed_tech,
                            cfg.combo_prereqs, self.rng, cfg.innov_steps)
        self.rep[slots] = child
        self.pop.tech[slots] = cb.max_level_known(child, self._tree_level)

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
            if self.combinatorial:                           # the hearth ACCUMULATES the union of deposited
                np.bitwise_or.at(self.struct_rep, tgt, brep[reinforce])  # repertoires (a growing cultural store)
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
                if self.combinatorial:
                    self.struct_rep[slots] = brep[who]       # a new hearth opens with the founder's repertoire
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
            self.food = np.vstack([self.food, self._spawn_food(need)])
            self.food_type = np.concatenate([self.food_type, self._food_types(need)])
            self.food_tier = np.concatenate([self.food_tier, self._food_tiers(need)])
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
        self.evolve = bool(d["evolve"])
        self.rng.bit_generator.state = json.loads(str(d["rng"]))
        st = {k[len("pop__"):]: d[k] for k in d.files if k.startswith("pop__")}
        self.pop.load(st)
        self.lineage_first_step = {int(k): int(v) for k, v in zip(d["lin_keys"], d["lin_vals"])}
