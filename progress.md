# alife — progress

## Current state (Round 173 — 2026-06-21) — THE UNATTENDED MULTI-DAY CLIMB: the world you start once and leave running. A single idempotent daemon.tick() (the cron/systemd/supervisor entrypoint) resumes the on-disk world, climbs one segment, and refreshes a rolling LIVE PANEL — so "leave it running for days, it keeps developing" is now a real loop on the open-ended generative substrate (red-teamed CONFIRMED — genuine resume across 6 real PIDs, the dashboard is the FULL rolling history, irregular scheduler cadence still yields one monotone climb).

**R173 lands frontier (1)'s capstone: STAND UP THE ACTUAL UNATTENDED LOOP.** R169-R172 built persistence
and PROVED process death is invisible to development (bit-for-bit continuity, even on the generative
substrate). But the *driver* was still a verification script that hand-drove subprocesses for the proof.
R173 turns it into the real deliverable: a single `daemon.tick()` any external scheduler calls repeatedly
against ONE on-disk `state_dir`, which extends the world one segment and REGENERATES a rolling LIVE PANEL
from the WHOLE accumulated trajectory. You start it once and glance at the dashboard as it climbs. 禁止造假.

**The contribution (a thin resumable wrapper over the proven persistence primitive — no new sim, no new RNG).**
New `genesis/daemon.py`:
- `render_live_panel(traj, path, boundaries=)` — a PURE function of the accumulated trajectory dict (the
  rolling dashboard a tick refreshes): 5 climb curves (conn_depth/breadth/axes/diet/pop) + a glanceable
  LIVE-STATE text read-out. Reflects exactly the on-disk history, no hidden state.
- `tick(state_dir, cfg, seed, segment_steps)` — one unattended tick = `persist.run_segment` + regenerate
  the live panel; `tick_index` persisted in `state_dir/daemon.json` so a FRESH process knows which tick it
  is. Idempotent across process death — the cron/systemd/supervisor/cloud-cron entrypoint.

**HEADLINE — 6 REAL subprocess ticks at IRREGULAR cadence become ONE continuous developing world + a live
dashboard.** REAL-VERIFY (`scripts/run_genesis_r173.py` → `runs/r173_daemon/{panel.png,world.gif}`,
EYE-VERIFIED, ~10.7s): irregular plan `[60,40,70,50,60,40]` — tick 1 BOOTSTRAP, ticks 2-6 RESUME, each
`start_step == prior end_step` (60→100→170→220→280→320) across 6 genuinely separate PIDs, `tick_index` 1→6
read from on-disk `daemon.json`. On-disk: ONE strictly-monotone history step 0→320; conn_depth 3→9, breadth
130→1000, diet ceiling 1→4, axes→2, pop 1000. Live panel regenerated every tick (`panel_n_samples`
4→6→10→13→16→18 = the full accumulated history each time). The 3D render shows the restored DEEP (gold)
population alive over food, tree.n=1000, diet_ceiling=(4,2) — restored, not collapsed.

