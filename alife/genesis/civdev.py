"""CIVILIZATION DEVELOPMENT — run the WHOLE living world at once and watch it develop (R168).

R148-R167 validated each civilization mechanism in ISOLATION (niche construction / processing / cumulative
combinatorial culture / tech-gated diet tiers / culture-gated physical capabilities / demes & traditions /
the structural depth of the tech DAG). The R160-R167 arc then drifted into increasingly abstract analysis of
those mechanisms on standalone registry models. This module does the integration the arc had deferred: it
turns ON the full stack TOGETHER in a single persistent `GenesisWorld` and logs the civilization-level
signals that only appear when the whole machine runs — so the world can be RENDERED and WATCHED developing,
which is the CEO's actual deliverable ("just by running, freely develops toward a civilization").

It owns no new simulation mechanism. `civ_config` is the canonical full-stack regime (the same viable
building + combinatorial-culture + tech-actions + tech-capabilities regime the R154 capabilities driver
established, factored out so the test and the driver share ONE definition). `develop_trajectory` is a
read-only observer over `world.step()` + `world.snapshot()` + the society repertoire (no extra RNG, no state
change) that records, per logged step, BOTH the structural depth of the technology (R167 `connected_depth` /
`closure`) AND the EMBODIED civilization signals the abstract arc could not see: how many physical capability
axes the culture has unlocked (`realized_axes`), how many food tiers the population can actually eat
(`edible_tiers`), population, lineage diversity, and descent depth. `capability_color` maps each living agent
to a colour by its realized capability breadth, so the 3D render SHOWS deep-culture agents emerging.

The falsifiable headline (red-teamed by the driver): under the full stack with social learning + evolution
the civilization DEVELOPS — connected tech depth and realized capability axes CLIMB over a long run — whereas
an ASOCIAL control (`learn=False`, no inter-generational transmission) cannot accumulate and stays shallow.
Same world, same physics, the SAME per-lifetime innovation budget; the only change is whether culture is
transmitted. This is Tomasello's ratchet, not a rigged null.

HONEST CAVEAT (red-team R168, baked in): the asocial control's floor (connected depth 0, society breadth ==
n_seed_tech) is structural at the SHARED `innov_steps=1` — an agent born with an empty repertoire makes one
discovery from its adjacent possible (the seeds), and a level-1 technique needs TWO prerequisites held at
once, which one lifetime's innovation cannot reach. It is NOT that innovation is switched off: with a generous
per-lifetime budget the SAME asocial world DOES develop (innov_steps=30 -> connected depth ~8, both capability
axes). So the load-bearing claim is precisely "at a MATCHED per-lifetime innovation budget, cumulative depth
requires social TRANSMISSION" (generation N+1 must start where N left off) — fair because both arms share
`civ_config`'s `innov_steps=1`, NOT "asocial agents cannot innovate at all."
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from alife.genesis import techdepth
from alife.genesis.genesis import GenesisConfig, GenesisWorld
from alife.world3d import World3D

# base phenotype (no capability nodes) -> full physical capability (deep culture), for the 3D render.
_LOCKED = np.array([0.42, 0.13, 0.62])    # violet
_UNLOCKED = np.array([1.0, 0.80, 0.10])   # gold


def civ_config(**kw) -> GenesisConfig:
    """The canonical full-stack civilization regime: niche construction (building/processing) + cumulative
    combinatorial culture + tech-gated diet tiers + culture-gated physical capabilities. The single source of
    truth shared by the unit test and the driver. `learn=False` turns it into the asocial control."""
    base = dict(
        processing=True, building=True, culture=True, combinatorial=True,
        max_techniques=2000, n_seed_tech=6, innov_steps=1,
        hearth_reach_per_strength=3.0, hearth_radius=12.0,
        tech_actions=True, n_food_tiers=4, recipe_level_step=1, tier_value_bonus=2.0, tier0_frac=0.7,
        tech_capabilities=True, n_capabilities=2, cap_level_step=2,
        food_cap=1200, food_regrow=70, capacity=2000,
    )
    base.update(kw)
    return replace(GenesisConfig(world=World3D(size=100.0), n0=600), **base)


def capability_color(world: GenesisWorld) -> np.ndarray:
    """Per living agent (prey only): colour by REALIZED capability breadth — how many physical capability axes
    its culture has unlocked (0 -> violet base phenotype, 1 -> gold full capability)."""
    act = world.pop.active()
    if act.size == 0:
        return np.zeros((0, 3))
    held = world.rep[np.ix_(act, world._cap_tech)].sum(axis=1)        # 0..n_capabilities
    frac = (held / max(world.cfg.n_capabilities, 1))[:, None]
    return _LOCKED * (1.0 - frac) + _UNLOCKED * frac


def develop_trajectory(world: GenesisWorld, steps: int, every: int = 25) -> dict:
    """Drive a full-stack `GenesisWorld` for `steps` steps, logging the civilization-development signals every
    `every` steps. READ-ONLY on the world (world.step() + snapshot() + repertoire union only; no new RNG, no
    state change). Returns arrays keyed:
        step, population, conn_depth, closure, breadth, realized_axes, edible_tiers, diversity, max_gen.
    `conn_depth`/`closure`/`breadth` = the R167 structural-depth view of the society's technology;
    `realized_axes` = mean physical capability axes unlocked (snapshot 'realized_axes');
    `edible_tiers`   = mean food tiers the population can actually eat (snapshot 'mean_edible_tiers')."""
    pa, pb, level = world._tree_pa, world._tree_pb, world._tree_level
    n_seed = world.cfg.n_seed_tech
    log: dict[str, list] = {k: [] for k in (
        "step", "population", "conn_depth", "closure", "breadth",
        "realized_axes", "edible_tiers", "diversity", "max_gen")}
    for s in range(steps):
        world.step()
        if s % every:
            continue
        snp = world.snapshot()
        known = techdepth.society_repertoire(world)
        log["step"].append(s)
        log["population"].append(float(snp["population"]))
        log["conn_depth"].append(techdepth.connected_depth(known, pa, pb, level, n_seed))
        log["closure"].append(techdepth.closure_fraction(known, pa, pb, n_seed))
        log["breadth"].append(int(known.sum()))
        log["realized_axes"].append(float(snp.get("realized_axes", float("nan"))))
        log["edible_tiers"].append(float(snp.get("mean_edible_tiers", float("nan"))))
        log["diversity"].append(float(snp["diversity"]))
        log["max_gen"].append(float(snp["max_gen"]))
    return {k: np.asarray(v) for k, v in log.items()}


def develop_vs_control(steps: int, seed: int, every: int = 25) -> dict:
    """The red-team measurement, one seed: the full-stack civilization (social learning + evolution) vs the
    ASOCIAL control (`learn=False`). Returns {full, control} develop_trajectory dicts. One sim at a time."""
    full = develop_trajectory(GenesisWorld(civ_config(learn=True), seed=seed, evolve=True), steps, every)
    ctrl = develop_trajectory(GenesisWorld(civ_config(learn=False), seed=seed, evolve=True), steps, every)
    return {"full": full, "control": ctrl}