**RED-TEAM CONFIRMED (scoped to R173's value-add).** The continuity primitive itself was already proven
non-vacuous (R169 not-vacuous control + R172 load-bearing tree restore, both committed). R173's NEW claims
survive: (a) **genuine resume, not re-bootstrap** — the start_step chaining across 6 PIDs + tick_index from
disk; (b) **the live panel is the FULL rolling history, not the last segment** — `panel_n_samples` grows with
the trajectory (`test_daemon_live_panel_renders_from_full_trajectory`); (c) **scheduler cadence is
irrelevant** — an irregular plan still yields one strictly-monotone history of the exact summed length
(`test_daemon_irregular_tick_cadence_one_continuous_history`). 219 genesis tests (+3).

**HONEST CAVEAT (recorded, baked into the next rung):** with K=1000 the open-ended climb SATURATES within
tick 1 (everything plateaus by ~step 30), so ticks 2-6 demonstrate PERSISTENCE/MAINTENANCE of the developed
state across real process death rather than continued climbing. The unattended-loop mechanism + rolling
dashboard are fully real; SUSTAINED multi-tick climb (depth/breadth rising tick after tick) needs a larger
cap or slower innovation — that, plus wiring `daemon.tick` into the real supervisor/cron for actual days,
is R174.

## Current state (Round 172 — 2026-06-21) — PERSISTENCE ON THE OPEN-ENDED GENERATIVE SUBSTRATE: the grown tree survives process death.

**R172 lands the top-ranked post-R171 frontier (1): make the generative open-ended world PERSISTENT.** R169
made the world resumable, but only on the FIXED civ_config substrate (no generative tree) — so a resumed run
that used `generative_tree=True` would silently collapse: the grown tree's deep nodes were never checkpointed,
so on reload the deep techniques in each agent's `rep` mapped back to a fresh seed-only `GrowingTree` (level 0),
killing realized depth and the depth-gated body. R172 closes that hole: the GROWN tree itself now survives
process death, so the open-ended climb (depth + embodied diet ceiling + axes) persists across real restarts —
the literal "leave it running for days, it keeps developing" deliverable now works on the OPEN-ENDED substrate.

**The contribution (checkpoint the grown tree; no new physics, no new RNG, off-path byte-identical).**
- `GrowingTree.state()` / `restore()` (combinatorial.py): round-trip the grown tree losslessly. The (a,b)->id
  registry is NOT stored — it is rebuilt from the materialized parent pairs on restore, so an already-composed
  pair returns its original id and a genuinely new composition extends from `n`. `restore` copies IN PLACE
  (`pa[:]=…`) so a World that bound `_tree_pa/_tree_pb/_tree_level` to the tree's arrays keeps seeing the
  restored state. Raises on a saved-tree > capacity (cfg mismatch).
- `GenesisWorld.save/load_checkpoint`: persist `tree_pa/pb/level/n` when `generative_tree` is on; restore IN
  PLACE on load (keeps the array binding). depth_gates snapshot now also records the embodied diet ceiling +
  axes so the climb is visible on the on-disk trajectory.

**HEADLINE — on the GENERATIVE substrate, a resumed chain == an uninterrupted run, BIT FOR BIT.** REAL-VERIFY
(`scripts/run_genesis_r172.py` → `runs/r172_persist/{panel.png,world.gif}`, EYE-VERIFIED, ~8.5s):
**4 REAL subprocess restarts** (`subprocess.run` = genuine process death) × 80 steps on the generative +
depth_gates world: on-disk trajectory continuous (step 0→320), connected tech depth climbs 3→9, embodied diet
ceiling climbs 1→4, axes→2, population persistent at 1000. **Continuity proof:** uninterrupted run vs a chain
that suffers process death every segment is `max|diff|=0.000e+00`, bit_for_bit_identical=True across ALL signals
(depth/breadth/axes/edible/pop/diversity/max_gen). The 3D render shows the restored, developed population —
agents gold (deep realized culture) over green food motes, proving the tree was restored not collapsed.

**RED-TEAM CONFIRMED (load-bearing not-vacuous control — the restore CAUSES the continuity).** The obvious
attack is "bit-for-bit identity is trivial because the tree is reconstructable from rep anyway." Refuted by a
permanent test (`test_persist_generative_tree_restore_is_load_bearing`): a boundary chain that reloads the
checkpoint but then RESETS the tree to a fresh seed-only `GrowingTree` (the pre-R172 behavior) DIVERGES
(`continuity_max_abs_diff > 0`) — so the bit-for-bit continuity is caused by restoring the grown tree, not by
trivial reconstruction. Plus: the depth/diet trajectory genuinely CLIMBS in the window (not flat, so there is
real development to be continuous through), and `state()/restore()` round-trips losslessly with the registry
rebuilt from parents (unit test). 216 genesis tests (+3).

---

## Round 171 (2026-06-21) — OPEN-ENDED CULTURE NOW DRIVES THE BODY: depth gates. The generative grown tree (R170) was an abstract repertoire; R171 makes its open-endedness CAUSAL on EMBODIMENT — the diet tiers an agent can eat and the locomotion/reach axes it has unlocked are gated on its realized cultural DEPTH, so the embodied ceiling is open-ended too (red-teamed CONFIRMED — capped freezes the body even with a healthy pop; the freeze is the depth-CAP, not death)

**R171 lands the top-ranked post-R170 frontier (1): GATE EMBODIED ACTIONS ON THE GROWN TREE — close the
open-endedness→body loop.** R170's generative `combinatorial.GrowingTree` made the cultural REPERTOIRE
open-ended (depth climbs with the cap, freezes when capped) but nothing physical depended on how deep the
culture had grown — the fixed-node gates (tech_actions/tech_capabilities) designate SPECIFIC pre-built deep
nodes ahead of the run, which a generative tree (whose deep nodes don't exist until composed) cannot use. R171
adds `depth_gates`: embodied capability is gated on the agent's REALIZED cultural depth (`pop.tech` = its
deepest known technique level), which needs no pre-built node. So open-ended culture now CAUSALLY drives an
open-ended BODY. 禁止造假.

**The contribution (a gate mechanism over the existing dense rep; reuses the diet/capability config, no new
physics, no new RNG).** New `depth_gates` flag (requires `generative_tree=True`):
- food tier t≥1 is edible ONLY by an agent whose culture has reached level ≥ `recipe_level_step * t` (a deeper
  tier demands a strictly deeper culture; tier 0 is the free resource) — new `_eat_depth_gates` eat path;
- capability axis i unlocks at level ≥ `cap_level_step * (i+1)` (axis 0 = locomotion speed, 1 = harvest reach)
  — `_cap_speed`/`_cap_reach` grow a depth-gated branch;
- `GenesisWorld.diet_capability_ceiling()` = read-only read-out (max edible tier, n axes unlocked) over the
  living pop, bounded above by the grown tree's depth → freezes when capped, climbs when not;
- `depth_gates=False` is BYTE-IDENTICAL (food_tier all-zero, no extra RNG, eat/speed/reach paths unchanged);
  mutually exclusive with the fixed-node gates (it IS their generative replacement).

**HEADLINE — the embodied diet/capability CEILING tracks the cultural cap.** REAL-VERIFY
(`scripts/run_genesis_r171.py` → `runs/r171_depth/{panel.png,world.gif}`, EYE-VERIFIED, ~8s, 3 live full-stack
worlds ×320 steps): **uncapped (K=4000)** cultural depth climbs 4→11, the embodied diet ceiling climbs to the
TOP tier (4 of 4), both capability axes unlock, the population EATS across all 5 tiers (`_tier_eat_count` all
positive) and sits at capacity 1000. **capped (K=20):** the SAME machinery freezes — depth flat at 1, diet
ceiling 0, 0 axes, only tier-0 eaten. **null (innov_steps=0):** the tree never grows (n=n_seed), depth 0,
ceiling 0. The 3D render shows the developed uncapped population, agents violet→gold by culture depth = what
their bodies can do.

**RED-TEAM CONFIRMED (decisive control — freeze is the depth-CAP, not population death).** The capped/null pops
also crash (8-9), so the obvious attack is "ceiling 0 is just death." Refuted: a capped world with ALL food
free (`tier0_frac=1.0`, no starvation from locked tiers) keeps a HEALTHY pop (309) yet its depth/tree/diet
ceiling/axes stay frozen at 1/20/0/0, while the uncapped all-free world reaches 10/4000/4/2 — the CAP is the
ONLY difference, so the embodied freeze is the depth-cap. Plus the committed controls: cap-sweep monotone
(ceiling non-decreasing in K, strictly out-reaches the small cap), the load-bearing innov_steps=0 null (no
composition → no unlock even at K=4000), and `depth_gates=False` byte-identity. 213 genesis tests (+6).

**HONEST CAVEAT (baked in):** the diet/axes ceiling is the MAX over living agents, so it pins early once any one
agent reaches a depth — the load-bearing claim is the CAP control + the BROAD realized eating across all tiers,
not the single-agent max. depth_gates is the generative replacement for the fixed-node gates, mutually exclusive
with them by construction. Next rung: leave this embodied open-ended world running for days via the supervisor.

## Current state (Round 170 — 2026-06-21) — OPEN-ENDEDNESS MADE CAUSAL IN THE LIVE WORLD: the generative tech tree. The living civilization's culture is no longer explored on a FIXED pre-built tree (a frozen ceiling) — it GROWS the tree on demand from the population's real compositions, open-ended BY CONSTRUCTION, bounded only by the memory cap (red-teamed CONFIRMED — the freeze is the CAP not pop death; a no-composition null never grows)

**R170 lands the top-ranked post-R169 frontier (1): BREAK OUT — make open-endedness CAUSAL.** Across R164-R169
the genuinely-unbounded machinery (R164 `unbounded.TechSpace`, the phylorate rate laws, the tech-depth DAG)
lived in SEPARATE analytical/registry models; the LIVE world (genesis.py) still ran its culture on a FIXED
pre-enumerated tree (`combinatorial.build_tech_tree`, `max_techniques` columns) whose deepest level is a frozen
pre-set ceiling. R170 brings the open-endedness INTO the running civilization: the live world now grows its tech
tree from the population's actual compositions, so the cultural frontier is open-ended by construction in the
world you watch develop, not only in an offline model. 禁止造假.

**The contribution (a generative tree over the SAME dense rep — no representation rewrite, drops into the
existing combinatorial culture behind a flag).** New `combinatorial.GrowingTree` = the live-world analogue of
R164 `unbounded.TechSpace`, but over the World's dense boolean repertoire:
- starts with ONLY the `n_seed_tech` level-0 primitives materialized; the first time two KNOWN techniques are
  composed it MATERIALIZES a brand-new deeper node (id = next free column, level = 1+max(parent levels), parents
  = the pair) appended into the pre-allocated capacity-K arrays — so the dense rep width stays K while the
  realized tree is BUILT by the living culture.
- `pa/pb/level` are the SAME arrays the World binds as `_tree_*`, mutated in place as nodes are born, so every
  downstream reader (max_level_known, combinatorial_test, the phylogeny read-outs) works unchanged on the grown tree.
- the ONLY ceiling is the capacity `max_techniques` (the memory cap == `unbounded.TechSpace`'s `cap`): cap it
  small and the frontier FREEZES once full; raise it and breadth+depth keep climbing with run length.
- wired behind `generative_tree` (default False = the fixed-tree path, BYTE-IDENTICAL). The fixed-deep-node gates
  (tech_actions/tech_capabilities, which designate recipe/capability nodes ahead of the run) are not yet wired
  onto the grown tree → combining them raises ValueError (dynamic recipe designation = the next rung).

**HEADLINE — the live population's cultural frontier is bounded ONLY by the cap; capping freezes it.** REAL-VERIFY
(`scripts/run_genesis_r170.py` → `runs/r170_generative/{panel.png,world.gif}`, EYE-VERIFIED, ~7s):
- 3 live full-stack worlds × 320 steps. **generative big-cap (K=4000):** breadth (distinct techniques known by the
  living pop) climbs **145→3962**, frontier depth **5→9**, the tree GREW **6→4000 nodes** from real compositions.
  **generative capped (K=30):** the SAME machinery FREEZES — breadth flat at **30**, depth flat at **2**.
  **fixed pre-built tree (K=4000):** breadth 16→185, depth 1→8 (a hard pre-set ceiling).
- The 3D render shows the developed generative civilization alive, agents violet→gold by culture depth.

**RED-TEAM CONFIRMED (inline, decisive + construction-guaranteed).**
- **The freeze is the CAP, not population death:** a cap sweep gives breadth that tracks the cap EXACTLY —
  K=30→breadth 30 (pop=719, healthy), K=120→breadth 120 (pop=1000), K=4000→breadth 3668/depth 10. Monotone in K;
  the capacity is the binding constraint, not a dying population.
- **Load-bearing null:** generative ON but `innov_steps=0` (no composition) → breadth stays at **6** (=n_seed),
  depth 0, the tree never grows. So the climb is genuinely driven by the population's real compositions, not seeding.
- `generative_tree=False` byte-identical to the fixed-tree path (unit-tested); GrowingTree unit-tested (materialize
  on demand, canonical-pair dedup, cap freeze, depth grows only when uncapped). 207 genesis tests (+5).

**HONEST CAVEAT (baked in):** in a SHORT run (320 steps) the FIXED pre-built tree's depth (8) was COMPARABLE to the
generative tree's (9-10) — the fixed tree also has pre-built deep nodes to discover, so "generative out-depths
fixed in 320 steps" is NOT the claim. The decisive, construction-guaranteed claim is the CAP control: the
generative frontier is bounded ONLY by capacity (breadth tracks the cap exactly; depth scales 2/3/10 with K=30/120/
4000), whereas the fixed tree has a HARD pre-set ceiling it can never pass. Also: the generative tree does not yet
GATE physical actions (recipe/capability gates need pre-built deep nodes) — that is the next rung.

## Current state (Round 169 — 2026-06-21) — GENESIS PERSISTENT, RESUMABLE LONG RUN: the world you leave running. GENESIS is now a process that SURVIVES PROCESS DEATH and resumes the SAME civilization (the literal CEO "just by running locally or in the cloud" deliverable), proven by BIT-FOR-BIT trajectory continuity across genuine restarts (red-teamed CONFIRMED — load-bearing negative controls break continuity)

**R169 lands the top-ranked post-R168 frontier (1): a PERSISTENT, RESUMABLE long run.** R168 proved the
full-stack civilization develops in one ~30s run and that a single checkpoint reload preserves population/
max_gen at the reload instant. R169 turns GENESIS into an actual persistent PROCESS: it runs in SEGMENTS,
checkpointing each segment to disk and APPENDING the development trajectory to a durable on-disk log, so a
brand-new process resumes from the latest checkpoint and CONTINUES the same civilization — across sessions,
machines, days. The CEO can leave it running, kill it, restart it, and it keeps climbing the SAME ladder
instead of starting over. 禁止造假.

**The contribution (a thin persistence layer + a driver; reuses R168 civdev signals + the committed checkpoint
API, no new sim mechanism, no new RNG).** New `alife/genesis/persist.py`:
- **`run_segment(state_dir, cfg, seed, segment_steps)`** — the persistent driver primitive: one call loads the
  latest on-disk checkpoint + rolling trajectory (or bootstraps fresh), advances one segment, appends the new
  development samples to the on-disk trajectory, rewrites the checkpoint. This is what a cron / supervisor / a
  fresh `python` invocation calls each tick to keep the world developing unattended.
- **`continuous_trajectory` / `chained_trajectory`** — the matched pair the continuity proof compares.
  `chained_trajectory` destroys and rebuilds the world object from a disk checkpoint at EVERY segment boundary
  (a simulated process death); `continuous_trajectory` runs the same total length uninterrupted.
- **`continuity_max_abs_diff`** — max |difference| across every development signal (NaN-vs-NaN counts as equal).

**HEADLINE — process death is INVISIBLE to the civilization's development.** REAL-VERIFY
(`scripts/run_genesis_persist.py` → `runs/r169_persist/{panel.png,world.gif}`, EYE-VERIFIED, ~32s):
- **6 REAL subprocess restarts** (distinct PIDs, each a genuine separate `python` process that loads disk state
  and continues): connected tech depth climbs **0→13**, society breadth **6→598**, capability axes **→2**, edible
  diet **→3.85** ACROSS the restarts; the on-disk trajectory is one strictly-advancing history **step 0→1200**
  (`strictly-advancing-across-restarts=True`). If each subprocess had started fresh, conn_depth would reset to ~8
  every segment; instead it monotonically climbs 8→10→11→12→13 — the proof the world RESUMES, not restarts.
- **THE FALSIFIABLE CONTINUITY PROOF:** a resumed chain (process death every segment) vs one uninterrupted run of
  the same length is **BIT-FOR-BIT IDENTICAL — max|diff| = 0.000e+00** across all signals (panel bottom-right: the
  two curves are exactly coincident). If resume were lossy (any stepped state not checkpointed) or non-deterministic
  (any RNG not restored), the chained trajectory would diverge; it does not.
- **The GIF** is the watchable payoff: the developed population loaded from the FINAL checkpoint renders entirely
  GOLD (full physical capability unlocked by deep culture) — the civilization that grew across 6 restarts, alive
  and watchable. 201 genesis tests (+2: continuity bit-for-bit; run_segment extends-on-disk monotonically).

**RED-TEAM (mandatory; refutation-first; verdict CONFIRMED — the continuity proof is not vacuous).** The obvious
attack: "continuous == chained trivially because a fresh `GenesisWorld(cfg, seed)` reconstructs the same world
without the checkpoint even mattering." REFUTED by two load-bearing NEGATIVE CONTROLS that make checkpoint reload
the ONLY difference: (A) at each boundary build a fresh world but DO NOT load the checkpoint → the trajectory
diverges (step resets, breadth collapses to the fresh-start value); (B) load a checkpoint from a DIFFERENT seed
(999) at each boundary → max|diff| > 0. So the bit-for-bit continuity is genuinely CAUSED by lossless checkpoint
reload, not by the world being reconstructable from the seed alone. Both controls are committed as a PERMANENT
unit test (`test_persist_continuity_proof_is_not_vacuous`), so the proof can never silently become vacuous.
A genuine result: GENESIS is now a persistable, resumable process — the CEO's "just by running locally or in the
cloud, freely develops toward a civilization" is a concrete, restart-proof artifact. Next leap in `## Frontier / next`.

## Current state (Round 168 — 2026-06-21) — GENESIS FULL-STACK LIVING CIVILIZATION: run the WHOLE world at once, RENDER it, WATCH it develop. The first time every separately-validated R148-R167 mechanism runs together as ONE persistent watchable world (red-teamed CONFIRMED-WITH-CAVEAT, 3 fresh seeds + bit-for-bit metric recompute)

**R168 is a deliberate LEAP BACK FROM ABSTRACTION.** R148-R167 validated each civilization mechanism in
ISOLATION (niche construction / processing / cumulative combinatorial culture / tech-gated diet tiers /
culture-gated capabilities / demes & traditions / the structural depth of the tech DAG), and the R160-R167
arc then drifted into ever-finer analysis of those mechanisms on STANDALONE REGISTRY TOYS (rate laws, DAG
closure, Mantel tests). The CEO's actual deliverable — "a world that, just by running, freely develops toward
a civilization" — was never assembled or rendered. R168 does exactly that: turns the WHOLE stack ON together
in one persistent `GenesisWorld` and renders it developing. 禁止造假.**

**The contribution (one small shared module + a driver; reuses validated mechanisms, no new physics).** New
`alife/genesis/civdev.py`:
- **`civ_config`** — the canonical full-stack regime (building/processing + combinatorial culture +
  tech-gated diet tiers + culture-gated physical capabilities), factored out as the ONE source of truth the
  unit test and driver share. `learn=False` turns it into the asocial control.
- **`develop_trajectory`** — a READ-ONLY observer over `world.step()` + `snapshot()` + the society repertoire
  (no new RNG, no state change) logging the civilization-development signals the abstract arc could not see
  together: connected tech depth (R167) + closure + breadth, AND the EMBODIED signals — realized physical
  capability axes, mean edible diet tiers, population, lineage diversity, descent depth.
- **`develop_vs_control`** (full vs asocial null) and **`capability_color`** (3D agents coloured violet→gold
  by realized culture depth, so deep-culture agents emerge visibly in the render).

**HEADLINE — the civilization DEVELOPS just by running, and it is WATCHABLE.** REAL-VERIFY
(`scripts/run_genesis_civ.py 1500 800` → `runs/r168_civ/{civ.gif,panel.png,checkpoint.npz}`, EYE-VERIFIED,
~30s): the **panel** shows connected tech depth climbing 0→14 as a cumulative STAIRCASE (each rung when a
prereq chain completes), both physical capability axes unlocking ~step 150, the edible diet broadening 1→3.86
of 4 tiers, and population persistent at capacity with `resume_ok=True`. The **3D GIF** is the payoff: agents
start VIOLET (base phenotype, no culture) and the whole population turns GOLD as accumulated culture unlocks
their physical capabilities — the civilization developing, watchable with the eyes. The **asocial control**
(`learn=False`, same world same physics) stays flat: connected depth 0, 0 capability axes, eats tier-0 food
only. **Persistence proven**: checkpoint saved mid-run, reloaded into a fresh world, continuity confirmed
(the CEO's "just by running locally or in the cloud" requirement). 199 genesis tests (+3).

**RED-TEAM (mandatory; refutation-first; verdict CONFIRMED-WITH-CAVEAT — independent agent).** (1) SEED
ROBUST: 3 fresh seeds (5,6,7 @600 steps) all show full conn_depth 9-11 & axes=2 & diet ~3.5-3.8 vs control
conn_depth 0 & axes 0 & tier-0-only & population collapse (89-98). (2) METRIC SOUND: an independent numpy
recompute of the longest mutually-known prereq chain = 11, matching `techdepth.connected_depth` bit-for-bit;
conn_depth ≤ nominal max known level ≤ tree max. (3) DETERMINISTIC observer (byte-identical across runs).
**HONEST CAVEAT (baked into the docstring): the asocial control's floor is STRUCTURAL at the SHARED
`innov_steps=1`** — an agent born with an empty repertoire makes one discovery (a seed), and a level-1
technique needs TWO prerequisites held at once, which one lifetime's innovation cannot reach. It is NOT that
innovation is switched off: the SAME asocial world with a generous per-lifetime budget DOES develop
(`innov_steps=30` → connected depth ~8, both axes). So the load-bearing claim is precisely "**at a MATCHED
per-lifetime innovation budget, cumulative depth requires social TRANSMISSION**" (Tomasello's ratchet:
generation N+1 must start where N left off) — fair because both arms share `civ_config`'s `innov_steps=1`,
NOT "asocial agents cannot innovate at all." A genuine result: the integrated, embodied, watchable living
civilization the whole staged ladder was building toward. Next leap in `## Frontier / next`.

## Current state (Round 167 — 2026-06-21) — GENESIS TECH DEPTH: cumulative culture is a CONNECTED dependency DAG, not a broad scatter. The R160-R166 arc measured culture by BREADTH/RATE; R167 measures its STRUCTURE and finds breadth/nominal-depth MISLEAD (red-teamed CONFIRMED-WITH-CAVEAT, 3 fresh seeds + saturation control destroyed)

**R167 changes the AXIS, not the increment.** Six rounds (R160-R166) measured the cumulative-culture repertoire
by BREADTH (`pop_distinct`) and RATE (`dN/dt`). But breadth is not what makes culture *cumulative* — a pile of
independent tricks is broad and shallow. The structural signature of cumulative culture is that technology STANDS
ON technology: each thing known because the things it depends on are also known. New `alife/genesis/techdepth.py`
measures that on the LIVE combinatorial GenesisWorld:
- **`closure_fraction`** — of the known non-seed techniques, the fraction whose BOTH prerequisites are also known
  (the local "standing on known shoulders" rate).
- **`connected_depth`** — the longest chain of consecutive MUTUALLY-KNOWN prerequisites (the realized cumulative
  ladder), contrast the NOMINAL `max_level` (deepest tree level of any known technique, chain held or not).
- **`realized_edges`** / **`society_repertoire`** / **`depth_trajectory`** — the DAG + read-only live driver.

**HEADLINE — the STRUCTURE inverts the breadth/nominal verdict (combinatorial vs the additive null, `combo_prereqs`
the ONLY change, same tree).** REAL-VERIFY (`scripts/run_genesis_techdepth.py 500` → `runs/r167_techdepth/panel.png`
EYE-VERIFIED, 102s, max_techniques=20000 so the additive scatter stays a sparse SUBSET): the ADDITIVE NULL is
~12× BROADER (breadth ~7700 vs ~650) and reaches a ~3× HIGHER nominal tree level (max_level ~32 vs ~11) — by those
metrics it looks far more advanced. But its realized DAG is DISCONNECTED: closure collapses to ~0.13-0.15 (87% of
its known techniques lack their foundations) and connected_depth collapses to ~5-6. The COMBINATORIAL repertoire is
a prereq-CLOSED, deep CONNECTED ladder: closure ~1.0, connected_depth == nominal max_level. So cumulative culture is
structurally deep-and-CONNECTED, not broad — and breadth / nominal max_level actively MISLEAD.

**RED-TEAM (mandatory; refutation-first; verdict CONFIRMED-WITH-CAVEAT — independent agent).** (1) FRESH seeds 2,3,4:
combo closure=1.0 & connected==max_level every seed; additive 8-20× broader, 3× higher nominal level, yet closure
0.10-0.16 & connected collapsed — inversion holds 3/3. (2) SATURATION CONFOUND DESTROYED (the key attack): additive
breadth is only 32-38% of the 20k tree (not near saturation); DOUBLING the tree to 40000 drops additive closure
FURTHER (0.03-0.04) and connected_depth to 2-3 — the opposite of a saturation artifact; and at MATCHED breadth
(additive's closure when its breadth first reaches combo's final ~650) closure is ~0.000. The gap is not a breadth or
tree-size artifact. (3) METRIC CORRECTNESS: an independent numpy recompute matches techdepth bit-for-bit (closure
1.000/0.135, connected 11/6). **HONEST CAVEAT (baked into the docstring): combinatorial UNION closure ~1.0 is
effectively guaranteed BY CONSTRUCTION at this population scale — any of 2000 agents holding a prereq counts as known,
so the union is pinned at 1.0; the genuinely sub-1 measured quantity is the PER-AGENT closure (falls to ~0.51 at
fidelity 0.70). The load-bearing contrast is the ADDITIVE null's ~0.1, which holds regardless.** A genuine result: the
first STRUCTURAL / dependency-graph view of the living civilization's technology, dissociating cumulative depth from
mere breadth. 196 genesis tests (+4).

## Current state (Round 166 — 2026-06-21) — GENESIS LIVE PHYLORATE: the innovation RATE law EMERGES from the live economy. R165's autocatalytic effort E(N)∝N was POSITED; here it is shown to emerge endogenously in the real evolved-neural GenesisWorld (robust POSITIVE, red-teamed CONFIRMED 4 fresh seeds)

**R166 RECONNECTS the abstract analysis arc (R160-R165) back to the LIVE GenesisWorld — the CEO's actual
target.** R165 measured the rate law on a standalone registry model (`phylorate.py`) and its sharpest red-team
caveat was that "technology begets technology" (E(N) ∝ N) was an ASSUMED effort law, not derived. R166 closes
that caveat by taking the rate law to the real population of evolved-neural agents that sense / metabolise /
reproduce / die, and showing the autocatalytic effort EMERGES from the world's own energy economy. 禁止造假.**

**The contribution (a thin live driver + one pure metric; reuses R165's rate tools UNCHANGED).** New
`alife/genesis/livephylorate.py`:
- **`step_trajectory(world, steps)`** drives a real combinatorial `GenesisWorld` and emits a trajectory dict
  `{step, n_distinct, new, active}` in EXACTLY the shape `phylorate.rate_vs_size` / `phylorate.acceleration`
  consume — so R165's abstract rate-law instruments apply to the LIVE economy with no change. Read-only on the
  world (calls `world.step()` + the existing `combinatorial_test()` read-out only; no new sim mechanism, no
  extra RNG).
- **`rate_slope(out)`** = slope of the binned dN/dt-vs-N curve = the live accelerating-or-not discriminator.
- The endogenous loop is pre-existing machinery never built for this: a newborn makes `innov_steps` combinatorial
  discoveries when born (so per-step effort ∝ newborns ∝ population), and tech PAYS energy
  (`_harvest_gain`: gain × (1 + tech_gain·tech), genesis.py:835), so repertoire → energy → population → effort →
  repertoire is an ENDOGENOUS autocatalysis. 3 new tests (192 genesis green): rate_slope sign on synthetic
  rising/flat trajectories; step_trajectory shape + non-decreasing N + determinism; the economy>control smoke.

**HEADLINE (POSITIVE, red-teamed CONFIRMED 4 fresh seeds). In the LIVE evolved-neural GenesisWorld the per-step
innovation rate dN/dt RISES with the accumulated repertoire N (super-linear) BECAUSE mastery pays energy —
deeper repertoire feeds more agents → more newborns → more combinatorial innovation attempts. The DECISIVE
CONTROL tech_gain=0 (mastery stops paying) runs the SAME discovery machinery on the SAME tech tree but the
population can no longer grow with the repertoire: the rate flattens and the realized repertoire saturates
several-fold lower.** REAL-VERIFY numbers (1200 steps, capacity 9000, max_techniques 8000, n0 900, size 100,
2 seeds): ECONOMY (tech_gain 0.35) final repertoire 960 / 1937, workforce → capacity 9000, rate_slope
+1.08 / +1.35 per kN; CONTROL (tech_gain 0) repertoire 235 / 397, workforce ~1726-2096, rate_slope -0.44 / +0.31.

**REAL-VERIFY (`scripts/run_genesis_livephylorate.py 1200` → `runs/r166_livephylorate/panel.png` EYE-VERIFIED,
122s): (A) red ECONOMY rate-vs-N curves rise (~0.5 → 1.3) and sit above the gray CONTROL which stays low and
flat — the matched-N separation visible directly; (B) ECONOMY cumulative repertoire climbs far above the
decoupled control; (C) ECONOMY workforce grows to capacity while CONTROL stays stuck low; (D) rate_slope bars
ECONOMY positive vs CONTROL near-zero/negative.**

**RED-TEAM (mandatory; refutation-first; verdict CONFIRMED — independent agent, 4 FRESH seeds 2-5).** (1)
ECONOMY's final repertoire is **3.3-6.9× larger** and its workforce **3.6-4.8× larger** than CONTROL on **6/6
seeds**; ECONOMY slope more positive every seed. (2) **The load-bearing check — MATCHED N:** over the
OVERLAPPING N range, ECONOMY's dN/dt rises (~0.29 → ~1.0) and is **~2-3× the CONTROL's (flat ~0.24-0.35) AT
EQUAL N, with the gap WIDENING** — so the acceleration is genuine endogenous effort, NOT the artefact "more
agents trivially make more births". (3) **RNG isolation:** `tech_gain` enters at exactly one place
(genesis.py:835 harvest multiplier), absent from the combinatorial discovery path → both regimes share
byte-identical discovery machinery. **SHARPEST HONEST CAVEAT (baked into the docstring):** `rate_slope`'s SIGN
is the noisiest read — the CONTROL slope flips between seeds (-0.92 .. +0.48/kN), so the robust contrast is
"ECONOMY slope > CONTROL slope" + the matched-N curve + the several-fold repertoire/workforce gap, NOT "CONTROL
is strictly flat". The combinatorial adjacent possible contributes a weak intrinsic rate rise; the energy
ECONOMY amplifies it several-fold and is what drives the large repertoire. **A genuine result: the "technology
begets technology" effort law R165 had to posit is shown to EMERGE from the live economy, and is causally tied
to the tech→energy coupling by the decisive tech_gain=0 control. Reconnects 6 rounds of abstract rate analysis
to the live world.**

## Current state (Round 165 — 2026-06-20) — GENESIS PHYLORATE: the RATE law of cumulative innovation. Autocatalytic recombination on the OPEN combinatorial space gives SUPER-LINEAR (exponential) innovation; the decisive cap-control proves it is the OPEN adjacent possible, not the effort multiplier (robust POSITIVE, red-teamed CONFIRMED a/b/c/d over 4 seeds)

**R165 measures the RATE of innovation on R164's unbounded space (frontier option 1: phylorate / accelerating
dynamics).** R164 showed BREADTH grows linearly under a fixed-effort regime; R165 asks the Arthur/Kauffman
question — when each new technique becomes a building block AND effort tracks the accumulated repertoire, does
innovation ACCELERATE? New `alife/genesis/phylorate.py` runs four regimes on `unbounded.TechSpace`, each with a
distinct rate signature in the dN/dt-vs-N plane:
- **additive null** (independent invention from a FIXED pool) → SATURATES, dN/dt falls to 0 (DECELERATING; accel
  −0.12). The structureless null.
- **fixed-effort combinatorial** (R164 regime, constant E=base) → LINEAR, dN/dt ~ const (accel ~0.001).
- **autocatalytic + OPEN** (E(N)=max(base, alpha·N)) → SUPER-LINEAR / EXPONENTIAL: dN/dt ∝ N rises with N (accel
  +465; per-step multiplier N[t]/N[t−1]=1.4996 ≈ 1+alpha, R²=1.0; reaches N~55k in 22 steps).
- **autocatalytic + CAPPED** (DECISIVE CONTROL) — IDENTICAL alpha·N effort but capped at K: once full, collision
  fraction → 1.0, `new` → 0, rate COLLAPSES despite effort pinned at alpha·K. So sustained super-linearity is the
  OPEN adjacent possible, NOT the effort multiplier alone (the R164 cap=None-vs-cap=K control, now on the RATE).
- **Non-tautological discovered content:** on the open space the collision fraction → ~1e-4 as N grows (recomputed
  from the raw registry: 0.40 → 0.0001), because the distinct pair-space grows as N² while discoveries grow as N —
  the adjacent possible stays FED faster than it is consumed, so autocatalysis is sustained, not self-throttling.
- REAL-VERIFY: `scripts/run_genesis_phylorate.py` → runs/r165_phylorate/panel.png EYE-VERIFIED (crimson autocat+OPEN
  rockets up the log-y; rate-vs-N rises steeply; collision orange spikes to 1 while open stays ~0; accel bars crimson
  huge-positive vs orange negative). Red-team CONFIRMED a/b/c/d (independent agent, 4 seeds, raw-registry recompute,
  max diff 0.0). **HONEST CAVEAT (baked into docstring):** E(N)∝N is a MODELLING ASSUMPTION, not emergent — the
  genuinely discovered part is the narrower "open space doesn't self-throttle". It is EXPONENTIAL, not a fixed power
  law (`growth_exponent` rises with the fit window; read only as ">1 = super-linear"). 189 genesis tests (+7).

## Previous state (Round 164 — 2026-06-20) — GENESIS GENUINELY UNBOUNDED generative tech space: frontier complexity climbs with NO ceiling (open-ended by construction), vs the identical-dynamics fixed-cap tree which plateaus (robust POSITIVE, red-teamed CONFIRMED a/b/c)

**R164 lifts R150's fixed `max_techniques` ceiling — the genuine open-endedness rung (frontier option 1).
R150's combinatorial culture explored a tree PRE-BUILT to a fixed size, so frontier depth ceilinged at the
cap. R164 removes the cap: a technique IS the lazily-materialized COMPOSITION of two known parents (registry
`{pair -> id}`, nothing pre-allocated), so the reachable space is the infinite closure of the seeds under
pairing. New `alife/genesis/unbounded.py` — `TechSpace` (combine materializes a fresh id with level
1+max(parents); `cap` recovers the R150 regime by refusing new ids once full) + `run_population` (agents
compose two random knowns each step, then transmit a neighbour's repertoire with fidelity) + `chain_len`
(longest ancestral chain, proves the cumulative-descent invariant) + `ladder_arrays`. 8 new tests (182
genesis green). Pure numpy/registry — no sim/GL, <100 MB. 禁止造假.**

**HEADLINE (POSITIVE, red-teamed CONFIRMED a/b/c to 4000 steps over 2 seeds).**
- **(a) No ceiling.** Frontier depth keeps climbing with NO asymptote (final-third gain stays strictly
  positive at every horizon: depth 17→23→26→27→30 at steps 200/500/1000/2000/4000); BREADTH grows exactly
  linearly (~n_agents=40 distinct/step, 159,858 techniques at 4000 steps). At 600 steps: depth 20-21,
  breadth ~24k.
- **(b) Decisive control (cap=None vs cap=K, identical dynamics/seed).** Capped(K=100) FREEZES at breadth
  100 / depth 4-5 the moment its registry fills (the R150 ceiling); uncapped climbs to breadth ~24k /
  depth ~21 on the same seed. Not a tautology: the load-bearing empirical content is that lifting the cap
  keeps producing genuinely DEEPER compositions (depth, not just breadth, rises), not re-derivation of a
  shallow set.
- **(c) Depth is LITERAL cumulative-descent depth.** The invariant `chain_len(k)==level(k)` holds for every
  materialized technique — a level-L technique descends through L genuine compositions to the seeds.
  `chain_len` reads only `parents` (never `levels`), so it's an independent recomputation; corrupting a
  stored level makes them diverge → the invariant is discriminating, not vacuous. Ties R164's open-ended
  climb back to the R160-R163 descent-structure rung.

**THE SHARPEST HONEST CAVEAT (red-team).** Realized depth is genuinely unbounded (no asymptote through
4000 steps) but climbs ~LOGARITHMICALLY — empirically depth ≈ 2.5·ln(breadth) ≈ 2.5·ln(t), far below the
theoretical linear REACHABLE envelope (deepest reachable level = t after t rounds), because random
repertoire-pairing rarely chains deepest-with-deepest. So BREADTH is the clean linear unbounded metric;
depth is unbounded-but-strongly-DECELERATING. "Without bound" yes; "un-slowing rate" no. Baked into the
`unbounded.py` docstring. VERIFY: `scripts/run.sh scripts/run_genesis_unbounded.py 600` →
`runs/r164_unbounded/panel.png` (EYE-VERIFIED: crimson unbounded depth staircase to ~21 vs gray capped
frozen at ~4; breadth linear to ~24k vs capped flatline at 100; temporal ladder deeper=later Spearman
0.70; final-third depth gain positive both seeds vs capped zero).

## Current state (Round 163 — 2026-06-20) — GENESIS TEMPORAL phylogeny: combinatorial culture RECOVERS the time-ladder of cumulative descent; the additive null scrambles it; asocial never climbs (robust POSITIVE, red-teamed)

**R163 took the descent-recovery work from SPACE to TIME. R160-R162 reconstructed a SPATIAL phylogeny (demes as
taxa; the cladogram of traditions, ground-truth-validated: VERTICAL transmission recovers the birth genealogy,
HORIZONTAL does not). R163 reconstructs the TEMPORAL phylogeny — the time-ladder of cumulative descent: log when
each technique FIRST appears in the population over a long run, and ask whether that history recovers the
generative tech tree. The answer is a clean POSITIVE, red-teamed CONFIRMED. 禁止造假.**

**The contribution (a passive instrument + a pure metric; NO new sim mechanism → byte-identical when off).**
- **`track_tech_history` (default False)** — a passive observer that stamps the world step at which each technique
  first appears in any living agent's repertoire (`_update_tech_history`: reads `self.rep` only, consumes NO RNG,
  mutates NO sim state → byte-identical to off, verified by `array_equal` on pos AND rep). One int array of length
  `max_techniques` (analysis-only, bounded runs — like the R161 genealogy log).
- **`phylogeny.temporal_ladder_signal`** (pure, unit-tested) — given the first-appearance times + the tree
  (prereqs `pa`/`pb`, `level`), computes two tree-signal statistics vs a label-permutation null over the techniques
  that appeared: **precedence_frac** (fraction of appeared non-seed techniques that appear at/after BOTH their
  prereqs — the combinatorial mechanism forces this to 1.0, the additive null breaks it) and **level_time_corr**
  (Spearman of tree depth vs first-appearance time — deep techniques appear late; high = the history recovers the
  depth ladder). `_spearman` uses average-rank `rankdata` (matches scipy `spearmanr` to 1e-9 under heavy ties).
- **`World.temporal_phylogeny_test`** wraps the signal + the open-ended complexity snapshot (`max_level`,
  `pop_distinct`). Requires `track_tech_history`. 6 new tests (174 genesis green): perfect-ladder → corr 1.0/prec
  1.0/sig; scrambled → no signal; requires-combinatorial; byte-identical-off + logs appearances; the headline
  combinatorial-recovers-not-additive smoke; off-empty.

**HEADLINE (POSITIVE, robust). On the combinatorial tech-tree substrate, the population's first-appearance history
RECOVERS the generative tree's time-ladder of cumulative descent: precedence_frac = 1.000 (a technique never
appears before BOTH its prerequisites) and level<->time Spearman corr 0.94 (p~0 vs a label-permutation null ~0),
2/2 seeds. The ADDITIVE null (same tree, same machinery, prereq gate OFF) reaches the techniques in SCRAMBLED order
(precedence 0.35 ≈ the 1/3 chance level, corr ~0). The ASOCIAL null (no transmission) never climbs (max_level 0,
only the 8 seed primitives). The frontier depth climbs 0→9 and breadth 8→~312 under combinatorial social culture
vs a flat asocial floor.** The temporal analogue of R160-R162's spatial phylogeny, and a genuine cumulative-descent
(open-endedness) measurement: the population's HISTORY, not just its current state, carries a reconstructable
phylogenetic signal.

**THE SHARPEST POINT (honest, and the reason the instrument matters). The additive null does NOT stay shallow — it
reaches the WHOLE pool (max_level 20 / distinct 1500, the cap) FASTER than combinatorial, because with no prereq
gate it samples the entire tech space uniformly. So depth/breadth MAGNITUDE alone CANNOT distinguish genuine
cumulative descent from unstructured accumulation — only the temporal ORDER (precedence + depth-time correlation)
can. Cumulative culture is defined by the STRUCTURE of its history, not by how deep or broad the repertoire gets.**

**REAL-VERIFY (`scripts/run_genesis_temporal.py 500`; `runs/r163_temporal/panel.png` EYE-VERIFIED in 33s — a gold
staircase climb of frontier depth vs a flat gray asocial floor; a repertoire-breadth climb to ~312 vs asocial 8; a
combinatorial ladder scatter (first-appearance step rising with tree depth, corr 0.94); a scrambled additive-null
scatter (corr 0.01); tall gold recovery bars 2/2 with near-zero additive + null bars; a depth-coloured live 3D
world at n=3733), 3 arms × 2 seeds, 500 steps.**

**RED-TEAM (mandatory; independent refutation-first agent; verdict CONFIRMED 6/6).** (1) **precedence is
discriminating, not vacuous** — mechanistically forced to 1.0 under combinatorial, but the additive null gives 0.35
and a hand-injected single violation drops it to 0.9912, so the metric CAN fail. (2) **corr is dynamics, not a
level-definition artifact** — the additive arm uses the IDENTICAL tree (same `build_tech_tree`/`level`) yet gives
corr ~0; same definition, opposite result. (3) **permutation null correct** — permutes appearance times among
APPEARED techniques only, recomputes Spearman, p = mean(|null|≥|obs|); non-appeared kept at -1 and excluded. (4)
**byte-identical** — `_update_tech_history` reads `rep`, writes only `_tech_first_step`, no RNG/state mutation;
test asserts `array_equal` on pos AND rep over 80 steps. (5) **re-run 4 seeds (0,1,7,13)** all robust (combo corr
0.92-0.94/prec 1.0; additive corr ~0/prec ~0.35; asocial max_level 0). (6) **`_spearman` ties** match scipy 1e-9.
The decisive control is the additive null — identical tree + metric machinery, prereq gate the ONLY difference. The
descent-STRUCTURE rung (spatial R160-R162 + temporal R163) is now CLOSED with clean positives. Next (genuinely
unbounded generative tech space) in `## Frontier / next`.

## Current state (Round 162 — 2026-06-20) — GENESIS CLEAN ground-truthed phylogeny: VERTICAL transmission RECOVERS the true descent, HORIZONTAL does not (robust POSITIVE; closes the descent-recovery rung)

**R162 resolved R161's frontier option (1). R161 returned an honest NEGATIVE (the R160 cladogram does NOT recover
the true genealogy under default oblique transmission on the ECOLOGICAL-selection substrate; vertical-only raised
recovery only noisily — 0.16..0.94, sig 2/4 — because vertical-only starved demes → low Mantel power). R162
removed BOTH confounds R161 named and got a clean, robust result. 禁止造假.**

**The two fixes (no new sim mechanism — a re-parameterization + a new analysis method).**
- **Confound 1 — ecological HOMOPLASY → `spatial_tiers=False` (NEUTRAL substrate).** Turning off spatial
  ecological selection makes cultural divergence pure NEUTRAL LINEAGE drift (innovations accumulate stochastically
  down lineages) instead of convergent adaptation to shared regions — so cultural distance can track ANCESTRY
  rather than ENVIRONMENT.
- **Confound 2 — deme SHRINKAGE → `tier0_frac=0.80` lifeline.** With abundant free food, vertical-only no longer
  starves agents that can't copy recipes from hearths → the population stays large and ALL ~27 spatial demes
  survive (R161 vertical-only collapsed to 5-12) → full Mantel statistical power.
- **New method — `genealogy.partial_mantel_corr` / `partial_mantel_test`** (pure, unit-tested): the partial Mantel
  correlation of (cultural, genealogical) CONTROLLING for inter-deme SPATIAL distance (residualize both on the
  control, Pearson the residuals, label-permutation null). Directly answers the isolation-by-distance red-team.
  `genealogy_phylogeny_test` now also returns the inter-deme `d_spatial` matrix + `partial_mantel_*`.

**HEADLINE (POSITIVE, robust). In a neutral-drift world, VERTICAL transmission makes the reconstructed inter-deme
CULTURAL distances RECOVER the TRUE inter-deme GENEALOGICAL (patristic) distances — Mantel mean 0.366 (per seed
0.349 / 0.344 / 0.423 / 0.348), significant on 3/4 (seed 1 fails ONLY from 12-deme low power — same 0.344 effect
size). HORIZONTAL/oblique copying does NOT recover descent — Mantel mean 0.054, sig 0/4, ≈ the label-permutation
null — EVEN THOUGH horizontal copying is also spatially local (nearest-hearth) and therefore also builds
spatially-structured culture.** That asymmetry is the load-bearing argument: spatial geometry alone does NOT
produce the cultural↔genealogical correlation (else horizontal would show it too); only VERTICAL inheritance links
culture to the actual birth forest. VERT > HORIZ on 4/4 seeds. This upgrades R161's noisy suggestive vertical
result (0.16..0.94, 2/4) to a clean robust contrast and CLOSES the descent-recovery rung (R160 tree-shaped →
R161 ground-truthed-negative-for-horizontal → R162 clean-positive-for-vertical).

**REAL-VERIFY (`scripts/run_genesis_neutral_phylo.py 450`; `runs/r162_neutral_phylo/panel.png` EYE-VERIFIED in
143s — green VERTICAL bars tower over red HORIZONTAL bars on 4/4 seeds; Mantel bars ≈ PARTIAL-Mantel bars on 4/4
→ isolation-by-distance ruled out; a positive recovery scatter (Mantel 0.349, p 0.008); TRUE vs RECONSTRUCTED
inter-deme distance heatmaps both structured; a deme-coloured live 3D world at n=1484), neutral substrate, 4 seeds,
450 steps.**

**RED-TEAM (mandatory; refutation-first; verdict ROBUST POSITIVE).** (1) **Load-bearing NEGATIVE CONTROL = the
horizontal arm** — identical substrate, identical spatial deme geometry, ONLY the transmission channel differs, and
it returns ≈ null on 4/4. So the vertical positive is CAUSED by vertical transmission, not by the test always
returning positive, nor by spatial geometry, nor by deme counts (seeds 0 & 2 have the full 27 demes in BOTH arms
yet give opposite results: vertical 0.349/0.423 vs horizontal 0.018/0.077). (2) **Partial Mantel** (control for
space) stays ~0.34 (0.342/0.342/0.376/0.290), sig 3/4 → the recovery is NOT isolation-by-distance. (3)
**Label-permutation null** built into every Mantel gives per-seed significance. **HONEST caveats (kept):** magnitude
is MODEST (~0.37, far from a clean 1.0) — substantial homoplasy from parallel independent innovation (`innov_steps`
per newborn) + spatial mixing as agents move during life; seed-1 significance fails purely on low power (12 demes).
The directional + causal claim (vertical recovers, horizontal doesn't, beyond space, 4/4) is robust; a high-
magnitude clean tree is not claimed.

**A genuine result: on a neutral-drift world GENESIS's cultural cladistics RECOVERS the real line of descent under
vertical transmission and provably fails under horizontal copying — the gold-standard descent-recovery validation
R160→R161 was building toward. The genealogy + partial-Mantel instruments are committed and reusable. Next rung
(temporal phylogeny / open-ended complexity) in `## Frontier / next`.**

## Current state (Round 161 — 2026-06-20) — GENESIS GROUND-TRUTH cultural cladistics: the R160 cladogram does NOT recover the true line of descent under default (horizontal) transmission (HONEST NEGATIVE); vertical-only raises recovery but not robustly

**R161 answered R160's #1 honest caveat: "tree-like vs flat" is not "the RIGHT tree" — R160 reconstructed a
cladogram and showed it beats a flat column-shuffle, but there was no GROUND-TRUTH line of descent to validate
against. R161 builds the ground truth and runs the validation every phylogenetic method must pass: does
cultural-trait cladistics RECOVER the real genealogy?**

**The contribution.**
- **`alife/genesis/genealogy.py`** (new, pure/unit-tested): logs the actual BIRTH genealogy as a parent-pointer
  FOREST and computes the TRUE patristic (tree) distance between individuals (`patristic_distance_matrix`;
  cross-founder pairs join at a virtual super-root), plus a **Mantel test** (`mantel_test`) — correlation of
  two distance matrices against a label-permutation null (the right exchangeable unit: taxa, not pairs).
  Unit-validated: a perfect tree → corr 1.0; a label-shuffle → ~0; cross-founder uses the virtual root.
- **`World.genealogy_phylogeny_test`**: partitions the living pop into a grid³ of spatial demes, builds the
  RECONSTRUCTED inter-deme CULTURAL distance (mean-L1 over informative techniques — the R160 character distance)
  and the TRUE inter-deme GENEALOGICAL distance (mean pairwise patristic distance among sampled deme members in
  the logged forest), and Mantel-correlates them vs the label-permutation null. `track_genealogy` is a PASSIVE
  observer — consumes NO RNG, changes NO sim state → byte-identical to off (verified by test).
- **`vertical_only` flag**: gates OFF oblique (nearest-hearth) transmission so newborns inherit ONLY the parent's
  repertoire + innovation = pure VERTICAL descent (a real regime change — culture feeds survival — not an
  observer; default off = byte-identical to R150..R160).

**HEADLINE (HONEST NEGATIVE, robust). Under the default OBLIQUE/horizontal transmission the R160 tree-shaped
cladogram does NOT recover the true line of descent: Mantel(cultural, genealogical) significant on 0/4 seeds,
mean 0.06 — indistinguishable from the label-permutation null (≈0).** Cultural similarity tracks shared
ENVIRONMENT (spatial ecological selection + horizontal copying drive convergent cultural evolution = homoplasy),
NOT shared ANCESTRY. This RIGOROUSLY confirms R160's own panmictic-null caveat (the tree was "descent broadly"
— spatial lineage + heritable repertoire — NOT the literal genealogy).

**CAUSAL CONTRAST (suggestive, NOT robust). Gating to VERTICAL-only transmission RAISES recovery in the
predicted direction — mean Mantel 0.47 vs 0.06 (per seed 0.16 / 0.67 / 0.11 / 0.94), significant on 2/4 — but
NOT robustly:** removing oblique transmission shrinks viable demes (seed 3: corr 0.94 but only 5 demes = low
statistical power) and ecological convergence still competes with vertical drift. So the clean per-seed contrast
is NOT established; only the mean trend + the robust horizontal negative are believed. **禁止造假 — stated as a
negative, not dressed up as a positive.**

**REAL-VERIFY:** `scripts/run_genesis_genealogy.py 450` → `runs/r161_genealogy/panel.png` EYE-VERIFIED (TRUE vs
reconstructed distance heatmaps; weak horizontal recovery scatter; contrast bars vertical(green) > horizontal
(red) on 2/4 seeds with null≈0; 3D deme-coloured world). 166 genesis tests (+7). The genealogy instrument +
the diagnosed mechanism (horizontal transmission/ecological convergence erases the genealogical signal) ARE the
deliverable; both flags committed default-off byte-identical. Next: see `## Frontier / next` + `## Decisions pending`.

## Current state (Round 160 — 2026-06-20) — GENESIS cultural PHYLOGENETICS: the cultural divergence is hierarchically TREE-structured (a reconstructable cladogram of traditions), robust 3/3

**R160 PIVOTED off the twice-inert Stage-4 economy (R158/R159) to the genuine next civilization rung: cultural
CLADISTICS. R156/R157 showed local transmission grows spatially DIVERGENT traditions (F_ST>0; region↔branch
alignment) — but those are FLAT statistics ("demes differ"). R160 asks the descent-with-modification question:
is that divergence HIERARCHICALLY structured — a reconstructable phylogenetic TREE of traditions, with nested
shared-derived techniques (synapomorphies) bundling whole tech-tree branches into clades — or is it flat? The
answer is a robust POSITIVE with honest caveats. 禁止造假.**

**The contribution (read-only analysis; NO new sim mechanism, NO flag → byte-identical to the R159 sim path).**
New module `alife/genesis/phylogeny.py` (pure numpy): (1) `treelikeness` = 1 − mean Holland (2002) delta-Q over
deme quartets (1 = perfectly tree-additive; an additive quartet has its two larger pairing-sums equal → delta 0);
(2) `cophenetic_corr` = correlation of the UPGMA tree's cophenetic distances with the observed inter-deme
distances; (3) `column_shuffle_null` = the load-bearing null: permute each technique independently across demes,
preserving every technique's marginal frequency AND the prereq-DAG-induced structure, but destroying the
cross-technique COVARIANCE that bundles a branch into a clade. `World.phylogeny_test(grid,min_deme,n_shuffle)`
partitions the living population into a grid³ lattice of demes (taxa), builds the deme×technique character matrix,
and returns treelikeness + coph_corr + the column-shuffle means + the inter-deme distance matrix + per-deme
dominant technique (for the cladogram render). 4 new tests (159 genesis green): metric integrity (a hand-built
nested ((d0,d1),(d2,d3)) matrix → treelike 1.0, coph 1.0; a star → nan), column-shuffle destroys the signal,
phylogeny_test fields + off-empty (non-combinatorial → {}), and the headline real>shuffle smoke.

**REAL-VERIFY (`scripts/run_genesis_phylogeny.py 450`; `runs/r160_phylogeny/panel.png` EYE-VERIFIED — a nested
27-deme CLADOGRAM with multi-level branches (not a degenerate ladder); treelikeness bars green(local)>grey(shuffle);
cophenetic bars green>grey; a deme-coloured live 3D world; the frontier-depth climb rising ~6→14), R157
ecological-selection substrate (spatial_tiers + recipe_budget), 2 seeds + render seed, 450 steps:**
- **PRIMARY (the phylogenetic signal, load-bearing):** local treelikeness **0.682 / 0.667** > column-shuffle
  **0.510 / 0.508** on **2/2**; cophenetic corr **0.793 / 0.736** > shuffle **0.62-0.63** on **2/2**. The shuffle
  preserves marginal frequencies + the prereq-DAG structure but breaks clade covariance, so real>shuffle proves
  the divergence is genuinely TREE-structured (descent-with-modification), not flat and not a DAG/sampling artifact.
- **SECONDARY (causal probe, honest NULL):** local vs PANMICTIC transmission — local **0.675** vs panmictic
  **0.709** (local>panmictic only **1/2**). Nearest-hearth (local) cultural copying does NOT add detectable
  tree-likeness over random-hearth (panmictic) copying → the tree structure is descent BROADLY (spatial lineage +
  heritable repertoire), NOT specifically caused by the oblique cultural channel.

**RED-TEAM (mandatory; inline, refutation-first; verdict ROBUST POSITIVE).** (1) **3rd seed** — seed 2 treelike
**0.632 > shuffle 0.506**, coph **0.680 > 0.604** → the column-shuffle contrast is **3/3 seeds**. (2) **sampling-
noise REFUTED** — recompute on a RANDOM HALF of each deme's agents: treelike **0.654** holds (vs shuffle 0.506); a
sampling artifact would collapse toward the shuffle, it doesn't. (3) **metric integrity** — unit-tested: a perfect
nested tree → 1.0, a star → nan, the shuffle drops it. **HONEST caveats (kept, not hidden):** (a) magnitude is
**MODEST** (treelike ~0.65, well above the ~0.51 shuffle floor but far from a clean 1.0 tree — substantial
homoplasy: parallel discovery + the prereq DAG allow convergent acquisition); (b) the panmictic secondary is
NULL — the signal is NOT specifically the local cultural channel; (c) the asocial control (learn=False) collapses
the population (n=74, 0 demes) because this substrate REQUIRES culture to survive, so a clean spatial-only floor
can't be measured. **A genuine result: culture on this world carries a real, robust, reconstructable phylogenetic
signal (a cladogram of traditions) — the first time GENESIS measures the STRUCTURE of cultural descent, not just
its presence. Next rungs (ground-truth the descent tree; temporal phylogeny) in ## Frontier.**

## Current state (Round 159 — 2026-06-20) — GENESIS PRODUCTIVE goods trade: unlocks wasted food, yet STILL causally inert (a DEEPER honest negative than R158)

**R159 answered R158's honest negative head-on. R158 showed REDISTRIBUTING harvested energy is inert because it
does not relax the binding constraint; R159 replaced redistribution with PRODUCTION — trade in GOODS that unlock
otherwise-WASTED locked food — and red-teaming reveals an even STRONGER negative: the population is not
food-limited AT ALL, so neither redistribution nor production can move it. 禁止造假.**

**The mechanism (additive, unit-tested, byte-identical when off — `trade_goods=False` + `seed_specialists=False`
= exact R157).** Two new flags in `genesis.py`: (1) `seed_specialists` (frac `seed_specialist_frac`) starts an
ALREADY-specialized population — a minority of founders each born holding ONE random recipe, the rest naive —
isolating the *economic* question from R157's cultural-emergence bootstrap (which R155–R157 already solved).
(2) `trade_goods` (requires `tech_actions`, mutually exclusive with R158 `trade`): after a tier-t≥1 specialist
eats its own mote it acts as a HARVESTER-FOR-OTHERS — `_do_goods_trade` claims up to `goods_max` of the still-
uneaten ripe tier-t motes within `trade_radius`, REMOVES each (frees a food slot for regrowth) and ships its
full tier value as an edible GOOD to the nearest HUNGRY COMPLEMENTARY partner (lacks tier t's recipe). Energy is
CONSERVED (good = mote value, no free injection) — unlike R158's "otherwise-spoiled surplus", this consumes real
standing food. `goods_test` read-out (count, motes-freed, volume, mean partner dist); `trade_scramble` reused as
the null (random hungry recipient). 4 new tests (155 genesis green): byte-identical-off, requires-tech_actions +
excludes-trade, goods-fires-and-is-local (vs scramble dist), and the headline regression
**`test_goods_trade_is_causally_inert_on_carrying_capacity`**.

**REAL-VERIFY (`scripts/run_genesis_goods.py 300`; `runs/r159_goods/panel.png` EYE-VERIFIED — pop ON/OFF curves
OVERLAP at 900; a food-supply-invariance panel showing pop FLAT as supply varies; real goods volume; a
branch-coloured 3D living world), seed-specialist regime, 2 seeds, 300 steps:**
- **PRODUCTION (positive, real):** the productive economy FIRES — **~2450** wasted tier-t motes/run consumed-for-
  trade and shipped LOCALLY (mean partner dist **7.9** ≪ radius 12) to complementary partners; the matched-
  energy SCRAMBLE is dispersed (dist **69.2**). The mechanism does exactly what it claims.
- **CAUSAL INERTNESS (the finding, DEEPER than R158):** pop ON == pop OFF = **900** on both seeds
  (|goods−off| = **0**; + 2/2 in tests). Unlocking otherwise-wasted food does NOT raise the carrying capacity.

**RED-TEAM (mandatory; refutation-first; verdict: ROBUST NEGATIVE — and it strengthened the claim).** The obvious
alternative explanation is "pop is just food-cap-limited at 900". REFUTED decisively: with trade OFF, sweeping
**food_regrow 12→80 (≈7× supply rate)** AND **food_cap 300→2500 (≈8× food stock)** leaves pop pinned at **900 in
every single case** — at food_cap=300 the population is **3.2× the standing food count** (900 agents on ~278
motes). The carrying capacity is INTRINSIC (foraging/lifespan/world-size/energy economy), set independent of food
supply in both senses. So unlocking food cannot lift a ceiling food never set. **Two independent economy attempts
now agree (R158 redistribution, R159 production): an economy bolted onto this substrate does not change the
population outcome — because the binding constraint is not food.** This is a real, valuable scientific result.

**DECISION (anti-thrash): PIVOT.** Two principled economy mechanisms have both returned clean inertness on the
same population invariant; a third would be thrash. Per the loop's anti-thrash rule R160 pivots — see
`## Frontier` and `## Decisions pending`. The economy mechanism is kept (real, tested, default-off) as substrate.

---

## Current state (Round 158 — 2026-06-20) — GENESIS inter-agent TRADE economy: a real local exchange network, but CAUSALLY INERT (honest negative)

**R158 attacked the Stage-4 "civilization leap": turn R157's ecologically-segregated region-specialists into an
ECONOMY via EXCHANGE. The mechanism is correct and the exchange network is real and structured — but the round
delivers an HONEST NEGATIVE, red-teamed across four regimes: bolting trade onto ecological traditions is
CAUSALLY INERT (it redistributes energy without changing population or tradition outcomes). 禁止造假.**

**The mechanism (additive, unit-tested, byte-identical when off — `trade=False` = exact R157).** New flag
`trade` (requires `tech_actions`), `genesis.py`: when an agent harvests a LOCKED-tier (t≥1) mote it alone could
eat, a fraction `trade_share` of the gain flows to the nearest HUNGRY COMPLEMENTARY agent (one that LACKS tier
t's recipe, so physically could not have eaten the food) within `trade_radius`. The surplus is modeled as
otherwise-spoiled (the giver keeps its full harvest) so the transfer is positive-sum — like food ripening
(R148) it is a WORLD MECHANIC, not faked behaviour. `_do_trade` + a `trade_test` read-out (count, volume,
mean partner distance, complementary frac, cross-region frac). The causal NULL `trade_scramble`: deliver each
share to a UNIFORMLY-RANDOM hungry agent (locality + complementarity cut), same energy injected. 5 new tests
(151 genesis green): requires-tech_actions, scramble-requires-trade, byte-identical-off (pos+energy+rep),
transfers-only-to-complementary-partner (hand-built), real-is-local+complementary+less-cross-region-than-
scramble, and the headline regression **`test_trade_is_causally_inert_on_population`**.

**REAL-VERIFY (`scripts/run_genesis_trade.py 300`; `runs/r158_trade/panel.png` EYE-VERIFIED — off/trade/trade-g2
population curves OVERLAP at the 900 capacity ceiling = inert; structure bars show real-local+complementary vs
scramble-dispersed; substantial volume; a branch-coloured 3D living world), saturated regime (capacity 900),
2 seeds, 300 steps:**
- **STRUCTURE (positive, by-construction + emergent volume):** real trade is LOCAL (mean partner dist **7.6**
  ≪ radius 12) and fully COMPLEMENTARY (**1.00** of receivers lack the recipe), volume **~86k**; the matched-
  energy SCRAMBLE is dispersed (dist **65.4**, compl **0.69**). Real trade is mostly WITHIN-region (cross-region
  frac **0.07** vs scramble **0.61**) — it feeds nearby off-branch MINORITIES, not a cross-border economy.
- **CAUSAL INERTNESS (the finding):** off / trade / trade-with-2×-energy-INJECTING-gain all settle at n=**900**
  on **both** seeds (|trade−off| = **0**, |g2−off| = **0**; + 4/4 in tests). Redistribution — even net energy
  injection — does NOT lift the capacity/food-bound ceiling, and alignment is unchanged (noise). An inter-agent
  economy alone does not relax the binding constraint, so it does not drive a population/tradition transition.

**RED-TEAM (mandatory; inline, refutation-first; verdict: ROBUST NEGATIVE).** Adversarially probed FOUR regimes
trying to find ANY robust trade positive: (a) `recipe_budget=1` SHARP-specialist rescue — trade ON and OFF both
collapse to the IDENTICAL 59 survivors (no surplus exists during the bootstrap collapse); (b) harsher lifeline
(low `tier0_frac`) — universal collapse to ~5–16 (locked tiers can't bootstrap); (c) alignment sharpening —
NOISE (real 0.036 ≈ off 0.038 over 4 seeds, real<off only 2/4); (d) carrying-capacity via `trade_gain`∈{1,2,3}
— pinned at the ceiling regardless. NO regime gave trade a clean robust benefit; the inertness is genuine
because the limiting constraint (capacity/food, not energy distribution) is not relaxable by moving energy
around. **HONEST caveat:** the inertness is cleanest in the capacity-bound saturated regime (where nothing can
raise pop past the cap); in sub-capacity regimes trade's effect is pure seed-dependent NOISE, and in a richer
full-stack regime it even DESTABILIZED one seed (boom-bust). Across all: never a robust positive. The mechanism
+ scramble null are committed (default-off) and reusable for R159's redesign (trade in GOODS that unlock wasted
food). **An honest, important negative: an economy must be coupled to a relaxable constraint to matter — see
## Frontier.**

## Current state (Round 157 — 2026-06-20) — GENESIS ECOLOGICALLY-SELECTED divergent traditions (region↔branch alignment), red-teamed ROBUST

**R156 grew divergent traditions but they were NEUTRAL DRIFT (modest F_ST ~0.03). R157's question: how do you
SHARPEN modest neutral-drift traditions into discrete, economically-distinct cultures? The round delivers a
clean scientific arc — one HONEST NEGATIVE that motivates the POSITIVE mechanism, both red-teamed.**

**HONEST NEGATIVE first — forgetting does NOT sharpen drift (`culture_decay`, committed default-off).** The
frontier's leading hypothesis was "the hearth record is a never-forgetting UNION accumulator that homogenizes;
add forgetting and local divergence sharpens." Built it: `culture_decay=True` replaces the boolean union with a
per-technique floating MEMORY that decays (`memory_decay`) and must be re-deposited to stay in the sensed record
(the Tasmania / Henrich cultural-loss effect; default-off byte-identical). **Probe REFUTED it:** at decay 0.02
F_ST is a wash (0.0518 vs 0.0460 seed0; 0.0408 vs 0.0409 seed1) and at 0.05 it is strictly WORSE (0.0398/0.0345,
fewer distinct traditions) — uniform decay erodes the DEEP techniques that DEFINE a tradition faster than the
shallow shared ones. The diagnosis: R156 traditions are neutral drift in a spatially-homogeneous world, so there
is **no force maintaining divergence** and forgetting can only erode, not sharpen. Substrate kept (default-off).

**POSITIVE — the missing force is SELECTION (`spatial_tiers` + `recipe_budget`).** Make the world spatially
HETEROGENEOUS: a recipe-locked mote's tier is set by its x-axis REGION (`spatial_tiers`), so region r yields only
tier-(r+1) food, edible (via R153 `tech_actions`) ONLY by holders of that tier's recipe BRANCH. A recipe carry-
BUDGET (`recipe_budget`, the R155 `_enforce_cap_budget` mechanism applied to recipes) forces each agent to be a
branch SPECIALIST instead of a generalist-who-learns-everything (R154's convergence trap), and a high free-tier
LIFELINE (`tier0_frac`) keeps the population alive while branches sort. So in region r only recipe-r specialists
can eat the rich local food → **selection LOCKS each region to its own branch** = discrete, spatially-structured,
economically-distinct traditions MAINTAINED by local adaptation, not drift. (`recipe_upkeep`, a metabolic cost
per carried recipe, is a committed weaker alternative lever; the budget is the keystone.) New read-out
`ecological_traditions_test`: per-region own-branch vs other-branch fraction → **ALIGNMENT** = own − other. 13 new
tests (146 genesis green): 4 knobs require-tech_actions/combinatorial, all default-off byte-identical, spatial
tier=region assignment, budget caps carried branches, forget-unmaintained-technique, lossy-vs-union, read-out
fields + off-empty, spatial-beats-random smoke, two checkpoint roundtrips.

**REAL-VERIFY (`scripts/run_genesis_ecotraditions.py 450`; `runs/r157_ecotraditions/panel.png` + branch-coloured
3D `ecotraditions.gif` EYE-VERIFIED — agents coloured by their recipe BRANCH; green spatial-alignment lines sit
above grey null lines, own>other branch fraction both seeds, and the 3D shows red agents clustering in the left
region / blue in the centre, a subtle spatial colour structure):** spatial vs random-niche null, 2 seeds, 450
steps, n=6000 both —
- **SPATIAL alignment 0.049 / 0.152** (own 0.59/0.73 vs other 0.54/0.58) vs **RANDOM-niche null −0.016 / 0.008**.
  Spatial > null on **2/2** seeds (mean **0.101 vs −0.004**, null at zero); +probe 3/3 = **5/5 total**.

**RED-TEAM (mandatory; inline, refutation-first; verdict ROBUST).** (1) **metric integrity** — a hand-built
perfect region-sort (region r holds only branch r) returns alignment **1.0000**, all-branches **0.0000**.
(2) **THE POSITION-SHUFFLE NULL (load-bearing, 3 seeds)** — recompute alignment after permuting which region each
agent sits in: REAL **0.049 / 0.152 / 0.057** sits **>2σ above the shuffle floor ~0** (±0.001–0.008) on **3/3** =
GENUINE spatial structure, not a metric/sampling artifact. **HONEST caveats:** magnitude is **MODEST** (alignment
~0.05–0.15; agents still carry SOME wrong branches — own 0.59–0.73, not a pure 1.0); `recipe_budget=1` gives sharp
pure specialists but **CRASHED the population** (bootstrap chicken-and-egg — specialists starve before spatial
sorting can sort them; seed-dependent collapse to n≈50), so budget=2 + a free-tier lifeline is the viable regime.
The directional + causal claim (selection > both nulls, 5/5 seeds) is robust; SHARP discrete pure-specialist
cultures are the next rung, not yet reached. 禁止造假 — every number read from live `rep`/positions.

**A genuine emergent result: ecological selection (spatial niches + a knowledge carry-budget) turns R156's modest
neutral-drift traditions into spatially-locked, economically-distinct ones — verified + red-teamed. The path to
SHARP cultures (and then inter-group TRADE = the civilization leap) is seeded in ## Frontier.**

## Current state (Round 156 — 2026-06-20) — GENESIS emergent DIVERGENT cultural TRADITIONS (cultural F_ST), red-teamed ROBUST

**R156 opens a NEW axis on the civilization frontier. R150-R155 measured only ONE global culture frontier
(how deep the population climbs the open-ended tech tree). But a real civilization is not a single
monoculture of knowledge — it is MANY DIVERGENT cultural traditions. R156 asks whether the EXISTING
substrate already grows them, and the answer is YES (modestly), red-teamed ROBUST.**

**The mechanism — emergence on existing substrate + a clean causal control (additive, default-off,
byte-identical when off).** Oblique transmission already copies the NEAREST strong hearth (a spatial
cultural store, R148/R150), so a region that happens to climb one BRANCH of the adjacent possible
reinforces it locally (founder effect + path dependence) while another region climbs another → spatially
structured traditions. The round adds only a measurement + a null:
- **`tradition_test(grid, min_deme)`** (in situ, never feeds selection): partitions the living population
  into a `grid^3` lattice of spatial demes and computes **Wright's F_ST** over the boolean technique
  repertoire (cultural traits): `F_ST = (H_T − H_S)/H_T`, H = mean per-technique gene-diversity 2p(1−p),
  pooled vs within-deme. F_ST ≈ 0 = one global tradition; F_ST > 0 = spatially structured traditions.
  Also reports `n_distinct_traditions` (distinct deme-dominant deepest techniques) + per-deme dominant tech.
- **`panmictic_culture` (default False)** — the causal NULL: keep the SAME learners (identical
  nearest-hearth in-range gate) but copy a UNIFORMLY RANDOM strong hearth instead of the nearest one, so
  the place↔tradition correlation is cut. The ONLY manipulated variable is WHICH hearth you copy. Requires
  `combinatorial=True`; `panmictic_culture=False` is byte-identical to R150 (exact nearest-hearth path).
- 5 new tests (133 genesis green): requires-combinatorial, byte-identical-off (pos+vel+rep), panmictic
  changes the produced culture (transmission differs), tradition_test fields + range + off-empty, local
  transmission builds ≥2 demes with multiple distinct dominant techniques.

**REAL-VERIFY (`scripts/run_genesis_traditions.py 500`; `runs/r156_traditions/panel.png` +
tradition-coloured 3D `traditions.gif` EYE-VERIFIED — agents coloured by a hue hashed from their
deepest-known technique; the F_ST-over-time plot shows green LOCAL lines sitting above grey PANMICTIC):**
local vs panmictic, 2 seeds, 500 steps, grid=3 (27 demes), n≈3300–3800 —
- **LOCAL F_ST 0.0269 / 0.0256** (distinct traditions **6 / 10**) vs **PANMICTIC F_ST 0.0155 / 0.0221**
  (distinct **5 / 5**). Local > panmictic on **2/2** seeds; mean distinct traditions **8 vs 5**.

**RED-TEAM (mandatory; inline, refutation-first; verdict ROBUST).** (1) **metric integrity** — a hand-built
perfectly-divergent two-deme case returns F_ST **1.0000**, identical demes **0.0000**. (2) **THE
POSITION-SHUFFLE NULL (the load-bearing probe, 3 seeds)** — recompute F_ST after permuting which deme each
agent sits in: LOCAL real **0.032 ≫ shuffle noise floor 0.007** on **3/3** seeds, so the F_ST is GENUINE
spatial structure, not a sampling/metric artifact; local > panmictic **3/3** (0.032 vs 0.021) = spatial
transmission CAUSES the extra divergence. **HONEST caveats (in the writeup):** the magnitude is **MODEST**
(F_ST ~0.03, ~4–5× the shuffle floor, not a dramatic 0.2); and the panmictic null is NOT at the shuffle
floor either (real 0.021 > shuffle 0.006) — because reproduction is already spatial (kin-adjacent offset),
spatially-near agents share lineage and somewhat-correlated repertoires even without nearest-hearth copying.
Nearest-hearth transmission ADDS structure on TOP of that baseline; the directional + causal claim holds, the
absolute F_ST does not (yet) describe sharp discrete cultures. The 3D "spatial patches" are correspondingly
subtle, reported honestly rather than oversold. 禁止造假 — every number read from live `rep`/positions.

**A genuine emergent result: local cultural transmission over the open-ended tree grows spatially
structured, divergent traditions (not one global monoculture) — verified + red-teamed. The next step is to
SHARPEN them from modest neutral drift into discrete, economically-distinct cultures (see ## Frontier).**

## Current state (Round 154 — 2026-06-20) — GENESIS culture gates a MULTI-AXIS physical phenotype (diet + speed + reach), red-teamed ROBUST

**R154 generalises R153 from "culture unlocks ONE world-action (what you EAT)" to "culture unlocks a
multi-DIMENSIONAL physical capability VECTOR." Deep combinatorial tech-tree nodes now ALSO unlock
LOCOMOTION (a higher max speed) and HARVEST REACH (a larger eat radius), on top of R153's diet — so
cultural depth reshapes the agent's whole physical phenotype, a tech-driven capability economy rather
than a single switch. Positive and red-teamed ROBUST.**

**The mechanism (additive, unit-tested, byte-identical when off — `tech_capabilities=False` = exact R153).**
New flag `tech_capabilities` (requires `combinatorial=True`), `genesis.py` + `combinatorial.py`:
- `combinatorial.capability_techniques(level, n_seed, n_caps, step)` designates the deep tech node that
  unlocks each PHYSICAL axis i at tree-level ≥ `cap_level_step·(i+1)` (axis 0 = locomotion, axis 1 = reach),
  so each successive axis sits strictly deeper and only the cultural ratchet (transmission) reaches it
  (mirrors R153's `recipe_techniques`, distinct nodes so one tree carries both diet and capability gates);
- `_cap_speed(act)` returns a per-agent max-speed column vector (`cfg.speed·(1+cap_speed_mult)` for holders
  of `_cap_tech[0]`, else `cfg.speed`), threaded into the `_act` speed clamp in `step()` — genuinely physical
  (`_limit_speed` enforces it, so a non-holder's realized speed can never exceed the base cap);
- `_cap_reach(eaters)` returns a per-eater eat radius (`cfg.eat_radius·(1+cap_reach_mult)` for holders of
  `_cap_tech[1]`), threaded into the `_resolve` radius in `_eat_tech_actions` — a holder harvests motes the
  base radius can't touch;
- `tech_capabilities_test` read-out: `realized_axes`, `frac_unlocked` per axis, `mean_axes` (per-agent
  capability breadth), `mean_speed_cap` / `mean_reach` (the realized physical phenotype), `mean_realized_speed`
  (the actual |velocity| — the load-bearing behavioural proof). Snapshot carries the 5 capability fields.
- 9 new tests (127 genesis green): requires-combinatorial, byte-identical-off (pos+vel+food), deterministic+
  deepening capability nodes, too-shallow-tree raises, speed cap categorical + physically enforced in step,
  reach node enlarges eat radius categorically, read-out fields + off-empty, transmission>asocial smoke,
  checkpoint preserves capability phenotype.

**REAL-VERIFY (`scripts/run_genesis_capabilities.py`; `runs/r154_capabilities/panel.png` + capability-breadth-
coloured 3D `capabilities.gif` eye-verified — the social world turns GOLD as nodes spread, with purple
culturally-naive newborns visibly mixed in):** social (`learn=True`) vs asocial (`learn=False`), 2 seeds,
800 steps, cap_level_step=2, both mults 1.0 —
- **SOCIAL**: `realized_axes` **2/2**, `mean_speed_cap` **5.72** (base 3.0), `mean_reach` **5.74** (base 3.0),
  `mean_realized_speed` **4.61**, diet `realized_tiers` **4/4**, pop 2000;
- **ASOCIAL**: `realized_axes` **0**, `mean_speed_cap` **3.00 EXACTLY**, `mean_reach` **3.00 EXACTLY**,
  `mean_realized_speed` **2.65**, diet **1**, pop ~47–146 (alive on free tier-0 food but stuck at the base
  phenotype). Asocial is CATEGORICALLY locked out — the deep capability nodes are unreachable from an empty
  repertoire in one lifetime; only cumulative transmission reaches them. 禁止造假 — every number read from live `rep`/`vel`.

**RED-TEAM (mandatory; independent general-purpose agent, refutation-first; verdict ROBUST):** 6 probes.
(1) **metric integrity** — hand-set `rep`, `_cap_speed`/`_cap_reach`/`tech_capabilities_test` returned the
hand-computed values to 1e-9. (2) **THE LOAD-BEARING CONFOUND KILLED** — "is the realized-speed gap just that
social agents are denser/better-fed?" With `cap_speed_mult=0` (locomotion node unlocked but ZERO speed bonus)
realized_speed collapses **4.35 → 2.71 ≈ asocial 2.53**: **~90% of the movement gap IS the speed cap itself**,
not a health confound — the strongest "physical action, not a number" result. (3) **categorical asocial-base**
— at 2500 steps asocial speed_cap/reach stay **3.0000/3.0000**, frac_unlocked [0,0]. (4) **reach = real
access** — a holder harvests a mote at distance 4.5 (beyond base 3.0); a non-holder is denied that same mote
yet still eats a 2.5 mote normally (gate is reach-specific, categorical). (5) **byte-identical off** —
pos/vel/food `array_equal` vs the flag off. (6) **reproducible** seeds 2/3 (axes 2/2, speed_cap 5.3–5.4 vs
3.0, diet 4 vs 1 both). **HONEST (red-team noted, neutral):** headline magnitudes (speed_cap 5.72) are
seed-specific — other seeds land ~5.3–5.4 at 800 steps (not 100% of agents hold the node yet); the
DIRECTIONAL claim (social ≫ asocial, asocial == base exactly) is robust on all 4 seeds. `realized_axes` is a
presence flag (saturates easily); the load-bearing signals (speed_cap, reach, realized_speed) carry the
verdict. **CONVERGENT not divergent (the seed for R155):** cheap, freely-transmitted capabilities make the
whole population learn ALL axes — no specialization yet; R155 makes axes costly to force a division of labour.
**A genuine emergent result: culture physically determines an agent's multi-axis capability, not a payoff
scalar — verified + red-teamed. Substrate committed + reusable.**

## Current state (Round 153 — 2026-06-20) — GENESIS culture MATTERS PHYSICALLY: techniques UNLOCK a world-action (what an agent can EAT), red-teamed ROBUST

**R153 lifts the R151 capstone's top frontier — "make culture MATTER physically." Until now the learned
`tech` only multiplied a harvest SCALAR (1+tech_gain·tech): cultural depth changed a NUMBER, not what an
agent DID. R153 makes culture change a PHYSICAL ACTION — what food an agent can eat — and the result is
positive and red-teamed ROBUST.**

**The mechanism (additive, unit-tested, byte-identical when off — `tech_actions=False` default = exact
R150/R151).** New flag `tech_actions` (requires `combinatorial=True`), `genesis.py` + `combinatorial.py`:
- food spawns in recipe-locked **TIERS** (`_food_tiers`): tier 0 is the free resource (prob `tier0_frac`),
  tiers 1..`n_food_tiers`-1 are locked;
- a tier-t mote (t≥1) is edible **ONLY** by an agent whose combinatorial repertoire holds that tier's
  **RECIPE technique** — a deep tech-tree node chosen by `combinatorial.recipe_techniques`: tier t's recipe
  sits at tree-level ≥ `recipe_level_step·t`, so a higher tier requires a strictly deeper place in the
  adjacent-possible climb, and only the cultural ratchet (transmission) reaches it;
- `_eat_tech_actions` resolves eating per-tier high→low (≤1 mote/agent/step), gating each locked tier on
  `self.rep[agent, recipe_tech[t]]`; the tier's value (`food_value·(1+tier_value_bonus·t)`) feeds the usual
  caste/technique multipliers via `_harvest_gain(base=...)`. Locked motes simply persist (the visible signature);
- `tech_actions_test` read-out: `realized_tiers` (tiers ≥1 living agent can eat), `mean_edible_tiers` (per-agent
  diet breadth), `locked_food_frac` (ripe food no one can eat), cumulative `tier_eats`. `food_tier` checkpoint
  round-trips. 10 new tests (109 genesis green): requires-combinatorial, byte-identical-off, deterministic+
  deepening recipe selection, too-shallow-tree raises, categorical eat gate + tier value, tier-0-always-edible,
  tier spawn distribution, fields/off-empty, social>asocial smoke, food_tier round-trip.

**REAL-VERIFY (`scripts/run_genesis_recipes.py`; `runs/r153_recipes/panel.png` + diet-breadth-coloured 3D
`recipes.gif` eye-verified — a dense world, agents mostly GREEN = full realized diet with a red/orange
minority of culturally-naive newborns, and visibly more red mid-run than at the end = the realized-tiers
climb):** social vs asocial, 2 seeds, food_cap 1200 / tier0_frac 0.7 / 4 tiers / tier_value_bonus 2.0 —
- **SOCIAL** (`learn=True`): `realized_tiers` 1→**4/4**, mean diet breadth **3.37/4**, pop **2000**,
  `locked_food_frac` **0.00** (the population unlocks every tier and wastes no food);
- **ASOCIAL** (`learn=False`): stuck at **1 tier**, breadth **1.0**, pop **~96** (alive but locked out),
  **81%** of ripe food rots uneaten — cumulative cultural capability is impossible in one lifetime from an
  empty repertoire (the deep recipes are unreachable). ~21× population, full diet vs locked. 禁止造假 — every
  number read from the live `rep`/`food_tier`.

**RED-TEAM (mandatory; independent general-purpose agent, refutation-first; 禁止造假 — verdict ROBUST):**
(1) **metric integrity** — hand-set a known `rep`/`food_tier`, `tech_actions_test` returned exactly the
hand-computed realized_tiers/edible/locked (reads live state, nothing staged). (2) **categorical gate** — the
core "this is a physical ACTION not a scalar" check: asocial `tier_eats=[1982,0,0,0]` — **EXACTLY ZERO** motes
of every locked tier; social `[23952,3468,3543,3318]`. All-or-nothing, not a smaller multiplier. (3)
**reproducible** seeds 5/6/7 — social tiers=4/pop=2000 vs asocial tiers=1/pop 69–98, every seed. (4) **THE
CONFOUND KILLED** — "is load-bearing just energy injection (social eats richer tiers)?" With
`tier_value_bonus=0` (locked tiers worth the SAME base value as tier 0) the population gap is **byte-identical**
to the bonus=2.0 case (13.7× / 42.6×): **~100% of the population gap is genuine ACCESS to more food motes, NOT
the richer payoff** — the strongest possible result for the real-action-unlock interpretation; realized_tiers
still climbs to 4 with bonus=0 (the unlock is about access, not payoff). (5) **distinct from scalar** —
tech_actions=False keeps food_tier all-zero / no recipe table (R153 is a genuinely new physical axis on top of
R150's scalar). (6) **no artifacts** — deterministic, food_tier stays length-synced after many steps, no
dead-slot repertoire leak into newborns. **HONEST (red-team noted, neutral):** social pop is capacity-clamped
at 2000 (a ceiling, not a free-running equilibrium) — does not affect the gap, the gate, or the access-vs-payoff
decomposition. **This is a genuine emergent result: culture physically determines what an agent can do in the
world, not just a payoff scalar — verified + red-teamed. Substrate committed + reusable.**

## Current state (Round 152 — 2026-06-20) — can coupling building to the caste flip R151's SUBSTITUTION into COMPLEMENT? HONEST NEGATIVE: substitution is robust

**R151 found niche construction SUBSTITUTES for the division of labour (caste-free building lets hearths ripen
food for free → the processor caste is selected away). R152 tried to FLIP that into COMPLEMENT — to make a
genuine division-of-labour economy RE-EMERGE around niche construction — by coupling building to the caste.
It did NOT emerge. Honest finding: SUBSTITUTION is the robust attractor.**

**The mechanism built (additive, correct, unit-tested, byte-identical when off — `build_specialized=False`
default = exact R148..R151).** New flag `build_specialized` (requires `building` AND `specialize`), `genesis.py`:
- build STRENGTH is CONVEX in the caste trait — a build act deposits `build_gain · spec^build_spec_gamma`, so a
  pure builder (spec=1) raises a real hearth and a harvester (spec≈0) leaves a dead ember (the R147 convexity
  lesson applied to building);
- a builder earns a maintenance WAGE (reusing the R147 `_pay_processors` path): `_build` records each hearth's
  last maintainer in `struct_last_builder`; `_ripen_hearths` credits that maintainer on `food_proc` for the
  motes it ripens; when a harvester eats one, the wage flows back to the builder. So value flows from the
  consumers of the shared infrastructure back to its maintainers.
- 6 new tests (99 genesis tests green): requires-both validation, byte-identical-when-off, convex build
  strength, wage-to-maintainer, viable-world smoke, checkpoint round-trip of `struct_last_builder`.

**REAL-VERIFY (`scripts/run_genesis_complement.py`; `runs/r152_complement/panel.png` + caste-coloured 3D
`complement.gif` eye-verified — COMPLEMENT and SUBSTITUTE worlds both uniformly teal/harvester):** the intended
builder caste did NOT re-emerge, across THREE distinct mechanistic regimes (NOT parameter jiggling — each
attacks a different reason the caste might fail):
- **food-rich** (R151's regime): the caste FULLY collapses, identical to R151 — under slow decay the crowd's
  incidental weak deposits ACCRETE enough hearths that no dedicated builder is needed (building = free public good);
- **scarce + fast-decay hearths** (the viable regime SHOWN): the world survives at carrying capacity but only a
  **~3% maintainer MINORITY** forms (`frac_build` 0.03 COMPLEMENT vs 0.00 SUBSTITUTE, coupling shift **+0.029 ≈
  0**; `spec_mean` 0.13 vs 0.11 — both harvester-dominated). One tall hearth (high reach) feeds hundreds, so the
  economic EQUILIBRIUM needs only a handful of builders — NOT a balanced Smithian split;
- **many-small-hearths** (low reach, to force more maintainers): the whole world STARVES (non-viable, all 3
  conditions extinct).
**Conclusion: even an explicit convex-build + maintenance-wage coupling does not flip substitution; the shared,
accretive, persistent nature of built infrastructure keeps building a near-public good that a tiny minority
supplies, so the harvester caste still dominates. This EXTENDS R151 — substitution isn't a fluke of one regime,
it resists a direct engineering attempt to flip it.** 禁止造假 — `frac_build` read from the live `spec` trait.

**HONEST caveats (flagged, not hidden):** (1) the `WAGE-OFF` control (coupling on, `process_payment=0`) kills
the whole population, but that is CONFOUNDED — the wage is also a raw energy injection, so its removal starves
the world independently of caste dynamics → it is NOT clean evidence the caste is load-bearing, and is not
claimed as such. (2) A ~3% builder minority is a real persistent specialist niche, just not the balanced
division of labour the round set out to grow; the negative is on the STRONG claim. The coupling mechanism stays
in the codebase behind its default-off flag — a correct, reusable tool for a future substrate-level redesign.

## Current state (Round 151 — 2026-06-20) — GENESIS INTEGRATED CAPSTONE: the ladder stages INTERACT, they don't sum (niche construction substitutes for the division of labour)

**Every ladder stage (R143 predator arms race · R147 caste division of labour · R148 niche-construction
hearths · R150 open-ended combinatorial culture) had only ever been verified in ISOLATION behind its own
flag — they had NEVER run together. R151 turns them ALL on in ONE world and asks the only question an
isolated test cannot: do they SUM into a civilization, or INTERACT?** The answer is the round's finding.

**(a) A real CORRECTNESS collision, found + fixed.** With both `specialize` and `culture` on, the harvest
payoff `if specialize ... elif culture ...` was MUTUALLY EXCLUSIVE — culture's `tech_gain` energy bonus was
silently DROPPED under caste, so the open-ended cultural ratchet lost its selective gradient. Fixed by
composing the two modifiers MULTIPLICATIVELY in a new `_harvest_gain(eaters)` helper (`genesis.py`):
`food_value · (1-spec)^gamma · (1+tech_gain·tech)`, each term gated on its own flag → byte-identical to every
prior single-flag config (R147/R149/R150), changing ONLY the never-before-run both-on case. Unit-test +
byte-identical guard added; 93 genesis tests green (+3: `_harvest_gain` composition, single-flag legacy match,
all-stages-coexist smoke).

**(b) HEADLINE EMERGENT INTERACTION — niche construction SUBSTITUTES for the division of labour.** Running
all stages together, the Stage-3 PROCESSOR CASTE COLLAPSES: in the integrated world the fraction of processors
(heritable `spec`>0.8) → 0.00 and `spec_mean` → 0.085 (86% pure harvesters). The cause is the Stage-4 hearths:
built hearths ripen raw food PASSIVELY (`_ripen_hearths`), and with `building=True` the per-agent `_process`
action is REPLACED by `_build` (genesis.py:482-485), so the costly processor caste has no role left and is
selected away. Built infrastructure makes a division of labour obsolete — automation displacing labour,
emergent in situ. What DOES coexist in the one living world: the predator-prey arms race persists (no
extinction), hearths accumulate, and the open-ended culture keeps climbing.

**REAL-VERIFY (`scripts/run_genesis_capstone.py`; `runs/r151_capstone/panel.png` + caste-coloured 3D
`capstone.gif` eye-verified — a dense, alive, uniformly-harvester 3D world, consistent with the collapsed
caste):** at the IDENTICAL food-rich regime —
- **SUBSTITUTION** — WITH hearths frac_processor → **0.00** (seeds 0 AND 1); WITHOUT hearths (building off,
  same food) → **0.62**. The decisive disambiguation: building-ON/culture-OFF also → 0.00, building-OFF/
  culture-OFF → 0.62, so the single causal variable is the HEARTHS, not culture's harvest bonus.
- **MECHANISM** — with ~0 processors the hearths still sustain ~**400 ripe (edible) food** at any instant →
  niche construction is doing the processing the caste otherwise would.
- **COEXISTENCE** — prey ~2500 + predators ~90 persist (no extinction, 2 seeds); 600 standing hearths;
  open-ended culture `pop_distinct` → **319**, frontier level → **10** (transmission-driven, climbs under the
  full stack).

**RED-TEAM (independent agent, refutation-first; 禁止造假 — verdict ROBUST):** (1) reproducible across seeds
2/3/4 — WITH hearths frac_proc 0.000 every seed, WITHOUT 0.44-0.57 (the 0.62 was not a fluke); (2) NOT a
threshold artifact — the WHOLE spec distribution shifts (median 0.05 vs 0.77-0.84), any cutoff in [0.2,0.9]
gives the same story; (3) MECHANISM causally load-bearing — disabling ONLY hearth ripening (reach=0) while
keeping hearths makes the population go EXTINCT (hearths are the sole ripening path under building); (4)
predators ruled out (caste still collapses with `n_predators0=0`) and culture ruled out (collapses with
culture off). **One honest caveat the red-team flagged:** the no-hearth state is processor-DOMINATED
(spec_mean ~0.7, pure harvesters only 5-14%), not a balanced 50/50 Smithian split — so "division of labour"
mildly oversells what's being substituted-for; the substitution direction and magnitude are not in doubt.
**Also honest:** the open-ended cultural climb is TRANSMISSION-driven (newborns inherit the repertoire and
discover from the adjacent possible regardless of the energy payoff), so (a)'s harvest fix is a CORRECTNESS
fix, NOT a cultural-climb mover in this food-rich regime (the legacy dropped-payoff world climbs the same).
**This is a genuine emergent stage-interaction finding, not theatre.** The capstone substrate + the
`_harvest_gain` composition are committed and reusable.

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
- **(R163) TEMPORAL phylogeny / open-ended cumulative descent — RESOLVED, POSITIVE (robust), no CEO action.**
  Frontier option (1) landed: the combinatorial culture's first-appearance HISTORY recovers the generative tree's
  time-ladder (precedence 1.0, level<->time corr 0.94, sig 2/2 vs label-null ~0); the additive null scrambles it
  (prec 0.35, corr 0); asocial never climbs (max_level 0). Red-teamed CONFIRMED 6/6 over 4 seeds; the additive null
  is the decisive control (identical tree+machinery, prereq gate the only difference). Honest sharpest point:
  depth/breadth MAGNITUDE cannot distinguish cumulative descent from unstructured accumulation — only the temporal
  ORDER does. The descent-STRUCTURE rung (spatial R160-R162 + temporal R163) is CLOSED. Per anti-thrash, R164
  PIVOTS to frontier option (2): GENUINELY UNBOUNDED generative tech space. The `track_tech_history` +
  `temporal_ladder_signal` instruments are committed + reusable. No CEO action.
- **(R162) CLEAN ground-truthed phylogeny — RESOLVED, POSITIVE (robust), no CEO action.** R161's frontier option
  (1) landed: in a NEUTRAL-drift substrate (`spatial_tiers=False` + `tier0_frac=0.80` lifeline) cultural cladistics
  RECOVERS the true genealogy under VERTICAL transmission (Mantel mean 0.366, sig 3/4) and provably does NOT under
  HORIZONTAL copying (mean 0.054, sig 0/4 ≈ null) — the horizontal arm is the load-bearing negative control;
  partial Mantel rules out isolation-by-distance; honest caveat = modest magnitude (~0.37, homoplasy). The
  descent-recovery rung (R160→R161→R162) is CLOSED. Per the anti-thrash rule the loop does NOT push for higher
  magnitude now; R163 PIVOTS to frontier option (2)/(1-new): TEMPORAL phylogeny / open-ended complexity. The
  genealogy + partial-Mantel instruments are committed + reusable. No CEO action.
- **(R161) GROUND-TRUTH cladistics — RESOLVED as an HONEST NEGATIVE (robust for horizontal), no CEO action.** The
  ground-truth instrument (`genealogy.py` + `genealogy_phylogeny_test` + `vertical_only`) is built, unit-validated,
  and committed default-off. Finding: under default horizontal transmission the R160 cladogram does NOT recover the
  true genealogy (0/4 sig, ≈null) — cultural similarity is environmental convergence (homoplasy), not ancestry.
  Vertical-only raises recovery (mean 0.47, up to 0.94) but only 2/4 sig (deme-shrinkage low-power). Per the
  anti-thrash rule the loop does NOT keep re-running this verify; R162 either makes vertical recovery robust (one
  bounded attempt: neutral-drift substrate or seeded founders) OR PIVOTS to a new rung (temporal phylogeny /
  generative tech space). The instruments are reusable for any future descent-recovery claim. 禁止造假.
- **(R160) GENESIS cultural CLADISTICS — RESOLVED, POSITIVE (robust 3/3).** The pivot off the inert economy
  landed: the cultural divergence is hierarchically TREE-structured (treelike > column-shuffle 3/3, subsample-
  stable, red-teamed). Honest caveats kept (modest magnitude; panmictic-secondary null; asocial can't floor).
  Loop continues to R161 = ground-truth the descent tree (track a real genealogy, recover the phylogeny). The
  phylogeny module/metrics are committed + reusable. No CEO action.
- **(R159) GENESIS Stage-4 ECONOMY (both redistribution R158 + production R159) — HONEST NEGATIVE, PARKED; loop
  PIVOTS to cultural phylogeny (R160).** Two principled economy mechanisms both proved causally inert on the
  population because the carrying capacity is INTRINSIC (foraging/lifespan), not food-limited — red-teamed
  decisively (pop=900 flat across food_regrow 7× AND food_cap 8×; 3.2× the food count at fc=300). The mechanisms
  (`trade` R158, `trade_goods`+`seed_specialists` R159, + scramble nulls) are committed default-off substrate,
  reusable IF a future substrate change makes food the binding constraint (Frontier option 2, would be a
  `vr-lead`-gated substrate redesign). NOT a CEO gate; logged so the economy rung is revisited deliberately
  rather than thrashed. R160 proceeds with cultural phylogeny/cladistics (Frontier option 1). No CEO action.
- **(R152) Stages 3+4 COMPLEMENT (a division of labour re-emerging around niche construction) — HONEST
  NEGATIVE, PARKED.** Coupling building to the caste (convex build skill + maintenance wage) did NOT flip
  R151's substitution across 3 distinct regimes — at most a ~3% maintainer minority, not a balanced caste,
  because shared/accretive/persistent infrastructure stays a near-public good a tiny minority supplies. The
  mechanism (`build_specialized`, default off) is committed + unit-tested for a future substrate redesign
  (e.g. make hearths INDIVIDUALLY owned/excludable so a builder captures the value, or require a distinct
  non-substitutable builder-only ACTION). NOT a CEO gate; logged so it's revisited deliberately. No CEO action.
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

**Current ceiling (post-R173): the unattended multi-day climb is a REAL LOOP — start once, glance at a live
dashboard.** R172 made the open-ended embodied climb durable across process death; R173 stands up the actual
unattended driver: `genesis/daemon.py` `tick(state_dir, cfg, seed, seg)` = `persist.run_segment` + regenerate a
rolling LIVE PANEL from the whole accumulated trajectory, with `tick_index` persisted in `daemon.json` so any
fresh process (cron/systemd/supervisor/cloud cron) resumes the SAME world. REAL-VERIFY: 6 real subprocess ticks
at irregular cadence → one continuous monotone history step 0→320, depth 3→9, breadth 130→1000, diet 1→4,
dashboard refreshed each tick, restored deep population rendered. Durable instrument: `genesis/daemon.py` +
`scripts/run_genesis_r173.py`. **Honest caveat now driving the next rung: with K=1000 the climb saturates inside
tick 1, so ticks 2-6 show persistence, not continued climbing.** Candidate R174+ frontiers, ranked ambition ×
feasibility:
(1) **SUSTAINED MULTI-TICK CLIMB + wire the real supervisor (TOP).** Tune the config so the open-ended climb does
NOT saturate in one segment (raise the cap toward thousands AND/OR slow innovation so depth/breadth keep RISING
tick after tick over many segments), then wire `daemon.tick` into the actual `~/.claude/bin/evolving-loop.sh`
supervisor / a cron tick so it runs for real days — the dashboard visibly climbing across dozens of ticks is the
CEO's core "just by running, it keeps developing" deliverable, finally end-to-end.
(2) **LONG-HORIZON DEPTH DIVERGENCE in the BODY** — over a long persistent run, a FIXED tree plateaus at its hard
ceiling while the generative tree keeps deepening; show "fixed vs generative" diverging in the EMBODIED diet/axes
ceiling over thousands of steps via the daemon path.
(3) **Stage-2 SIGNALLING redesign (parked)** — synchronous sharply-lethal predation arena; believe emergence only
if it beats frozen AND deaf AND causal, ≥3 seeds, red-team.
**Bias: the next LEAP IN KIND is (1) — the loop now RUNS unattended; make what it produces visibly KEEP CLIMBING
across days, not plateau in the first tick.** Caveat carried forward: continuity is exact only when the resumed
process rebuilds the SAME `gen_cfg()` (a cfg/capacity mismatch raises on restore by design); the multi-day driver
must pin the config.

**Current ceiling (post-R172): the open-ended embodied world is now PERSISTENT — it survives process death.**
R171 made the open-ended grown tree drive the body; R172 makes that whole climb durable: the grown tree itself
is checkpointed (`GrowingTree.state()/restore()` + `save/load_checkpoint`), so a resumed run on the generative +
depth_gates substrate is BIT-FOR-BIT identical to an uninterrupted one (verified across 4 REAL OS-process
restarts, `max|diff|=0`), with depth (3→9) and embodied diet ceiling (1→4) climbing across the restart
boundaries. Load-bearing red-team: sabotaging the restore (reset to a fresh seed-only tree = pre-R172 bug)
forces divergence, so the continuity is CAUSED by the restore. Durable instrument: `scripts/run_genesis_r172.py`
+ the persist tree-checkpoint path. This UNBLOCKS the "left running for days" deliverable on the open-ended
substrate. Candidate R173+ frontiers, ranked ambition × feasibility:
(1) **STAND UP THE MULTI-DAY UNATTENDED CLIMB (TOP — now unblocked).** Wire a supervisor/cron tick to call
`persist.run_segment` on the generative + depth_gates `gen_cfg()` against a single on-disk `state_dir`, with a
rolling live panel regenerated each tick from the accumulated trajectory — a genuine standing artifact where
depth/diet-ceiling/axes keep advancing on disk across days and real restarts. R172 proved the segment loop is
correct; this makes it a continuously-running world, the CEO's core "just by running, it develops" deliverable.
(2) **LONG-HORIZON DEPTH DIVERGENCE verify (paired with the body)** — over a long persistent run, a FIXED tree
plateaus at its hard ceiling while the generative tree keeps deepening; show "fixed vs generative" diverging in
the EMBODIED diet/axes ceiling, not just in an abstract count, over thousands of steps via the persist path.
(3) **Stage-2 SIGNALLING redesign (parked rung)** — synchronous sharply-lethal predation arena; believe
emergence only if it beats frozen AND deaf AND causal, ≥3 seeds, red-team. **Bias: the next LEAP IN KIND is (1)
— now that the open-ended embodied world is provably persistent, actually LEAVE IT RUNNING and watch depth + the
body keep climbing on disk across days.** **Caveat carried forward:** continuity is exact only when the resumed
process rebuilds the SAME `gen_cfg()` (a cfg/capacity mismatch raises on restore by design); the multi-day
driver must pin the config.

**Current ceiling (post-R171): the open-ended grown tree now CAUSALLY drives the BODY.** R170 made the cultural
repertoire open-ended; R171 fuses it with embodiment via `depth_gates`: the diet tiers an agent can physically eat
and the locomotion/reach capability axes it has unlocked are gated on its REALIZED cultural DEPTH (`pop.tech`), not
on pre-built nodes — so the EMBODIED ceiling inherits the grown tree's open-endedness. REAL-VERIFY + red-team
CONFIRMED: uncapped (K=4000) → depth 4→11, diet ceiling → top tier 4, both axes, pop 1000; capped (K=20) → depth
frozen 1, ceiling 0, no axes; null (innov=0) → tree never grows, ceiling 0. The decisive red-team control: a capped
world with ALL food free keeps a HEALTHY pop (309) yet its ceiling stays 0 — the freeze is the depth-CAP, not pop
death; the cap is the only difference. Durable instrument: `depth_gates` + `GenesisWorld.diet_capability_ceiling()`
+ `scripts/run_genesis_r171.py`. Candidate R172+ frontiers, ranked ambition × feasibility:
(1) **WIRE THE SUPERVISOR to `persist.run_segment` on the generative + depth_gates substrate (TOP — the literal
"left running for days" deliverable).** A genuine multi-day cloud climb where depth, diet ceiling, axes and the
rolling live panel all keep advancing on disk — open-ended embodiment unfolding unattended. Cheap; turns R169-R171
into one standing artifact.
(2) **LONG-HORIZON DEPTH DIVERGENCE verify** — over a long run, fixed tree plateaus at its hard ceiling while the
generative tree keeps deepening; pair it with the embodied ceiling so "fixed vs generative" shows up in the BODY.
(3) **Stage-2 SIGNALLING redesign (parked rung)** — synchronous sharply-lethal predation arena; believe emergence
only if it beats frozen AND deaf AND causal, ≥3 seeds, red-team. **Bias: the next LEAP IN KIND is (1) — leave the
now-embodied open-ended world running for days and watch the body keep climbing; this is the CEO's core deliverable.**
**HONEST caveat carried forward:** the diet/axes ceiling is the MAX over living agents, so it pins early once any
agent reaches a depth; the load-bearing claim is the CAP control (capped/null frozen vs uncapped climbing) + the
broad realized eating (`_tier_eat_count` positive across ALL tiers in the uncapped pop), not the single-agent max.
Also depth_gates is the GENERATIVE replacement for the fixed-node gates (tech_actions/tech_capabilities), mutually
exclusive with them by construction.

**Current ceiling (post-R170): open-endedness is now CAUSAL IN THE LIVING WORLD.** The live civilization no longer
explores a FIXED pre-built tech tree (a frozen pre-set ceiling) — `combinatorial.GrowingTree` (the dense-rep
live-world analogue of R164 `unbounded.TechSpace`) GROWS the tree on demand from the population's real
compositions, so the cultural frontier is open-ended BY CONSTRUCTION in the world you watch develop, bounded
ONLY by the memory cap (red-team CONFIRMED: cap sweep → breadth tracks the cap exactly 30/120/3668 with healthy
pops; no-composition null → breadth stays at n_seed). Crucially this needed NO sparse-rep migration (the R169
frontier had flagged a vr-lead rep rewrite) — the generative tree drops onto the EXISTING dense boolean rep
behind `generative_tree`, so the architectural gate is avoided. Durable instrument: `combinatorial.GrowingTree`
+ `scripts/run_genesis_r170.py`. Candidate R171+ frontiers, ranked ambition × feasibility:
(1) **GATE EMBODIED ACTIONS ON THE GROWN TREE (TOP — closes the open-endedness→body loop).** The generative tree
is currently an abstract repertoire; it does NOT yet gate diet tiers / physical capability axes (those designate
FIXED deep nodes ahead of the run). Make recipe/capability designation DYNAMIC over the live grown tree (e.g. the
deepest currently-materialized nodes unlock the next diet tier / capability axis) so OPEN-ENDED culture causally
drives ever-deeper EMBODIED capability — open-ended complexity you can SEE in the agents' bodies, not just a count.
(2) **WIRE THE SUPERVISOR to `persist.run_segment`** on the generative substrate for a genuine multi-day cloud
climb with a rolling live panel — the world literally left running for days, frontier climbing the whole time.
(3) **Stage-2 SIGNALLING redesign (parked rung)** — synchronous sharply-lethal predation arena; believe emergence
only if it beats frozen AND deaf AND causal, ≥3 seeds, red-team. **Bias: the next LEAP IN KIND is (1) — fuse the
now-unbounded culture with the body so open-endedness shows up as embodied capability, not an abstract repertoire.**
**HONEST caveat carried forward:** the R170 cap control is decisive, but in a short run the fixed tree's depth was
COMPARABLE to the generative tree's — the load-bearing claim is "frontier bounded only by capacity," not "generative
out-depths fixed in 320 steps." A long-run depth divergence (fixed plateaus at its hard ceiling, generative keeps
climbing) is worth a dedicated long-horizon verify.

**Current ceiling (post-R169): GENESIS is now a PERSISTABLE, RESUMABLE PROCESS — it survives process death and
resumes the SAME civilization (bit-for-bit continuous, proven against load-bearing negative controls), so the
CEO's "just by running locally or in the cloud, freely develops toward a civilization" is a concrete, restart-proof
artifact: 6 real subprocess restarts climb connected depth 0→13 / breadth 6→598 as ONE history. Durable instruments:
`persist.py` (run_segment = the per-tick persistent driver primitive; continuous/chained_trajectory = the continuity
proof) + `scripts/run_genesis_persist.py`. The R168 watchable full-stack world + this persistence layer = the literal
deliverable.** Candidate R170+ frontiers, ranked ambition × feasibility:
(1) **BREAK OUT — make open-endedness CAUSAL (TOP AMBITION).** Wire `unbounded.TechSpace` (R164) into the live world
so the OPEN repertoire climbs past the fixed-tree `max_techniques` ceiling AND gates physical actions — requires the
fixed-width boolean `rep` matrices → a sparse repertoire (spike-then-migrate, `vr-lead` architectural gate). The
R160-R168 instruments + R169 persistence now exist to validate a genuinely open-ended LONG run. (2) **WIRE THE
SUPERVISOR to `persist.run_segment`** for a genuine multi-day cloud climb: an external driver calls one segment per
tick (network-resilient, like evolving-loop.sh), with a rolling live panel regenerated from the on-disk trajectory —
the world literally left running for days. Cheap; turns R169 into a standing artifact. (3) **Stage-2 SIGNALLING
redesign (the one parked rung)** — synchronous sharply-lethal predation arena; believe emergence only if it beats
frozen AND deaf AND causal, ≥3 seeds, red-team. **Bias: R168+R169 built the embodied, persistent world; the next
LEAP IN KIND is (1) causal open-endedness — make the repertoire genuinely unbounded IN the living world — not more
plumbing or analysis. Gate the rep-matrix redesign on vr-lead first.**

**Current ceiling (post-R168): the integration leap is DONE — the whole civilization stack runs as ONE
persistent, RENDERED, watchable world that develops just by running (connected tech depth → 14, capability axes
unlock, diet broadens; agents visibly violet→gold; resume proven). For the first time the CEO's "a world that,
just by running, develops toward a civilization" is a concrete artifact, not a pile of isolated mechanisms.
Durable instruments: `civdev.py` (civ_config = the canonical full-stack regime, develop_trajectory observer,
develop_vs_control null, capability_color) + `scripts/run_genesis_civ.py` (the watchable driver). The
honest-claim discipline tightened: the asocial null is fair only at a MATCHED innovation budget (Tomasello's
ratchet), baked into the docstring.** Candidate R169+ frontiers, ranked ambition × feasibility:
(1) **PERSISTENT, RESUMABLE LONG RUN (TOP — the literal CEO deliverable now within reach).** R168 proved a single
run develops + checkpoints; the next rung is a CHECKPOINT-CHAIN long/cloud run the CEO can just leave running,
with development surfaced live (rolling panel/GIF), so the world keeps climbing across sessions/days. Feasible on
the committed checkpoint API; lands the "just by running" promise. (2) **BREAK OUT — make open-endedness CAUSAL.**
Wire `unbounded.TechSpace` (R164) into the live world so the OPEN repertoire keeps climbing past the fixed-tree
ceiling and GATES physical actions — requires the fixed-width `rep` → sparse repertoire (spike-then-migrate,
`vr-lead` architectural gate). The R160-R168 instruments now exist to validate it. (3) **Stage-2 SIGNALLING
redesign (the one parked rung)** — synchronous sharply-lethal predation arena; believe emergence only if it beats
frozen AND deaf AND causal, ≥3 seeds, red-team. **Bias: R168 reconnected to the embodied world; keep the momentum
THERE — (1) the persistent runnable civilization, or (2) the causal open-endedness — not back into standalone analysis.**

**Current ceiling (post-R167): the cumulative-culture repertoire is now characterised on FOUR axes — BREADTH
(R160-R166), RATE (R165-R166, emergent from the live economy), and now STRUCTURE: connected DEPTH + prereq CLOSURE
(R167). The R167 lesson is sharp and reusable: breadth and nominal max_level MISLEAD — the additive null beats
combinatorial on both yet is a disconnected scatter; the cumulative ladder is the CONNECTED, prereq-closed DAG.
Durable instruments: `techdepth.py` (closure_fraction, connected_depth, realized_edges, depth_trajectory) — a
saturation-proof structural validator for any future cumulative-descent claim.** The analysis-arc has now mapped
cumulative culture thoroughly (breadth/rate/structure/temporal-order/phylogeny). REMAINING GAPS / candidate R168+
frontiers, ranked ambition × feasibility:
(1) **BREAK OUT OF THE ANALYSIS ARC — make open-endedness CAUSAL in the embodied world (TOP AMBITION, the CEO
integration).** Wire `unbounded.TechSpace` into `GenesisWorld` so the OPEN repertoire GATES physical actions and is
SELECTED in the living sim — open-endedness driving behaviour, not just measured. Lift requires the fixed-width `rep`
matrices → sparse repertoire (spike-then-migrate, `vr-lead` architectural gate). The R160-R167 instruments now exist
to validate it once built. (2) **A SINGLE PERSISTENT LONG RUN, rendered + watchable** — the CEO deliverable is a
world that "just by running develops toward civilization"; produce one long integrated run with a spatial render
(GIF) of settlements forming / tech spreading / roles differentiating + the climbing complexity metrics overlaid.
Risk: the GL/GIF path is more fragile than the matplotlib panels (commit-early, shrink frames). (3) **Stage-2
SIGNALLING redesign (the one parked rung)** — synchronous, sharply lethal predation rounds (Floreano/Mitri arena);
believe emergence only if it beats frozen AND deaf AND causal, ≥3 seeds, red-team. **Bias: the analysis arc is now
deep enough; R168 should be a LEAP IN KIND — (1) or (2) — not another structural metric on the same world.**

**Current ceiling (post-R166): open-endedness is OPENED (R164), its RATE law characterised (R165), and that
rate law is now shown to EMERGE FROM THE LIVE ECONOMY (R166) — closing R165's "E(N)∝N is posited" caveat. In the
real evolved-neural GenesisWorld the per-step innovation rate rises with the accumulated repertoire BECAUSE tech
pays energy → bigger population → more innovation attempts; the decisive tech_gain=0 control flattens it and
saturates the repertoire ~4-5× lower (red-teamed CONFIRMED, 4 fresh seeds; load-bearing evidence = matched-N
dN/dt ~2-3× the control at equal N). Durable instruments: `unbounded.py`, `phylorate.py`, and now
`livephylorate.py` (step_trajectory / rate_slope) — the live bridge so the abstract rate tools apply to the real
world. REMAINING HONEST GAP: this measured the live BREADTH rate; whether the economy also accelerates frontier
DEPTH (max_level), and whether the live tech space can be made genuinely OPEN (it is still capped at
max_techniques), are open.** Candidate R167 frontiers, ranked ambition × feasibility:
(1) **EMBED the unbounded tech space into the LIVE world (TOP AMBITION, still the integration the CEO direction
is about).** Wire `unbounded.TechSpace` into `GenesisWorld` so the OPEN repertoire GATES physical actions and is
SELECTED in the embodied sim — making open-endedness CAUSAL in the living world, not just an analytical model.
Bigger lift: the World uses fixed-width boolean `rep` matrices that the sparse unbounded repertoire breaks —
spike-then-migrate, gated on a real `vr-lead` architectural argument. R166 now gives the motivating data (the
live world's rate accelerates but the bounded tree caps it). (2) **ENDOGENOUS-DEPTH — extend R166 to frontier
DEPTH.** Does the live economy also push max_level (deeper compositions), or only breadth? Add the matched-N
analysis as a first-class panel and test depth-vs-economy. Cheap, deepens R166. (3) **Stage-2 SIGNALLING redesign
(the one parked rung)** — synchronous, sharply lethal predation rounds (Floreano/Mitri arena) where a missed
warning reliably kills; believe emergence only if it beats frozen AND deaf AND causal, ≥3 seeds, red-team. Lean
(1) as the embodied-integration leap (gate the rep-matrix redesign on vr-lead first); (2) is the cheap extension.

**Current ceiling (post-R163): the descent-STRUCTURE rung is CLOSED in BOTH space and time. R160-R162 closed the
SPATIAL phylogeny (cultural cladistics ground-truthed: vertical transmission recovers the birth genealogy,
horizontal does not). R163 closed the TEMPORAL phylogeny: the combinatorial culture's first-appearance HISTORY
recovers the generative tree's time-ladder of cumulative descent (precedence 1.0 + level<->time corr 0.94, 2/2
seeds, red-teamed CONFIRMED 6/6) while the additive null scrambles it and asocial never climbs. The sharpest lesson:
cumulative culture is defined by the STRUCTURE of its history (temporal order), not by depth/breadth magnitude (the
additive null reaches the whole pool faster, but in scrambled order). The durable INSTRUMENTS (`track_tech_history`,
`phylogeny.temporal_ladder_signal`, `temporal_phylogeny_test`) validate any future cumulative-descent claim.**
Candidate R164 frontiers, ranked ambition × feasibility:
(1) **GENUINELY UNBOUNDED / generative tech space (TOP PICK — true open-endedness).** Lift the `max_techniques` cap:
a new technique IS the hashed pair of its parents (combinations of combinations), with bounded memory via a hashed
id pool, so the frontier DEPTH can climb without an artificial ceiling. Pair it with the R163 temporal-ladder + a
max-depth complexity metric that PROVABLY keeps climbing (vs the additive/asocial nulls) and does NOT saturate at a
cap. This is the genuine open-endedness rung and directly reuses the R163 instrument. (2) **Phylorate / innovation
dynamics** — measure the ACCELERATION of the frontier (discovery rate ∝ adjacent-possible size) and whether it is
super-linear (Kauffman/Arthur expanding adjacent possible) vs the additive null's deceleration; a temporal
read-out on top of R163. (3) **Sharpen the spatial descent recovery to HIGH magnitude** (lower-priority, rung
closed). Lean (1).

**Current ceiling (post-R162): the descent-recovery rung is CLOSED with a clean POSITIVE. R160 showed the cultural
divergence is tree-SHAPED; R161 ground-truthed it (honest negative — the tree-shaped cladogram does NOT recover the
true genealogy under default oblique transmission on the ecological substrate, ≈ the label-null = ecological
homoplasy not ancestry); R162 removed both confounds (NEUTRAL substrate `spatial_tiers=False` → lineage drift not
convergence; `tier0_frac=0.80` lifeline → vertical-only keeps all ~27 demes alive → full Mantel power) and got the
gold-standard result: in a neutral-drift world, VERTICAL transmission RECOVERS the true genealogy (Mantel mean
0.366, sig 3/4) while HORIZONTAL copying does NOT (mean 0.054, sig 0/4 ≈ null) EVEN THOUGH both are spatially
local — and a PARTIAL Mantel (control for space, ~0.34 sig 3/4) rules out isolation-by-distance. VERT>HORIZ 4/4.
Honest caveat: magnitude MODEST (~0.37; homoplasy from parallel innovation + movement mixing). The durable
INSTRUMENTS (`genealogy.py` incl. `partial_mantel_test`, `genealogy_phylogeny_test`, `vertical_only`) validate any
future descent-recovery claim.** Candidate R163 frontiers, ranked ambition × feasibility:
(1) **TEMPORAL phylogeny / open-ended complexity (TOP PICK — the Stage-5 rung).** Snapshot the population's
repertoire over a LONG run and reconstruct the TIME-ladder of cumulative descent against the LOGGED genealogy (now
ground-truth-validated by R162), and define an OPEN-ENDED cumulative-complexity metric (deepest reachable technique
level / frontier breadth / total information carried) that keeps CLIMBING vs an asocial/no-transmission null and
plateaus without culture. This is the genuine open-endedness rung and it reuses the R161/R162 genealogy log directly.
(2) **GENUINELY UNBOUNDED / generative tech space** — lift the `max_techniques` cap; a new technique IS the pair
of its parents (combinations of combinations), bounded memory via a hashed id pool + a max-depth complexity
metric that provably climbs. Pairs naturally with (1)'s open-ended metric. (3) **Sharpen the descent recovery to
HIGH magnitude** (lower-priority, the rung is already closed) — reduce homoplasy (innov_steps→0 pure copying, or
lower movement/dispersal so demes are tighter lineages) to push Mantel toward ~1; diminishing returns vs (1)/(2).
Lean (1). The R160 phylogeny + R161/R162 genealogy
modules/metrics are committed and reusable.

### PARKED (post-R159): the Stage-4 ECONOMY is twice-confirmed CAUSALLY INERT on this substrate's population.
**The decisive lesson is a hard substrate FACT, not a design hint:
on this substrate the population carrying capacity is INTRINSIC (foraging/lifespan/world-size), invariant to
food supply across food_regrow 7× and food_cap 8× (pop=900 even at 3.2× the food count). No economy — whether it
redistributes energy or unlocks wasted food — can move a ceiling that food never set.** This kills the "couple
trade to a relaxable constraint" plan as long as that constraint is FOOD: it isn't binding. Candidate R160
frontiers, ranked ambition × feasibility:
(1) **CULTURAL PHYLOGENY / cladistics across generations** (TOP PICK) — independent of the inert economy, this is
the genuine next civilization rung: reconstruct the lineage tree of recipe/technique branches over a long run,
and measure an OPEN-ENDED cumulative-cultural-complexity metric that keeps CLIMBING (vs an asocial / no-
transmission null). Advances the ladder (Stage 5 cumulative culture) without fighting the population invariant.
(2) **MAKE THE POPULATION FOOD-LIMITED BY CONSTRUCTION** (substrate change, gated on a real `vr-lead` argument)
— raise the intrinsic forage ceiling far above food supply (bigger world / cheaper metabolism / relax `max_age`)
so that THEN food becomes the binding constraint and the *already-built* R159 goods economy can finally bind and
raise carrying capacity. Spike-then-migrate; only if the phylogeny rung stalls. (3) **STORAGE / markets across
TIME** — smooth scarcity; but same risk of inertness if the temporal constraint also isn't binding. The R158
trade + R159 goods mechanisms + scramble nulls are committed default-off substrate, reusable once a binding
constraint exists. Lean (1).

### CEO DIRECTION SHIFT (2026-06-20, R140) — GENESIS: a living 3D world that grows a civilization
Yusen steered the loop to a new major frontier: **build a real, alive 3D world that — just by running
locally or in the cloud — freely develops toward a CIVILIZATION, populated by genuinely autonomous
creatures (evolved minds, not scripts).** This is now the STANDING direction; the single-phenomenon
demo arc is retired.

**Progress: GENESIS Stages 1, 3, 4 & 5 COMPLETE — the full ambition ladder is done (Stage 2 signalling parked); now DEEPENING the integration (R153 culture gates diet → R154 multi-axis physical capabilities → R155 costly/bounded capabilities = a SECOND division of labour via the TECH TREE → R156 emergent DIVERGENT cultural TRADITIONS via local transmission, cultural F_ST > panmictic null but MODEST = neutral drift → R157 ECOLOGICALLY-SELECTED traditions: a clean arc — HONEST NEGATIVE (forgetting/`culture_decay` does NOT sharpen drift, it erodes the deep techniques) motivating the POSITIVE (`spatial_tiers` + `recipe_budget`: spatial food niches + forced specialists → selection locks each region to its own branch, region↔branch alignment > scrambled-niche AND position-shuffle nulls 5/5 seeds, red-teamed ROBUST but still MODEST own~0.6 — sharp pure-specialist cultures + inter-group TRADE are the next rungs).** R141 foundation (3D evolved-neural world, behaviour evolves) →
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

### Frontier (post-R151 — capstone RAN; stages INTERACT not sum; what raises the ceiling now)
Current ceiling: every ladder rung was proven IN ISOLATION, and R151 ran them ALL TOGETHER in one world. The
capstone's verdict: the stages do NOT simply sum — they INTERACT, and the integration revealed (a) a real
harvest-payoff correctness collision (fixed; specialize/culture were mutually-exclusive, now multiplicative),
and (b) an emergent SUBSTITUTION — niche-construction hearths (Stage 4) displace the processor caste (Stage 3),
because the built world ripens food and the `building` path replaces the per-agent `_process` action (so the
caste collapses to 0% with hearths, persists at ~60% without; red-teamed ROBUST). Predator arms race +
niche construction + open-ended culture DO coexist alive. The next leaps in KIND:
- **(R152, ATTEMPTED — HONEST NEGATIVE) make Stages 3+4 COMPLEMENT via convex-build + maintenance-wage.** Did
  NOT flip substitution across 3 regimes (food-rich → caste collapses; scarce/fast-decay → ~3% minority only;
  small-reach → world starves). Root cause: shared/accretive/persistent infrastructure is a near-public good a
  tiny minority supplies, so a balanced caste is not the economic equilibrium. To revisit, the fix must make
  the builder's product EXCLUDABLE/individually-captured (a builder OWNS its hearth and gates who eats; or a
  distinct non-substitutable builder-only action), so the wage can't be free-ridden. `build_specialized`
  mechanism stays committed (default off) for that redesign. PARKED (see `## Decisions pending`).
- **(R153, DONE — culture MATTERS PHYSICALLY).** Lifted: techniques now UNLOCK a physical world-action (what an
  agent can EAT) via recipe-locked food tiers — `tech_actions`. Cultural depth physically widens the realized
  diet (social 1→4 tiers / breadth 3.4, asocial locked at 1, 81% food rots), red-teamed ROBUST with the
  energy-injection confound KILLED (~100% of the gap is ACCESS, not payoff). FIRST rung where culture changes
  what agents DO, not a scalar. Next leaps extend this to MORE action axes (below).
- **(R154, DONE — MULTI-AXIS culture-gated capabilities).** Generalised R153's single eat-gate into a
  capability VECTOR: deep tech nodes ALSO unlock LOCOMOTION (higher max speed) + HARVEST REACH (larger eat
  radius) via `tech_capabilities` (combinatorial.capability_techniques; per-agent `_cap_speed`/`_cap_reach`).
  Cultural depth now reshapes the whole physical phenotype — diet + speed + reach. Red-teamed ROBUST: social
  vs asocial realized_axes 2/2 vs 0, speed_cap 5.72 vs 3.00, reach 5.74 vs 3.00, realized_speed 4.61 vs 2.65,
  diet 4 vs 1; asocial EXACTLY at base (categorical); CONFOUND KILLED (cap_speed_mult=0 collapses the speed
  gap to ~10% → ~90% IS the cap, not a health confound). Byte-identical off. NOTE — convergent not divergent:
  with cheap, freely-transmitted capabilities everyone learns ALL axes (no specialization) → R155 below.
- **(R155, DONE — COSTLY/BOUNDED capabilities → emergent SPECIALIZATION).** R154's capabilities were FREE, so
  transmission converged the whole population to the full vector (no division of labour — the R152 convergence).
  R155 makes each capability EXCLUDABLE + BOUNDED: each tech node is the EXCLUSIVE harvesting KEY to one parallel
  food NICHE (`cap_niches`; a free-niche fraction keeps naive founders alive; keyed motes richer), a somatic
  BUDGET (`cap_budget`=1) caps keys held so an agent can't carry every key, and newborns keep the PARENT's key
  first (`_enforce_cap_budget` → heritable profile). Resource depletion → negative frequency dependence → a
  STABLE balanced polymorphism = a division of labour THROUGH the tech tree (attacks the R152 public-good
  negative from the EXCLUDABLE door: a PRIVATE capability, not a free-rideable shared-infra wage). The keys were
  made PURE symmetric niche tools (cap_speed_mult=cap_reach_mult=0) to isolate the niche effect from R154's
  speed/reach bonuses. REAL-VERIFY (scripts/run_genesis_specialize.py, profile-coloured 3D + controls;
  panel.png + specialize.gif EYE-VERIFIED — blue niche-0 and orange niche-1 specialists ~50/50 INTERMIXED, two
  coexisting castes not one converged phenotype): MIXED frac_per_key [0.52,0.48], **profile_entropy 1.00 (the
  MAX for two profiles)**, balance 0.98, mean_keys 1.00 (budget binds). **FREQUENCY-DEPENDENT SELECTION (the
  headline, red-team's decider):** seeded skewed 0.9/0.1 the key fractions are pulled BACK to ~0.5 under REAL
  niches (gap 0.04) but a NEUTRAL control with inert keys (niche_free_frac=1) keeps the initial skew (gap 0.63)
  = a restoring force from excludable niches, not drift. ADAPTIVE: a forced MONOCULTURE (skew=1, cap_force_mono)
  is driven toward EXTINCTION (24 agents, frac_keyed 1.0) while the mixed world holds carrying capacity.
  **RED-TEAM (independent agent): ROBUST.** Claim1 CONFIRMED 5 seeds; Claim3 CONFIRMED via the neutral control
  (selection not drift/seeding); Claim2 direction CONFIRMED & GENUINE (mono keeps key0 throughout and recovers
  when free food is raised → the collapse is wasted niche-1 food, NOT a force_mono key-erosion artifact) — but
  the MAGNITUDE is cap-bound (the niche-partitioned economy rides the `capacity` ceiling), so it is stated as
  "monoculture driven toward extinction", NOT a fixed Nx ratio. No integrity bugs (determinism, budget,
  key-gating, metrics all verified). **HONEST caveat:** the deep capability keys did NOT bootstrap from
  culturally-NAIVE founders in 900 steps — a single deep node has no intermediate selective gradient (the same
  bootstrap-deadlock as Stage-2 signalling), so the DYNAMICS were demonstrated with seeded keys; naive bootstrap
  is the R156 frontier. Byte-identical off. cap_niches=False = R154.
- **(R156, DONE — emergent DIVERGENT cultural TRADITIONS).** A civilization is not one monoculture of knowledge.
  R156 showed the EXISTING substrate grows MANY traditions: oblique transmission copies the NEAREST strong hearth
  (a spatial cultural store), so a region that climbs one BRANCH of the open-ended tree reinforces it locally →
  spatially structured cultures. `tradition_test` = Wright's F_ST over the boolean repertoire across a grid³ of
  demes; causal null `panmictic_culture` (copy a RANDOM hearth) cuts place↔tradition. LOCAL F_ST > panmictic 3/3
  + position-shuffle robust. **HONEST: MODEST (F_ST ~0.03) = neutral drift, not discrete cultures.**
- **(R157, DONE — ECOLOGICALLY-SELECTED traditions; one negative + one positive).** Asked how to SHARPEN R156's
  modest drift. **NEGATIVE: forgetting fails** — `culture_decay` (a decaying per-technique hearth MEMORY, the
  Tasmania/Henrich cultural-loss effect, replacing R156's never-forgetting union) does NOT sharpen drift; uniform
  decay erodes the DEEP techniques that define a tradition (F_ST wash at 0.02, worse at 0.05). Diagnosis: drift in
  a homogeneous world has no maintaining force. **POSITIVE: selection works** — `spatial_tiers` (a recipe-locked
  mote's tier = its x-REGION, so region r yields only branch-r food via R153 tech_actions) + `recipe_budget` (the
  R155 carry-budget on recipes → forced branch SPECIALISTS, not generalists) + a high `tier0_frac` LIFELINE → in
  region r only recipe-r specialists eat the rich food → selection LOCKS each region to its branch. New read-out
  `ecological_traditions_test` (region↔branch ALIGNMENT = own−other frac). REAL-VERIFY: spatial align 0.101 vs
  scrambled-niche null −0.004, 2/2 (+probe 3/3 = 5/5); red-team ROBUST (metric 1.0/0.0; position-shuffle real
  >2σ above floor ~0, 3/3). **HONEST: MODEST (align ~0.05–0.15, own~0.6 — wrong branches still carried);
  `recipe_budget=1` gives sharp pure specialists but CRASHES the pop (bootstrap chicken-and-egg).** All 4 knobs
  (culture_decay/spatial_tiers/recipe_budget/recipe_upkeep) committed default-off byte-identical.
- **(default next, R158 — SHARP cultures, then the civilization leap TRADE).** Two rungs: (a) SHARPEN — let
  `recipe_budget=1` (pure specialists) survive via a gentler/phased bootstrap (rich free tier early, tapered) so
  each region purifies to ONE branch (alignment → ~1, discrete cultures); (b) THE CIVILIZATION LEAP — inter-group
  TRADE/exchange: a recipe-r specialist has a tier-r SURPLUS it can't eat alone and a tier-q DEFICIT, so let
  neighbours of different branches EXCHANGE surplus (a transfer action / shared cache) → an inter-regional economy
  = the first proto-civilization economic structure. Build on `ecological_traditions_test` + `_eat_tech_actions`.
- **(still open) NAIVE BOOTSTRAP of the deep capability keys.** R155 demonstrated the specialization
  DYNAMICS via seeded keys but the keys did not emerge from naive founders (deep node, no gradient). Give
  acquisition a graded ladder so partial cultural depth already pays toward a key (mirror R153's nested tiers
  that bootstrapped), OR let the niche reward scale with proximity-to-key in the tree, so selection can climb to
  the key. Then re-verify the WHOLE chain emerges from a naive start (the strongest possible claim). Build on
  `_eat_cap_niches` + `capability_techniques`.
- **More axes / generative effects:** longer SENSE range (needs threading a per-agent sense_range through all
  sense sites — _sense_food/_sense_neighbours/_sense_predators/_sense_hearths; invasive, deferred), culture-gated
  BUILD types (deep culture raises a taller/longer-lived hearth), new tools. Build on the capability_techniques map.
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
