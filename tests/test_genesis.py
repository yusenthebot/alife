"""R141 — GENESIS foundation: a persistent 3D living world with evolved-neural agents.

These tests pin the substrate invariants. The headline 'behaviour genuinely evolves' claim is
proven by the long REAL-VERIFY run (scripts/run_genesis.py) + the frozen-genome control, not by a
unit test; test_evolution_beats_frozen_control is the fast smoke version.
"""

import os
import re
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from alife import genesis as genesis_pkg
from alife.genesis import metrics
from alife.genesis.agents import PopConfig, Population
from alife.genesis.genesis import GenesisConfig, GenesisWorld
from alife.world3d import World3D


def fast_cfg(**kw):
    base = GenesisConfig(world=World3D(size=90.0), capacity=900, n0=150,
                         food_cap=160, food_regrow=7, persist_steps=50)
    return replace(base, **kw)


# ---------- agent pool ----------
def test_pool_alloc_and_kill_reuse_slots():
    p = Population(PopConfig(capacity=10, n_weights=4))
    a = p.alloc(6)
    assert a.size == 6 and p.n_alive == 6
    p.kill(a[:2])
    assert p.n_alive == 4
    b = p.alloc(5)                       # 4 free slots (2 reused + 4 never used = 6 free) -> 5 fit
    assert b.size == 5 and p.n_alive == 9
    assert p.alloc(100).size == 1        # only 1 slot left, never exceeds capacity
    assert p.n_alive == 10


# ---------- world runs & conserves the pool ----------
def test_world_runs_and_conserves_pool():
    w = GenesisWorld(fast_cfg(), seed=1)
    for _ in range(500):
        w.step()
    p = w.pop
    assert p.n_alive <= p.capacity                      # never exceeds capacity
    assert p.n_alive > 0                                # not extinct
    act = p.active()
    assert np.isfinite(p.pos[act]).all() and np.isfinite(p.vel[act]).all()
    assert np.isfinite(p.energy[act]).all()
    assert (p.pos[act] >= 0).all() and (p.pos[act] <= w.cfg.world.size).all()


# ---------- metabolism kills an agent that never eats ----------
def test_metabolism_kills_idle_agents():
    # no food at all -> nobody can eat -> everyone starves (and nobody reproduces)
    w = GenesisWorld(fast_cfg(food_cap=0, food_regrow=0, n0=60), seed=2)
    start = w.pop.n_alive
    assert start == 60
    for _ in range(600):
        w.step()
    assert w.pop.n_alive == 0                            # starvation works


# ---------- reproduction is kin-adjacent, mutated, lineage-preserving ----------
def test_reproduction_is_kin_adjacent_and_mutates():
    w = GenesisWorld(fast_cfg(n0=8), seed=3)
    p = w.cfg
    pop = w.pop
    parent = pop.active()[0]
    pop.energy[parent] = p.e_repro + 20.0               # force exactly one eligible parent
    before_alive = pop.alive.copy()
    before_e = pop.energy[parent]
    before_brain = pop.brains[parent].copy()
    w._reproduce()
    child = np.where(pop.alive & ~before_alive)[0]
    assert child.size == 1                               # exactly one birth
    c = child[0]
    assert np.linalg.norm(pop.pos[c] - pop.pos[parent]) <= 6 * p.birth_jitter   # spawned beside parent
    assert pop.lineage[c] == pop.lineage[parent]         # bloodline copied
    assert pop.generation[c] == pop.generation[parent] + 1
    assert abs(pop.energy[parent] - before_e * 0.5) < 1e-9   # parent energy halved
    assert abs(pop.energy[c] - before_e * 0.5) < 1e-9        # 50/50 split
    assert not np.array_equal(pop.brains[c], before_brain)   # child brain mutated
    assert np.abs(pop.brains[c]).max() <= 6.0 + 1e-9         # within W_CLIP


# ---------- food, not the pop cap, limits the population ----------
def test_food_limits_population_not_cap():
    # default world scale (the regime where the food economy is real). Observed (1800 steps, seed 0):
    # regrow 10 -> ~1110 agents, regrow 40 -> ~4500, capacity 6000 -> food is the limiter, not the cap.
    lean = GenesisWorld(replace(GenesisConfig(), food_regrow=10), seed=0)
    rich = GenesisWorld(replace(GenesisConfig(), food_regrow=40), seed=0)
    for _ in range(1800):
        lean.step(); rich.step()
    cap = GenesisConfig().capacity
    assert 0 < lean.pop.n_alive < cap                    # bounded well below capacity
    assert 0 < rich.pop.n_alive < cap
    assert rich.pop.n_alive > 1.5 * lean.pop.n_alive     # more food -> larger carrying capacity


# ---------- no fitness function, no scripted movement ----------
def test_no_fitness_function_no_scripting():
    src = Path(genesis_pkg.genesis.__file__).read_text()
    body = "\n".join(l for l in src.splitlines() if not l.strip().startswith(('"', "#")))
    assert "brain.forward(" in body                      # movement comes from the evolved brain
    assert "reward" not in body.lower()                  # no reward signal anywhere
    # the ONLY place velocity is assigned for living agents is the brain-driven _act output
    assert re.search(r"newvel\s*=\s*_act\(", body)
    assert "_next_gen" not in body and "elite" not in body.lower()   # no GA / truncation selection


# ---------- the core claim, in miniature: evolution beats a frozen genome ----------
def test_evolution_beats_frozen_control():
    # Needs population scale (the signal is ~0 at small N). Default world, deterministic seed.
    # Observed @2400 steps: evolve ~0.128, frozen ~0.082 (the full claim is the long REAL-VERIFY run).
    def directedness_end(evolve):
        w = GenesisWorld(GenesisConfig(), seed=0, evolve=evolve)
        vals = []
        for s in range(2400):
            w.step()
            if s >= 1700 and s % 200 == 0:
                vals.append(w.snapshot()["directedness"])
        return float(np.mean(vals))

    evo = directedness_end(True)
    frozen = directedness_end(False)
    assert evo > 0.10                                    # evolved foragers clearly steer at food
    assert evo > frozen + 0.03                           # evolution beats the frozen-genome control


# ---------- the complexity instrument: persistence filter rejects drift ----------
def test_persistence_metric_filters_drift():
    active = np.array([0, 0, 0, 1, 1, 1], dtype=np.int32)   # two equally-abundant lineages
    first = {0: 0, 1: 50}
    # at step 100, persist=60: lineage 0 (age 100) counts, lineage 1 (age 50) is too young
    assert metrics.effective_lineages(active, first, current_step=100, persist_steps=60) == pytest.approx(1.0)
    # at step 200 both are old enough -> effective number 2.0 (even split)
    assert metrics.effective_lineages(active, first, current_step=200, persist_steps=60) == pytest.approx(2.0)
    assert metrics.effective_lineages(active, first, current_step=10, persist_steps=60) == 0.0


def test_directedness_metric_signs():
    # straight at the food -> +1; straight away -> -1
    pos = np.zeros((1, 3))
    food = np.array([[10.0, 0.0, 0.0]])
    assert metrics.food_directedness(pos, np.array([[1.0, 0, 0]]), food, 32.0) == pytest.approx(1.0)
    assert metrics.food_directedness(pos, np.array([[-1.0, 0, 0]]), food, 32.0) == pytest.approx(-1.0)
    assert metrics.food_directedness(pos, np.array([[1.0, 0, 0]]), np.zeros((0, 3)), 32.0) == 0.0


# ---------- checkpoint / resume is exact (cloud / multi-day safe) ----------
def test_checkpoint_roundtrip(tmp_path):
    cfg = fast_cfg()
    a = GenesisWorld(cfg, seed=5)
    for _ in range(200):
        a.step()
    ckpt = str(tmp_path / "g.npz")
    a.save_checkpoint(ckpt)
    b = GenesisWorld(cfg, seed=999)          # different seed; load must overwrite everything
    b.load_checkpoint(ckpt)
    assert b.step_count == a.step_count
    assert np.array_equal(b.pop.alive, a.pop.alive)
    aa, bb = a.pop.active(), b.pop.active()
    assert np.array_equal(aa, bb)
    assert np.array_equal(a.pop.pos[aa], b.pop.pos[bb])
    assert np.array_equal(a.pop.brains[aa], b.pop.brains[bb])
    assert np.array_equal(a.food, b.food)
    for _ in range(60):                       # resumed run must track the uninterrupted one exactly
        a.step(); b.step()
    assert np.array_equal(a.pop.active(), b.pop.active())
    assert np.allclose(a.pop.pos[a.pop.active()], b.pop.pos[b.pop.active()])


# ---------- R142: resource partitioning breaks the monoculture ----------
def test_diet_diversity_metric():
    # two equally-occupied niches -> effective number 2; one niche -> 1; single resource (K<=1) -> 1
    assert metrics.diet_diversity(np.array([0.0, 0.1, 1.9, 2.0]), 3) == pytest.approx(2.0)
    assert metrics.diet_diversity(np.array([1.0, 1.1, 0.9]), 3) == pytest.approx(1.0)
    assert metrics.diet_diversity(np.array([0.5, 1.5]), 1) == 1.0
    assert metrics.diet_diversity(np.zeros(0), 3) == 0.0


def test_typed_agents_eat_only_their_type():
    # an agent eats food of its OWN diet type, gains nothing from a mismatched type (the trade-off)
    w = GenesisWorld(replace(fast_cfg(n0=1), n_food_types=2), seed=0)
    a = w.pop.active()[0]
    w.pop.diet[a] = 0.0                                   # this agent eats type 0
    w.pop.energy[a] = 50.0
    w.food = np.array([w.pop.pos[a]])                     # one mote exactly on the agent
    w.food_type = np.array([1], dtype=np.int64)           # ...but it is type 1 (wrong)
    w.food_ripe = np.array([True]); w.ripe_age = np.zeros(1, dtype=np.int32)
    w.food_proc = np.full(1, -1, dtype=np.int64); w.food_tier = np.zeros(1, dtype=np.int64)
    w._eat()
    assert w.pop.energy[a] == 50.0                        # mismatched type -> no food gained
    w.food = np.array([w.pop.pos[a]]); w.food_type = np.array([0], dtype=np.int64)
    w.food_ripe = np.array([True]); w.ripe_age = np.zeros(1, dtype=np.int32)
    w.food_proc = np.full(1, -1, dtype=np.int64); w.food_tier = np.zeros(1, dtype=np.int64)
    w._eat()
    assert w.pop.energy[a] == 50.0 + w.cfg.food_value     # matching type -> eats


def test_resource_partitioning_maintains_diversity():
    # K=1 collapses to one strategy; K=3 sustains coexisting diet niches (observed diet_div ~3.0).
    one = GenesisWorld(replace(GenesisConfig(), n_food_types=1), seed=0)
    three = GenesisWorld(replace(GenesisConfig(), n_food_types=3), seed=0)
    for _ in range(2500):
        one.step(); three.step()
    assert one.snapshot()["diet_diversity"] == 1.0        # single resource -> one niche
    assert three.snapshot()["diet_diversity"] > 2.5       # three resources -> ~3 coexisting niches
    assert three.snapshot()["directedness"] > 0.05        # foraging still evolves under partitioning


def test_diet_is_heritable_and_mutates():
    w = GenesisWorld(replace(fast_cfg(n0=8), n_food_types=3), seed=1)
    pop = w.pop
    parent = pop.active()[0]
    pop.diet[parent] = 1.0
    pop.energy[parent] = w.cfg.e_repro + 20.0
    before = pop.alive.copy()
    w._reproduce()
    child = np.where(pop.alive & ~before)[0][0]
    assert abs(pop.diet[child] - 1.0) < 0.6               # inherits near parent's diet, slightly mutated
    assert 0.0 <= pop.diet[child] < 3.0                   # stays in range


# ---------- R143: co-evolutionary predator arms race ----------
def test_predators_off_is_prey_only():
    # default (n_predators0=0) is the R141/R142 prey-only world: no predator pop, prey brain n_in=9
    w = GenesisWorld(fast_cfg(), seed=0)
    assert w.pred is None and w.has_predators is False
    assert w.spec.n_in == 9
    assert w.snapshot()["predators"] == 0.0 and w.snapshot()["flee"] == 0.0


def test_predators_on_adds_sense_channel():
    w = GenesisWorld(replace(fast_cfg(), n_predators0=10), seed=0)
    assert w.pred is not None and w.has_predators
    assert w.spec.n_in == 13                              # food4 + neighbour4 + predator4 + energy1
    assert w.pred.n_alive == 10


def test_predator_catch_kills_prey_and_feeds():
    w = GenesisWorld(replace(fast_cfg(n0=4), n_predators0=2), seed=0)
    prey0 = w.pop.active()[0]
    pred0 = w.pred.active()[0]
    w.pred.pos[pred0] = w.pop.pos[prey0].copy()           # predator sitting on a prey, in catch range
    w.pred.cooldown[pred0] = 0
    e_before = w.pred.energy[pred0]
    n_prey_before = w.pop.n_alive
    w._pred_catch()
    assert w.pop.n_alive == n_prey_before - 1             # the prey was caught
    assert not w.pop.alive[prey0]                          # ...that specific prey
    assert w.pred.energy[pred0] == e_before + w.cfg.prey_energy_value
    assert w.pred.cooldown[pred0] == w.cfg.pred_handling   # now digesting


def test_predator_prey_coexist():
    # both species persist over a medium run (no extinction) — a living ecology, not a wipeout
    w = GenesisWorld(replace(GenesisConfig(), n_predators0=120), seed=0)
    for _ in range(3000):
        w.step()
    assert w.pop.n_alive > 0                               # prey not wiped out
    assert w.pred.n_alive > 0                              # predators not starved out


# ---------- R144: emergent signalling channel ----------
def test_signalling_off_is_byte_identical():
    # signalling=False keeps the R143 brain shape and adds no dynamics: two runs match bit-for-bit,
    # and the utterance state stays exactly zero (no extra RNG draws, no channel).
    a = GenesisWorld(replace(fast_cfg(), n_predators0=10), seed=3)
    b = GenesisWorld(replace(fast_cfg(), n_predators0=10), seed=3)
    for _ in range(120):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos) and np.array_equal(a.pop.vel, b.pop.vel)
    assert a.spec.n_in == 13 and a.spec.n_out == 3        # unchanged from R143
    assert np.abs(a.pop.utterance).max() == 0.0           # mute world


def test_signalling_on_adds_channels():
    w = GenesisWorld(replace(fast_cfg(), n_predators0=10, signalling=True, prey_pred_range=12.0), seed=0)
    assert w.spec.n_in == 14                              # food4 + neighbour4 + predator4 + heard1 + energy1
    assert w.spec.n_out == 4                              # 3D accel + 1 utterance
    # without predators the channel still attaches (food-signalling substrate): n_in 9->10
    w2 = GenesisWorld(replace(fast_cfg(), signalling=True), seed=0)
    assert w2.spec.n_in == 10 and w2.spec.n_out == 4


def test_utterance_is_emitted_and_bounded():
    w = GenesisWorld(replace(fast_cfg(n0=120), n_predators0=10, signalling=True, prey_pred_range=12.0), seed=1)
    for _ in range(40):
        w.step()
    act = w.pop.active()
    u = w.pop.utterance[act]
    assert (np.abs(u) > 1e-6).any()                       # somebody is signalling
    assert np.abs(u).max() <= 1.0 + 1e-9                  # tanh-bounded


def test_heard_channel_reads_nearest_neighbour():
    # the heard signal equals the nearest neighbour's last-step utterance, gated to 0 out of range
    w = GenesisWorld(replace(fast_cfg(n0=30), n_predators0=4, signalling=True), seed=2)
    for _ in range(5):
        w.step()
    act = w.pop.active()
    pos = w.pop.pos[act]
    from alife.evolve3d import _body_frame
    r, u, f = _body_frame(w.pop.vel[act])
    ns, ni, nprox = w._sense_neighbours(pos, r, u, f, w.cfg.sense_range)
    heard = w._heard(act, ni, nprox)
    expected = (w.pop.utterance[act][ni] * (nprox > 0)).reshape(-1, 1)
    assert np.allclose(heard, expected)
    assert (heard[nprox == 0] == 0).all()                 # no neighbour in range -> hears silence


def test_newborns_start_mute():
    w = GenesisWorld(replace(fast_cfg(n0=40), n_predators0=4, signalling=True), seed=0)
    w.pop.utterance[:] = 0.7                               # poison every slot, including the free ones
    for _ in range(30):
        w.step()
    # a slot reused by birth must have been reset (not carry the 0.7 from a dead occupant); the only
    # way utterance gets a fresh non-trivial value is via _emit -> values are in [-1,1], never stuck 0.7
    act = w.pop.active()
    assert not np.any(np.isclose(w.pop.utterance[act], 0.7, atol=1e-6) & (w.pop.generation[act] > 0))


def test_causal_listening_test_shape():
    w = GenesisWorld(replace(fast_cfg(n0=120), n_predators0=20, signalling=True, prey_pred_range=12.0), seed=0)
    for _ in range(60):
        w.step()
    out = w.signal_causal_test(np.random.default_rng(0))
    assert {"daccel", "flee_intact", "flee_deaf", "n_alarmed"} <= set(out)
    assert out["daccel"] >= 0.0
    # a mute world (signalling off) returns no causal result
    assert GenesisWorld(replace(fast_cfg(), n_predators0=10), seed=0).signal_causal_test() == {}


# ---------- R144: signal-information metrics ----------
def test_signal_world_mi_detects_coupling():
    rng = np.random.default_rng(0)
    n = 4000
    state = rng.integers(0, 2, n)
    coupled = state + rng.normal(0, 0.05, n)              # signal tracks the state almost perfectly
    randsig = rng.normal(0, 1, n)                         # signal independent of the state
    assert metrics.signal_world_mi(coupled, state, 4) > 0.8     # near the 1-bit ceiling
    assert metrics.signal_world_mi(randsig, state, 4) < 0.02    # ~0
    assert metrics.signal_world_mi(coupled, np.zeros(n, int), 4) == 0.0   # constant state -> undefined -> 0


def test_signal_mi_null_is_a_zero_baseline():
    rng = np.random.default_rng(1)
    n = 4000
    state = rng.integers(0, 2, n)
    coupled = state + rng.normal(0, 0.05, n)
    mean, std = metrics.signal_mi_null(coupled, state, rng, n_bins=4, n_perm=64)
    assert mean < 0.02 and std < 0.02                     # scrambling the labels destroys the information
    assert metrics.signal_world_mi(coupled, state, 4) > mean + 5 * max(std, 1e-9)


def test_danger_state_binary():
    prey = np.array([[0, 0, 0.0], [50, 50, 50.0]])
    pred = np.array([[2, 0, 0.0]])
    assert list(metrics.danger_state(prey, pred, 5.0)) == [1, 0]
    assert metrics.danger_state(prey, np.empty((0, 3)), 5.0).tolist() == [0, 0]


# ---------- R145: kin selection (clonal demes) + honest-signalling cost ----------
def test_clonal_founding_builds_high_relatedness():
    # n_founder_genomes>0 founds the prey as clonal demes: a prey's nearest neighbour is its clone far
    # more often than under the mixed (n0-distinct) founding R144 used.
    mixed = GenesisWorld(replace(fast_cfg(n0=300)), seed=0)
    clonal = GenesisWorld(replace(fast_cfg(n0=300), n_founder_genomes=8, founder_cluster_radius=5.0), seed=0)
    act_m, act_c = mixed.pop.active(), clonal.pop.active()
    r_mixed = metrics.neighbour_relatedness(mixed.pop.pos[act_m], mixed.pop.lineage[act_m])
    r_clonal = metrics.neighbour_relatedness(clonal.pop.pos[act_c], clonal.pop.lineage[act_c])
    assert r_clonal > 0.8 and r_mixed < 0.1                # clones cluster; distinct founders don't
    assert np.unique(clonal.pop.lineage[act_c]).size <= 8  # at most G distinct bloodlines
    # clonemates share a genome at founding (the kin-selection premise)
    for g in np.unique(clonal.pop.lineage[act_c]):
        same = act_c[clonal.pop.lineage[act_c] == g]
        assert np.allclose(clonal.pop.brains[same], clonal.pop.brains[same[0]])


def test_clonal_founding_off_is_byte_identical():
    # the default (n_founder_genomes=0) path must not perturb the R141..R144 RNG order
    a = GenesisWorld(replace(fast_cfg(), n_predators0=10, signalling=True, prey_pred_range=12.0), seed=7)
    b = GenesisWorld(replace(fast_cfg(), n_predators0=10, signalling=True, prey_pred_range=12.0), seed=7)
    for _ in range(60):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos) and np.array_equal(a.pop.brains, b.pop.brains)


def test_emit_cost_charges_loud_signallers():
    # with emit_cost>0 a loud emitter pays more energy than a silent one (honest-signalling cost)
    free = GenesisWorld(replace(fast_cfg(n0=120), n_predators0=8, signalling=True, emit_cost=0.0), seed=1)
    paid = GenesisWorld(replace(fast_cfg(n0=120), n_predators0=8, signalling=True, emit_cost=0.5), seed=1)
    for _ in range(3):
        free.step(); paid.step()
    # force a known loud utterance, then step once: the paid world must debit emit_cost*|u| extra energy
    for w in (free, paid):
        act = w.pop.active()
        w.pop.utterance[act] = 0.0
    fa, pa = free.pop.active(), paid.pop.active()
    e_free0, e_paid0 = free.pop.energy.copy(), paid.pop.energy.copy()
    # identical worlds at this point (same seed/draws) -> compare the energy debit after one step
    free.step(); paid.step()
    assert paid.cfg.emit_cost > free.cfg.emit_cost
    # paid world's mean energy should be <= free world's (loud signallers bled extra)
    assert paid.pop.energy[paid.pop.active()].mean() <= free.pop.energy[free.pop.active()].mean() + 1e-9


def test_neighbour_relatedness_bounds():
    pos = np.array([[0, 0, 0.0], [1, 0, 0], [40, 40, 40], [41, 40, 40]])
    lin_kin = np.array([5, 5, 9, 9])                       # each nearest neighbour is same-lineage
    lin_mix = np.array([0, 1, 2, 3])                       # all distinct
    assert metrics.neighbour_relatedness(pos, lin_kin) == 1.0
    assert metrics.neighbour_relatedness(pos, lin_mix) == 0.0


# ---------- R146: division of labour (two-stage food processing) ----------
def test_processing_off_is_byte_identical():
    # processing=False keeps the R141..R145 brain shape and all-edible food: two runs match bit-for-bit
    a = GenesisWorld(fast_cfg(), seed=3)
    b = GenesisWorld(fast_cfg(), seed=3)
    for _ in range(150):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos) and np.array_equal(a.pop.brains, b.pop.brains)
    assert a.spec.n_in == 9 and a.spec.n_out == 3            # unchanged
    assert a.food_ripe.all()                                 # all food edible (no raw state)


def test_processing_on_adds_channels_and_raw_food():
    w = GenesisWorld(fast_cfg(processing=True), seed=0)
    assert w.processing and w.spec.n_in == 13                # +nearest-raw-food sense (4)
    assert w.spec.n_out == 4                                 # +process gate
    assert not w.food_ripe.any()                             # food spawns RAW (inedible until ripened)
    # processing assumes a single food type
    with pytest.raises(ValueError):
        GenesisWorld(fast_cfg(processing=True, n_food_types=3), seed=0)


def test_only_ripe_food_is_edible():
    w = GenesisWorld(fast_cfg(n0=1, processing=True), seed=0)
    a = w.pop.active()[0]
    w.pop.energy[a] = 50.0
    w.food = np.array([w.pop.pos[a]])                        # one mote exactly on the agent
    w.food_type = np.zeros(1, dtype=np.int64)
    w.ripe_age = np.zeros(1, dtype=np.int32)
    w.food_proc = np.full(1, -1, dtype=np.int64); w.food_tier = np.zeros(1, dtype=np.int64)
    w.food_ripe = np.array([False])                          # raw -> not edible
    w._eat()
    assert w.pop.energy[a] == 50.0
    w.food_ripe = np.array([True])                           # ripe -> edible
    w._eat()
    assert w.pop.energy[a] == 50.0 + w.cfg.food_value


def test_process_ripens_raw_food_and_charges_cost():
    w = GenesisWorld(fast_cfg(n0=1, processing=True), seed=0)
    a = w.pop.active()[0]
    w.pop.energy[a] = 50.0
    # two raw motes within process_radius, one far away
    base = w.pop.pos[a]
    w.food = np.array([base + [1.0, 0, 0], base + [2.0, 0, 0], base + [60.0, 0, 0]])
    w.food_type = np.zeros(3, dtype=np.int64)
    w.food_ripe = np.zeros(3, dtype=bool)
    w.ripe_age = np.zeros(3, dtype=np.int32)
    act = w.pop.active()
    out = np.zeros((act.size, w.spec.n_out))
    out[:, w._proc_out] = 1.0                                # force the process gate ON
    w._process(act, out)
    assert w.food_ripe[0] and w.food_ripe[1]                 # nearby raw food ripened (public good)
    assert not w.food_ripe[2]                                # the far mote stays raw
    assert w.pop.energy[a] == 50.0 - w.cfg.process_cost      # the processor paid the labour cost


def test_ripe_food_decays_back_to_raw():
    w = GenesisWorld(fast_cfg(processing=True, ripe_ttl=5), seed=0)
    w.food_ripe[:] = True
    w.ripe_age[:] = 0
    for _ in range(4):
        w._decay_ripe()
    assert w.food_ripe.all()                                 # not yet expired
    w._decay_ripe()
    assert not w.food_ripe.any()                             # ttl reached -> reverts to raw (a flow)


def test_processing_world_sustains_population():
    # the two-stage economy closes: processors ripen food, harvesters eat it, the population persists.
    # (full-diversity founding — the clonal-deme founding starves in the bootstrap with only 8 genomes.)
    w = GenesisWorld(replace(GenesisConfig(), processing=True), seed=2)
    for _ in range(1500):
        w.step()
    assert w.pop.n_alive > 50                                # not extinct — the labour economy sustains life
    assert w.food_ripe.any()                                 # ripe food is being produced


def test_point_biserial_metric():
    rng = np.random.default_rng(0)
    g = rng.integers(0, 2, 500).astype(float)
    x_neg = -g + rng.normal(0, 0.1, 500)                     # x falls when group=1
    assert metrics.point_biserial(x_neg, g) < -0.8
    assert abs(metrics.point_biserial(rng.normal(0, 1, 500), g)) < 0.2   # independent -> ~0
    assert metrics.point_biserial(np.ones(500), g) == 0.0    # no variance -> 0


def test_allocation_test_shape():
    w = GenesisWorld(replace(fast_cfg(n0=200), processing=True, n_founder_genomes=6), seed=0)
    for _ in range(60):
        w.step()
    out = w.process_allocation_test()
    assert {"frac_processing", "cond_ripe", "cond_raw", "n"} <= set(out)
    assert 0.0 <= out["frac_processing"] <= 1.0
    # a non-processing world returns no allocation result
    assert GenesisWorld(fast_cfg(), seed=0).process_allocation_test() == {}


# ---------- 3D render smoke (headless moderngl) ----------
def test_render_smoke():
    from alife.world3d import World3D as W3
    w = GenesisWorld(fast_cfg(n0=80), seed=4)
    for _ in range(10):
        w.step()
    pos, vel, color, food = w.render_arrays()
    try:
        from alife.render3d import Renderer3D
        r = Renderer3D(W3(size=w.cfg.world.size), width=160, height=120)
        frame = r.render(pos, vel, color, cam_angle=0.6, food=food)
    except Exception as e:                    # no GL context in this env -> skip, not fail
        pytest.skip(f"no GL/render context available: {e}")
    assert frame.shape == (120, 160, 3)
    assert frame.dtype == np.uint8
    assert frame.max() > 0                      # something was drawn


# ---------- R147: caste specialization (convex trade-off -> division of labour) ----------
def test_specialize_requires_processing():
    with pytest.raises(ValueError):
        GenesisWorld(fast_cfg(specialize=True), seed=0)        # no processing substrate -> rejected


def test_specialize_off_is_byte_identical_to_r146():
    # specialize=False over the processing substrate is the exact R146 world: two runs match bit-for-bit,
    # the brain shape is unchanged, and spec stays all-zero (the trait is dormant, draws no RNG).
    a = GenesisWorld(fast_cfg(processing=True), seed=3)
    b = GenesisWorld(fast_cfg(processing=True), seed=3)
    for _ in range(120):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos) and np.array_equal(a.pop.brains, b.pop.brains)
    assert a.spec.n_in == 13 and a.spec.n_out == 4            # R146 shape, no extra channels
    assert not a.pop.spec.any()                               # caste trait dormant


def test_specialize_seeds_standing_caste_variation():
    w = GenesisWorld(fast_cfg(processing=True, specialize=True), seed=1)
    s = w.pop.spec[w.pop.active()]
    assert s.min() >= 0.0 and s.max() <= 1.0
    assert s.std() > 0.2                                      # broad founding spread (uniform), not a point


def test_convex_harvest_gain_penalises_generalists():
    # harvest gain = food_value * (1-spec)^gamma: pure harvester full, generalist quartered, processor ~0
    w = GenesisWorld(fast_cfg(n0=3, processing=True, specialize=True, spec_gamma=2.0), seed=0)
    act = w.pop.active()
    for slot, sp in zip(act[:3], (0.0, 0.5, 1.0)):
        w.pop.spec[slot] = sp
        w.pop.energy[slot] = 50.0
        w.food = np.array([w.pop.pos[slot]])                  # a ripe mote on this agent only
        w.food_type = np.zeros(1, dtype=np.int64)
        w.food_ripe = np.array([True]); w.ripe_age = np.zeros(1, dtype=np.int32)
        w.food_proc = np.full(1, -1, dtype=np.int64); w.food_tier = np.zeros(1, dtype=np.int64); w.food_tier = np.zeros(1, dtype=np.int64)
        w._eat()
    fv = w.cfg.food_value
    assert abs(w.pop.energy[act[0]] - (50.0 + fv)) < 1e-9             # spec 0 -> full value
    assert abs(w.pop.energy[act[1]] - (50.0 + fv * 0.25)) < 1e-9      # spec .5 -> quarter (convex penalty)
    assert abs(w.pop.energy[act[2]] - 50.0) < 1e-9                    # spec 1 -> ~nothing from harvesting


def test_process_reach_scales_with_caste():
    # a high-spec processor ripens a far mote a low-spec one cannot reach (reach = process_radius * spec)
    w = GenesisWorld(fast_cfg(n0=1, processing=True, specialize=True), seed=0)
    a = w.pop.active()[0]
    base = w.pop.pos[a]
    far = w.cfg.process_radius * 0.8                          # within full reach, outside a weak processor's
    w.food = np.array([base + [far, 0, 0]])
    w.food_type = np.zeros(1, dtype=np.int64)
    w.food_ripe = np.zeros(1, dtype=bool); w.ripe_age = np.zeros(1, dtype=np.int32)
    w.food_proc = np.full(1, -1, dtype=np.int64); w.food_tier = np.zeros(1, dtype=np.int64)
    out = np.zeros((1, w.spec.n_out)); out[:, w._proc_out] = 1.0
    w.pop.spec[a] = 0.3                                       # reach 0.3R < 0.8R -> cannot ripen it
    w._process(np.array([a]), out)
    assert not w.food_ripe[0]
    w.pop.spec[a] = 1.0                                       # full reach -> ripens it, and is attributed
    w._process(np.array([a]), out)
    assert w.food_ripe[0] and w.food_proc[0] == a


def test_processor_earns_wage_when_its_food_is_harvested():
    # the trade: a processor that ripened a mote is paid process_payment when a DIFFERENT agent eats it
    w = GenesisWorld(fast_cfg(n0=2, processing=True, specialize=True), seed=0)
    proc, harv = w.pop.active()[:2]
    w.pop.energy[proc] = 40.0; w.pop.energy[harv] = 40.0
    w.pop.spec[harv] = 0.0                                    # full-value harvester
    w.food = np.array([w.pop.pos[harv]])                      # ripe mote on the harvester, ripened by proc
    w.food_type = np.zeros(1, dtype=np.int64)
    w.food_ripe = np.array([True]); w.ripe_age = np.zeros(1, dtype=np.int32)
    w.food_proc = np.array([proc], dtype=np.int64); w.food_tier = np.zeros(1, dtype=np.int64)
    w._eat()
    assert abs(w.pop.energy[harv] - (40.0 + w.cfg.food_value)) < 1e-9   # harvester ate full value
    assert abs(w.pop.energy[proc] - (40.0 + w.cfg.process_payment)) < 1e-9  # processor got its wage


def test_force_generalist_pins_spec_at_half():
    w = GenesisWorld(fast_cfg(processing=True, specialize=True, force_generalist=True), seed=2)
    assert np.allclose(w.pop.spec[w.pop.active()], 0.5)       # founders all generalist
    for _ in range(300):
        w.step()
    assert np.allclose(w.pop.spec[w.pop.active()], 0.5)       # offspring too -> monomorphic control


def test_spec_is_heritable_and_mutates():
    w = GenesisWorld(fast_cfg(n0=8, processing=True, specialize=True), seed=1)
    pop = w.pop
    parent = pop.active()[0]
    pop.spec[parent] = 0.8
    pop.energy[parent] = w.cfg.e_repro + 20.0
    before = pop.alive.copy()
    w._reproduce()
    child = np.where(pop.alive & ~before)[0][0]
    assert abs(pop.spec[child] - 0.8) < 0.5                   # inherits near parent, slightly mutated
    assert 0.0 <= pop.spec[child] <= 1.0


def test_bimodality_metric_separates_two_castes_from_uniform():
    rng = np.random.default_rng(0)
    uniform = rng.uniform(0, 1, 2000)
    normalish = np.clip(rng.normal(0.5, 0.08, 2000), 0, 1)
    two_caste = np.clip(np.concatenate([rng.normal(0.05, 0.04, 1000),
                                        rng.normal(0.95, 0.04, 1000)]), 0, 1)
    assert metrics.bimodality(two_caste) > metrics.bimodality(uniform)
    assert metrics.bimodality(uniform) > metrics.bimodality(normalish)   # uniform > unimodal blob
    assert metrics.bimodality(two_caste) > 0.7                           # near the bimodal ceiling


def test_caste_test_reports_structure_and_determinism():
    a = GenesisWorld(fast_cfg(n0=200, processing=True, specialize=True), seed=0)
    b = GenesisWorld(fast_cfg(n0=200, processing=True, specialize=True), seed=0)
    for _ in range(80):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos) and np.array_equal(a.pop.spec, b.pop.spec)  # determinism
    out = a.caste_test()
    assert {"spec_mean", "bimodality", "frac_specialist", "proc_spec", "harv_spec", "n"} <= set(out)
    assert GenesisWorld(fast_cfg(processing=True), seed=0).caste_test() == {}    # off -> empty


# ---------- niche construction / building (R148, Stage 4) ----------
def _bcfg(**kw):
    return fast_cfg(processing=True, building=True, **kw)


def test_building_requires_processing():
    with pytest.raises(ValueError):
        GenesisWorld(fast_cfg(building=True), seed=0)


def test_building_adds_hearth_sense_channel():
    base = GenesisWorld(fast_cfg(processing=True), seed=0)
    built = GenesisWorld(_bcfg(), seed=0)
    assert built.spec.n_in == base.spec.n_in + 4        # +nearest-hearth sense channel
    assert built.spec.n_out == base.spec.n_out          # build gate REUSES the process-gate output


def test_building_off_is_deterministic_unchanged():
    a = GenesisWorld(fast_cfg(processing=True), seed=4)
    b = GenesisWorld(fast_cfg(processing=True, building=False), seed=4)
    for _ in range(60):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos)          # building=False draws no extra RNG


def test_build_act_founds_then_reinforces_hearth():
    w = GenesisWorld(_bcfg(n0=4), seed=0)
    act = w.pop.active()
    w.pop.pos[act[0]] = np.array([20.0, 20.0, 20.0])
    out = np.zeros((act.size, w.spec.n_out)); out[0, w._proc_out] = 1.0   # agent 0 builds
    w._build(act, out)
    assert w.struct_alive.sum() == 1                     # founded one hearth
    s0 = w.struct_strength[w.struct_alive][0]
    w._build(act, out)                                   # builds again at same spot -> reinforces (within merge)
    assert w.struct_alive.sum() == 1
    assert w.struct_strength[w.struct_alive][0] > s0     # strength accreted, no second hearth


def test_build_far_apart_founds_separate_hearths():
    w = GenesisWorld(_bcfg(n0=4), seed=0)
    act = w.pop.active()
    w.pop.pos[act[0]] = np.array([10.0, 10.0, 10.0])
    w.pop.pos[act[1]] = np.array([70.0, 70.0, 70.0])     # far beyond build_merge_radius
    out = np.zeros((act.size, w.spec.n_out)); out[[0, 1], w._proc_out] = 1.0
    w._build(act, out)
    assert w.struct_alive.sum() == 2


def test_hearths_ripen_only_nearby_raw_food():
    w = GenesisWorld(_bcfg(), seed=0)
    w.struct_pos[0] = np.array([45.0, 45.0, 45.0])
    w.struct_strength[0] = 2.0                            # strong enough to ripen
    w.struct_alive[0] = True
    w.food = np.array([[45.0, 45.0, 47.0],               # within hearth_radius -> ripens
                       [10.0, 10.0, 10.0]])              # far away -> stays raw
    w.food_ripe = np.zeros(2, dtype=bool)
    w.ripe_age = np.zeros(2, dtype=np.int32)
    w._ripen_hearths()
    assert w.food_ripe[0] and not w.food_ripe[1]


def test_weak_hearth_does_not_ripen():
    w = GenesisWorld(_bcfg(), seed=0)
    w.struct_pos[0] = np.array([45.0, 45.0, 45.0])
    w.struct_strength[0] = 0.3                            # below hearth_min_strength
    w.struct_alive[0] = True
    w.food = np.array([[45.0, 45.0, 46.0]])
    w.food_ripe = np.zeros(1, dtype=bool); w.ripe_age = np.zeros(1, dtype=np.int32)
    w._ripen_hearths()
    assert not w.food_ripe[0]                             # a faint deposit is not yet a working hearth


def test_unmaintained_hearth_decays_and_dies():
    w = GenesisWorld(_bcfg(struct_decay=0.1), seed=0)
    w.struct_strength[0] = 0.25; w.struct_alive[0] = True
    for _ in range(3):
        w._decay_structures()
    assert not w.struct_alive[0]                          # 0.25 - 3*0.1 <= 0 -> freed


def test_build_persist_false_wipes_hearths_each_step():
    w = GenesisWorld(_bcfg(build_persist=False), seed=0)
    w.struct_strength[0] = 5.0; w.struct_alive[0] = True
    w._decay_structures()
    assert w.struct_alive.sum() == 0                      # no ecological inheritance in the ablation


def test_clark_evans_clustered_below_uniform():
    rng = np.random.default_rng(0)
    side = 100.0
    uniform = rng.uniform(0, side, size=(300, 3))
    centers = rng.uniform(20, 80, size=(5, 3))
    clustered = centers[rng.integers(0, 5, 300)] + rng.normal(0, 2.0, size=(300, 3))
    assert metrics.clark_evans(clustered, side) < metrics.clark_evans(uniform, side)
    assert metrics.clark_evans(clustered, side) < 1.0    # R<1 = settlements


def test_niche_metrics_inheritance_fields():
    # one old hearth (age 500) with young agents around it -> inherited
    sp = np.array([[50.0, 50.0, 50.0], [10.0, 80.0, 30.0]])
    strength = np.array([3.0, 3.0]); age = np.array([500, 480])
    ap = np.array([[50.0, 50.0, 52.0]] * 30)
    aage = np.full(30, 20)
    out = metrics.niche_metrics(sp, strength, age, ap, aage, 100.0, 7.0, 1.0, mean_agent_lifespan=100.0)
    assert out["n_hearths"] == 2
    assert out["mean_struct_age"] > 100                  # hearths far older than agents
    assert out["inherit_ratio"] > 1.0                    # outlive their builders
    assert out["inherit_frac"] == 1.0                    # every agent's nearest hearth predates it
    assert out["near_frac"] == 1.0


def test_niche_test_runs_and_reports():
    w = GenesisWorld(_bcfg(n0=200), seed=0)
    for _ in range(120):
        w.step()
    out = w.niche_test()
    assert {"n_hearths", "settlement", "mean_struct_age", "inherit_ratio",
            "inherit_frac", "near_frac"} <= set(out)
    assert GenesisWorld(fast_cfg(processing=True), seed=0).niche_test() == {}   # off -> empty


def test_building_world_builds_hearths_under_evolution():
    w = GenesisWorld(_bcfg(n0=200), seed=0)
    for _ in range(200):
        w.step()
    assert w.struct_alive.sum() > 0                       # agents actually deposit hearths to eat
    assert w.pop.n_alive > 0                              # and survive on the world they reshaped


def test_checkpoint_roundtrip_with_hearths(tmp_path):
    w = GenesisWorld(_bcfg(n0=120), seed=1)
    for _ in range(150):
        w.step()
    p = str(tmp_path / "ck.npz")
    w.save_checkpoint(p)
    w2 = GenesisWorld(_bcfg(n0=120), seed=9)
    w2.load_checkpoint(p)
    assert np.array_equal(w.struct_alive, w2.struct_alive)
    assert np.allclose(w.struct_strength, w2.struct_strength)
    assert np.array_equal(w.struct_birth, w2.struct_birth)


# ---------- R152: division of labour AROUND niche construction (builder caste) ----------
def _bscfg(**kw):
    return fast_cfg(processing=True, building=True, specialize=True, build_specialized=True, **kw)


def test_build_specialized_requires_building_and_specialize():
    with pytest.raises(ValueError):
        GenesisWorld(fast_cfg(processing=True, building=True, build_specialized=True), seed=0)   # no specialize
    with pytest.raises(ValueError):
        GenesisWorld(fast_cfg(processing=True, specialize=True, build_specialized=True), seed=0)  # no building


def test_build_specialized_off_is_byte_identical():
    a = GenesisWorld(fast_cfg(processing=True, building=True, specialize=True), seed=5)
    b = GenesisWorld(fast_cfg(processing=True, building=True, specialize=True, build_specialized=False), seed=5)
    for _ in range(80):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos)              # flag off draws no extra RNG, scales nothing
    assert np.allclose(a.struct_strength, b.struct_strength)


def test_build_strength_convex_in_spec():
    w = GenesisWorld(_bscfg(n0=4), seed=0)
    act = w.pop.active()
    w.pop.pos[act[0]] = np.array([15.0, 15.0, 15.0]); w.pop.spec[act[0]] = 1.0   # pure builder
    w.pop.pos[act[1]] = np.array([70.0, 70.0, 70.0]); w.pop.spec[act[1]] = 0.2   # harvester (far -> own slot)
    out = np.zeros((act.size, w.spec.n_out)); out[[0, 1], w._proc_out] = 1.0
    w._build(act, out)
    assert w.struct_alive.sum() == 2
    s_builder = w.struct_strength[w.struct_last_builder == act[0]][0]
    s_harv = w.struct_strength[w.struct_last_builder == act[1]][0]
    assert s_builder > s_harv                                # convex: only the high-spec builder raises a real hearth
    assert s_harv < w.cfg.hearth_min_strength                # 0.2^2 = 0.04 -> a dead ember, ripens nothing
    assert s_builder >= w.cfg.hearth_min_strength


def test_build_specialized_pays_maintainer_wage():
    w = GenesisWorld(_bscfg(n0=4), seed=0)
    act = w.pop.active()
    builder = act[0]
    w.pop.spec[builder] = 1.0
    w.pop.pos[builder] = np.array([45.0, 45.0, 45.0])
    out = np.zeros((act.size, w.spec.n_out)); out[0, w._proc_out] = 1.0
    w._build(act, out)                                       # founds a strong hearth; builder is its maintainer
    h = np.where(w.struct_alive)[0][0]
    assert w.struct_last_builder[h] == builder
    w.food = np.array([[45.0, 45.0, 46.0]])                  # a raw mote within reach of the hearth
    w.food_ripe = np.zeros(1, dtype=bool); w.ripe_age = np.zeros(1, dtype=np.int32)
    w.food_proc = np.full(1, -1, dtype=np.int64); w.food_tier = np.zeros(1, dtype=np.int64)
    w._ripen_hearths()
    assert w.food_ripe[0]
    assert w.food_proc[0] == builder                         # hearth-ripened food credits the maintainer
    e0 = w.pop.energy[builder]
    w._pay_processors(np.array([0]))                         # a harvester eats it -> wage flows to the builder
    assert w.pop.energy[builder] == pytest.approx(e0 + w.cfg.process_payment)


def test_build_specialized_world_survives_and_builds():
    w = GenesisWorld(_bscfg(n0=200), seed=0)
    for _ in range(200):
        w.step()
    assert w.pop.n_alive > 0                                  # the wage economy is viable
    assert w.struct_alive.sum() > 0                           # high-spec builders raise maintained hearths


def test_checkpoint_roundtrip_with_build_specialized(tmp_path):
    w = GenesisWorld(_bscfg(n0=120), seed=1)
    for _ in range(150):
        w.step()
    p = str(tmp_path / "ck.npz")
    w.save_checkpoint(p)
    w2 = GenesisWorld(_bscfg(n0=120), seed=9)
    w2.load_checkpoint(p)
    assert np.array_equal(w.struct_last_builder, w2.struct_last_builder)


# ---------- R149: cumulative culture (Stage 5) ----------
def _ccfg(**kw):
    # a viable building regime (the real-run convex-reach params + denser food) so the population robustly
    # survives even in the asocial / frozen-genome controls — needed to compare the technique level fairly.
    kw.setdefault("n0", 250)
    return _bcfg(culture=True, hearth_reach_per_strength=3.0, hearth_radius=12.0,
                 food_cap=400, food_regrow=18, **kw)


def test_culture_requires_building():
    with pytest.raises(ValueError):
        GenesisWorld(fast_cfg(processing=True, culture=True), seed=0)   # culture without building


def test_culture_off_is_byte_identical_to_r148():
    a = GenesisWorld(_bcfg(n0=200), seed=3)                  # building, no culture
    b = GenesisWorld(_bcfg(n0=200, culture=False), seed=3)
    for _ in range(60):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos)              # culture=False draws no extra RNG, no perturbation


def test_culture_keeps_same_brain_shape_as_building():
    built = GenesisWorld(_bcfg(), seed=0)
    cult = GenesisWorld(_ccfg(), seed=0)
    assert cult.spec.n_in == built.spec.n_in                # tech is automatic, NOT a brain channel/output
    assert cult.spec.n_out == built.spec.n_out


def test_founders_are_culturally_naive():
    w = GenesisWorld(_ccfg(innov_mean=0.15, innov_sigma=0.25), seed=0)
    act = w.pop.active()
    assert w.pop.tech[act].mean() < 0.6                      # ~one innovation step; nothing to copy yet


def test_social_learning_copies_the_best_model():
    w = GenesisWorld(_ccfg(culture_fidelity=1.0, innov_mean=0.0, innov_sigma=0.0), seed=0)
    w.struct_pos[0] = np.array([45.0, 45.0, 45.0])          # a hearth carrying ancestral knowledge tech=10
    w.struct_strength[0] = 2.0; w.struct_tech[0] = 10.0; w.struct_alive[0] = True
    s = w.pop.alloc(1)                                       # a newborn slot in range of the hearth
    w.pop.pos[s] = np.array([45.0, 45.0, 46.0])
    par = w.pop.active()[0]; w.pop.tech[par] = 0.0
    w._acquire_tech(s, np.array([par]))
    assert abs(w.pop.tech[s[0]] - 10.0) < 1e-9              # copied the hearth record (fidelity 1, no innovation)


def test_asocial_control_cannot_copy():
    w = GenesisWorld(_ccfg(learn=False, culture_fidelity=1.0, innov_mean=0.0, innov_sigma=0.0), seed=0)
    w.struct_pos[0] = np.array([45.0, 45.0, 45.0])
    w.struct_strength[0] = 2.0; w.struct_tech[0] = 10.0; w.struct_alive[0] = True
    s = w.pop.alloc(1); w.pop.pos[s] = np.array([45.0, 45.0, 46.0])
    par = w.pop.active()[0]; w.pop.tech[par] = 7.0
    w._acquire_tech(s, np.array([par]))
    assert w.pop.tech[s[0]] < 1e-9                           # base forced to 0 -> reinvents from scratch


def test_fidelity_loses_some_on_copy():
    w = GenesisWorld(_ccfg(culture_fidelity=0.8, innov_mean=0.0, innov_sigma=0.0), seed=0)
    w.struct_pos[0] = np.array([45.0, 45.0, 45.0])
    w.struct_strength[0] = 2.0; w.struct_tech[0] = 10.0; w.struct_alive[0] = True
    s = w.pop.alloc(1); w.pop.pos[s] = np.array([45.0, 45.0, 46.0])
    par = w.pop.active()[0]; w.pop.tech[par] = 0.0
    w._acquire_tech(s, np.array([par]))
    assert abs(w.pop.tech[s[0]] - 8.0) < 1e-9               # 0.8 * 10 = imperfect transmission


def test_build_records_best_technique():
    w = GenesisWorld(_ccfg(n0=4), seed=0)
    act = w.pop.active()
    w.pop.pos[act[0]] = np.array([20.0, 20.0, 20.0]); w.pop.tech[act[0]] = 5.0
    out = np.zeros((act.size, w.spec.n_out)); out[0, w._proc_out] = 1.0
    w._build(act, out)
    assert abs(w.struct_tech[w.struct_alive][0] - 5.0) < 1e-9     # new hearth opens at the founder's tech
    w.pop.tech[act[0]] = 8.0; w._build(act, out)                  # reinforce with a better technique
    assert abs(w.struct_tech[w.struct_alive][0] - 8.0) < 1e-9     # record keeps the MAX
    w.pop.tech[act[0]] = 3.0; w._build(act, out)
    assert abs(w.struct_tech[w.struct_alive][0] - 8.0) < 1e-9     # a worse technique does not lower the record


def test_tech_boosts_harvest_energy():
    w = GenesisWorld(_ccfg(n0=2, tech_gain=0.5), seed=0)
    act = w.pop.active()
    w.pop.pos[act[0]] = np.array([10.0, 10.0, 10.0]); w.pop.tech[act[0]] = 0.0
    w.pop.pos[act[1]] = np.array([60.0, 60.0, 60.0]); w.pop.tech[act[1]] = 4.0
    w.food = np.array([[10.0, 10.0, 10.5], [60.0, 60.0, 60.5]])   # a ripe mote at each agent
    w.food_ripe = np.ones(2, dtype=bool); w.ripe_age = np.zeros(2, dtype=np.int32)
    w.food_proc = np.full(2, -1, dtype=np.int64); w.food_type = np.zeros(2, dtype=np.int64)
    w.food_tier = np.zeros(2, dtype=np.int64)
    e0, e1 = w.pop.energy[act[0]], w.pop.energy[act[1]]
    w._eat()
    g0 = w.pop.energy[act[0]] - e0; g1 = w.pop.energy[act[1]] - e1
    assert g0 > 0 and g1 > 0
    assert abs(g1 - g0 * (1.0 + 0.5 * 4.0)) < 1e-6               # tech 4 harvests 3x the energy of tech 0


def test_culture_is_not_genetic_climbs_with_frozen_genes():
    """The acid test that it's CULTURAL not genetic: with evolve=False the genome can't improve, yet the
    learned technique still ratchets up across generations via social transmission through the built world."""
    w = GenesisWorld(_ccfg(n0=250), seed=0, evolve=False)
    founder = w.pop.tech[w.pop.active()].mean()
    for _ in range(400):
        w.step()
    ct = w.culture_test()
    assert ct and ct["mean_gen"] >= 2                            # generations turned over
    assert ct["tech_mean"] > founder + 0.3                       # technique accumulated though genes are frozen


def test_cumulative_beats_asocial_smoke():
    """Headline smoke: WITH social learning the technique ratchets far above the ASOCIAL one-lifetime ceiling."""
    cum = GenesisWorld(_ccfg(n0=250, learn=True), seed=1)
    aso = GenesisWorld(_ccfg(n0=250, learn=False), seed=1)
    for _ in range(450):
        cum.step(); aso.step()
    c, a = cum.culture_test(), aso.culture_test()
    assert c and a
    assert c["tech_max"] > 1.5 * a["tech_max"]                   # the ratchet exceeds asocial reinvention
    assert c["hearth_tech_max"] > a["hearth_tech_max"]           # the cultural record accumulated


def test_culture_test_reports_fields_and_off_empty():
    w = GenesisWorld(_ccfg(n0=200), seed=0)
    for _ in range(120):
        w.step()
    out = w.culture_test()
    assert {"tech_mean", "tech_max", "hearth_tech_mean", "hearth_tech_max", "mean_gen"} <= set(out)
    assert GenesisWorld(_bcfg(), seed=0).culture_test() == {}    # culture off -> empty


def test_checkpoint_roundtrip_with_culture(tmp_path):
    w = GenesisWorld(_ccfg(n0=150), seed=1)
    for _ in range(150):
        w.step()
    p = str(tmp_path / "ck.npz")
    w.save_checkpoint(p)
    w2 = GenesisWorld(_ccfg(n0=150), seed=9)
    w2.load_checkpoint(p)
    assert np.allclose(w.struct_tech, w2.struct_tech)           # the cultural record survives a restart
    assert np.allclose(w.pop.tech, w2.pop.tech)


# ---------- R150: open-ended COMBINATORIAL culture ----------
def _kcfg(**kw):
    # the R149 viable culture regime + combinatorial tech tree on. Small tree for fast tests.
    kw.setdefault("n0", 250)
    kw.setdefault("innov_steps", 1)
    return _ccfg(combinatorial=True, max_techniques=400, n_seed_tech=6, **kw)


def test_combinatorial_requires_culture():
    with pytest.raises(ValueError):
        GenesisWorld(_bcfg(combinatorial=True), seed=0)        # combinatorial without culture=True


def test_combinatorial_off_is_byte_identical_to_r149():
    a = GenesisWorld(_ccfg(n0=200), seed=4)                    # R149 scalar culture
    b = GenesisWorld(_ccfg(n0=200, combinatorial=False), seed=4)
    for _ in range(60):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos)                # combinatorial=False draws no extra RNG
    assert np.array_equal(a.pop.tech, b.pop.tech)
    assert not hasattr(a, "rep")                               # no repertoire pool allocated on the scalar path


def test_tech_tree_is_deterministic_and_structured():
    from alife.genesis import combinatorial as cb
    pa, pb, level = cb.build_tech_tree(200, 6)
    pa2, pb2, level2 = cb.build_tech_tree(200, 6)
    assert np.array_equal(pa, pa2) and np.array_equal(level, level2)   # fixed tree across builds
    assert (pa[:6] == -1).all() and (level[:6] == 0).all()    # seeds: no prereqs, level 0
    for k in range(6, 200):
        assert 0 <= pa[k] < k and 0 <= pb[k] < k and pa[k] != pb[k]    # distinct lower-indexed prereqs
        assert level[k] == 1 + max(level[pa[k]], level[pb[k]])
    assert level.max() >= 2                                    # the tree has real depth to climb


def test_adjacent_possible_requires_prerequisites():
    from alife.genesis import combinatorial as cb
    pa, pb, level = cb.build_tech_tree(50, 4)
    rep = np.zeros((1, 50), dtype=bool)
    ap0 = cb.adjacent_possible(rep, pa, pb, 4, combo_prereqs=True)
    assert ap0[0, :4].all()                                    # from empty: only seeds are reachable
    assert not ap0[0, 4:].any()
    # a non-seed technique becomes reachable exactly once BOTH its prereqs are present
    k = 10
    rep[0, pa[k]] = True
    assert not cb.adjacent_possible(rep, pa, pb, 4, True)[0, k]   # one prereq is not enough
    rep[0, pb[k]] = True
    assert cb.adjacent_possible(rep, pa, pb, 4, True)[0, k]       # both prereqs -> now in the adjacent possible


def test_combo_prereqs_false_is_the_additive_null():
    from alife.genesis import combinatorial as cb
    pa, pb, _ = cb.build_tech_tree(50, 4)
    rep = np.zeros((1, 50), dtype=bool)
    ap = cb.adjacent_possible(rep, pa, pb, 4, combo_prereqs=False)
    assert ap.all()                                           # additive null: every unknown technique reachable


def test_max_level_known_picks_deepest():
    from alife.genesis import combinatorial as cb
    _, _, level = cb.build_tech_tree(50, 4)
    rep = np.zeros((2, 50), dtype=bool)
    rep[0, 4] = True                                          # a level-1 technique
    deep = int(np.argmax(level)); rep[1, deep] = True
    out = cb.max_level_known(rep, level)
    assert out[0] == level[4] and out[1] == level[deep]


def test_founders_start_with_a_tiny_repertoire():
    w = GenesisWorld(_kcfg(), seed=0)
    act = w.pop.active()
    assert w.rep[act].sum(axis=1).max() <= w.cfg.innov_steps   # each founder knows <= innov_steps techniques
    assert w.rep[act].any()                                    # but at least the seed discoveries happened


def test_social_learning_copies_repertoire_then_innovates():
    from alife.genesis import combinatorial as cb
    w = GenesisWorld(_kcfg(culture_fidelity=1.0, innov_steps=0), seed=0)
    pa, pb = w._tree_pa, w._tree_pb
    # plant a hearth carrying a deep, self-consistent repertoire (a full prereq chain up to technique k)
    w.struct_pos[0] = np.array([45.0, 45.0, 45.0]); w.struct_strength[0] = 2.0; w.struct_alive[0] = True
    chain = np.zeros(w.cfg.max_techniques, dtype=bool); chain[:6] = True
    for k in (6, 7, 8):
        chain[pa[k]] = True; chain[pb[k]] = True; chain[k] = True
    w.struct_rep[0] = chain
    s = w.pop.alloc(1); w.pop.pos[s] = np.array([45.0, 45.0, 46.0])
    par = w.pop.active()[0]; w.rep[par] = False
    w._acquire_repertoire(s, np.array([par]))
    assert np.array_equal(w.rep[s[0]], chain)                  # fidelity 1, no innovation -> exact copy of the record


def test_asocial_combinatorial_cannot_inherit():
    w = GenesisWorld(_kcfg(learn=False, culture_fidelity=1.0), seed=0)
    w.struct_pos[0] = np.array([45.0, 45.0, 45.0]); w.struct_strength[0] = 2.0; w.struct_alive[0] = True
    w.struct_rep[0, :50] = True                                # a rich hearth record
    s = w.pop.alloc(1); w.pop.pos[s] = np.array([45.0, 45.0, 46.0])
    par = w.pop.active()[0]
    w._acquire_repertoire(s, np.array([par]))
    assert w.rep[s[0]].sum() <= w.cfg.innov_steps              # asocial: ignores the record, reinvents from empty


def test_hearth_accumulates_repertoire_union():
    w = GenesisWorld(_kcfg(n0=4), seed=0)
    act = w.pop.active()
    w.pop.pos[act] = np.array([20.0, 20.0, 20.0])             # all builders at one site -> one hearth
    w.rep[act[0]] = False; w.rep[act[0], 7] = True
    out = np.zeros((act.size, w.spec.n_out)); out[0, w._proc_out] = 1.0
    w._build(act, out)
    h = np.where(w.struct_alive)[0][0]
    assert w.struct_rep[h, 7]
    w.rep[act[0]] = False; w.rep[act[0], 9] = True             # a later builder deposits a different technique
    w._build(act, out)
    assert w.struct_rep[h, 7] and w.struct_rep[h, 9]          # the record is the UNION (never loses a technique)


def test_combinatorial_open_ended_beats_additive_and_asocial():
    """The core R150 claim (smoke): under combinatorial (prerequisite-gated) discovery with social learning the
    living population's repertoire climbs far beyond the additive null AND the asocial control."""
    combo = GenesisWorld(_kcfg(n0=250, combo_prereqs=True, learn=True), seed=1)
    aso = GenesisWorld(_kcfg(n0=250, combo_prereqs=True, learn=False), seed=1)
    for _ in range(450):
        combo.step(); aso.step()
    c, a = combo.combinatorial_test(), aso.combinatorial_test()
    assert c and a
    assert c["pop_distinct"] > 3 * a["pop_distinct"]          # social pooling unlocks the combinatorial climb
    assert c["max_level"] > a["max_level"]                    # and reaches a deeper frontier


def test_combinatorial_test_fields_and_off_empty():
    w = GenesisWorld(_kcfg(n0=200), seed=0)
    for _ in range(120):
        w.step()
    out = w.combinatorial_test()
    assert {"pop_distinct", "hearth_distinct", "max_level", "mean_level", "mean_gen"} <= set(out)
    assert GenesisWorld(_ccfg(), seed=0).combinatorial_test() == {}   # scalar culture -> empty


def test_checkpoint_roundtrip_combinatorial(tmp_path):
    w = GenesisWorld(_kcfg(n0=150), seed=1)
    for _ in range(150):
        w.step()
    p = str(tmp_path / "ck.npz")
    w.save_checkpoint(p)
    w2 = GenesisWorld(_kcfg(n0=150), seed=9)
    w2.load_checkpoint(p)
    assert np.array_equal(w.rep, w2.rep)                       # the per-agent repertoires survive a restart
    assert np.array_equal(w.struct_rep, w2.struct_rep)         # and the hearth records
    assert np.array_equal(w.pop.tech, w2.pop.tech)


# ---------- R170: GENERATIVE open-ended tree (open-endedness made causal in the live world) ----------
def test_growing_tree_materializes_on_demand_and_caps():
    from alife.genesis import combinatorial as cb
    t = cb.GrowingTree(capacity=10, n_seed=3)
    assert t.n == 3 and (t.level[:3] == 0).all() and (t.pa[:3] == -1).all()   # seeds: level 0, no parents
    a = t.combine(0, 1)
    assert a == 3 and t.level[3] == 1 and t.n == 4                            # first product: a fresh deeper node
    assert t.combine(1, 0) == 3                                               # canonical pair -> same id, no growth
    assert t.n == 4
    b = t.combine(3, 2)
    assert b == 4 and t.level[4] == 2                                         # composing a product deepens the tree
    while t.n < t.capacity:                                                   # fill the registry to the cap
        lo = t.n
        assert t.combine(0, lo - 1) == lo
    full = t.n
    assert t.combine(1, 2) == -1 and t.n == full                             # full: no new node can be born (freeze)
    with pytest.raises(ValueError):
        t.combine(5, 5)                                                       # cannot compose a technique with itself


def test_growing_tree_discover_inplace_grows_depth_only_when_uncapped():
    from alife.genesis import combinatorial as cb
    rng = np.random.default_rng(0)
    big = cb.GrowingTree(capacity=4000, n_seed=6)
    small = cb.GrowingTree(capacity=12, n_seed=6)                             # capped at 12 nodes (6 products)
    rb = np.zeros((40, 4000), dtype=bool); rb[:, :6] = True
    rs = np.zeros((40, 12), dtype=bool); rs[:, :6] = True
    for _ in range(60):                                                       # repeated composition rounds
        big.discover_inplace(rb, rng, steps=2)
        small.discover_inplace(rs, np.random.default_rng(0), steps=2)
    assert big.n > small.n and small.n == 12                                  # capped tree freezes at capacity
    assert int(big.level.max()) > int(small.level.max())                     # uncapped frontier climbs deeper


def test_generative_tree_requires_combinatorial_and_excludes_fixed_node_gates():
    with pytest.raises(ValueError):
        GenesisWorld(_bcfg(generative_tree=True), seed=0)                     # generative_tree without combinatorial
    with pytest.raises(ValueError):
        GenesisWorld(_kcfg(generative_tree=True, tech_actions=True), seed=0)  # no pre-built deep recipe nodes


def test_generative_tree_off_is_byte_identical():
    a = GenesisWorld(_kcfg(n0=200), seed=4)                                   # default fixed tree
    b = GenesisWorld(_kcfg(n0=200, generative_tree=False), seed=4)
    for _ in range(80):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos)                               # the flag draws no extra RNG when off
    assert np.array_equal(a.rep, b.rep) and np.array_equal(a.pop.tech, b.pop.tech)
    assert a._tree is None                                                    # fixed-tree path: no GrowingTree built


def test_generative_tree_open_ended_climb_vs_capped_in_the_live_world():
    """The R170 headline: open-endedness is CAUSAL in the living world. With a generative tree the living
    population's cultural frontier (breadth + depth) keeps climbing, bounded ONLY by the capacity cap — raise
    the cap and it climbs higher; cap it small and it FREEZES. Same machinery, the only difference is the cap."""
    gen = dict(combinatorial=True, generative_tree=True, n_seed_tech=6, n0=250, innov_steps=3)
    big = GenesisWorld(_ccfg(max_techniques=4000, **gen), seed=1)
    cap = GenesisWorld(_ccfg(max_techniques=30, **gen), seed=1)
    for _ in range(300):
        big.step(); cap.step()
    b, c = big.combinatorial_test(), cap.combinatorial_test()
    assert b and c
    assert b["pop_distinct"] > 3 * c["pop_distinct"]                          # uncapped breadth climbs; capped freezes
    assert c["pop_distinct"] <= 30                                            # the capped tree cannot exceed its cap
    assert b["max_level"] > c["max_level"]                                    # and the uncapped frontier reaches deeper
    assert big._tree.n > 30 >= cap._tree.n                                    # the live tree GREW past the small cap


# ---------- R163: TEMPORAL phylogeny / open-ended cumulative descent ----------
def test_temporal_ladder_recovers_a_perfect_ladder():
    from alife.genesis import combinatorial as cb, phylogeny as ph
    pa, pb, level = cb.build_tech_tree(120, 6)
    first = level.astype(np.int64).copy()                      # PERFECT ladder: each tech appears at its depth
    sig = ph.temporal_ladder_signal(first, level, pa, pb, 6, n_perm=200)
    assert sig["precedence_frac"] == 1.0                       # a product never precedes its prereqs
    assert sig["level_time_corr"] > 0.99                       # time order == depth order
    assert sig["level_time_p"] < 0.05                          # vs the label-permutation null
    assert sig["precedence_null"] < 0.8                        # a shuffled ladder breaks precedence


def test_temporal_ladder_scrambled_has_no_signal():
    from alife.genesis import combinatorial as cb, phylogeny as ph
    pa, pb, level = cb.build_tech_tree(120, 6)
    first = np.random.default_rng(3).permutation(120).astype(np.int64)   # random times = the additive-null shape
    sig = ph.temporal_ladder_signal(first, level, pa, pb, 6, n_perm=200)
    assert abs(sig["level_time_corr"]) < 0.35                  # random times -> no depth recovery
    assert sig["precedence_frac"] < 0.9                        # random order violates prereq precedence


def _tcfg(**kw):
    return _kcfg(track_tech_history=True, **kw)


def test_track_tech_history_requires_combinatorial():
    with pytest.raises(ValueError):
        GenesisWorld(_ccfg(track_tech_history=True), seed=0)   # track_tech_history without combinatorial=True


def test_track_tech_history_is_byte_identical_and_logs_appearances():
    a = GenesisWorld(_kcfg(n0=250), seed=2)
    b = GenesisWorld(_kcfg(n0=250, track_tech_history=True), seed=2)
    for _ in range(80):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos)                # passive observer draws no RNG, perturbs nothing
    assert np.array_equal(a.rep, b.rep)
    first = b._tech_first_step
    assert int((first >= 0).sum()) >= 6                        # at least the seed primitives appeared
    assert first[first >= 0].max() <= b.step_count            # every stamp is a valid past step


def test_temporal_phylogeny_recovers_under_combinatorial_not_additive():
    """The R163 headline (smoke): combinatorial (prereq-gated) discovery makes the first-appearance time
    ladder RECOVER tree depth + respect precedence; the additive null scrambles the ladder."""
    combo = GenesisWorld(_tcfg(n0=250, combo_prereqs=True), seed=1)
    add = GenesisWorld(_tcfg(n0=250, combo_prereqs=False), seed=1)
    for _ in range(300):
        combo.step(); add.step()
    c, a = combo.temporal_phylogeny_test(n_perm=200), add.temporal_phylogeny_test(n_perm=200)
    assert c and a
    assert c["precedence_frac"] == 1.0                         # combinatorial: a technique never precedes its prereqs
    assert a["precedence_frac"] < 1.0                          # additive: uniform discovery breaks precedence
    assert c["level_time_corr"] > a["level_time_corr"]         # the depth ladder is recovered in time only under combo
    assert c["level_time_corr"] > 0.3


def test_temporal_phylogeny_test_off_empty():
    assert GenesisWorld(_kcfg(n0=200), seed=0).temporal_phylogeny_test() == {}   # track off -> empty


# ---------- R156: emergent divergent cultural TRADITIONS (cultural F_ST) ----------
def test_panmictic_requires_combinatorial():
    with pytest.raises(ValueError):
        GenesisWorld(_ccfg(panmictic_culture=True), seed=0)        # panmictic without combinatorial=True


def test_panmictic_off_is_byte_identical():
    a = GenesisWorld(_kcfg(n0=250), seed=3)
    b = GenesisWorld(_kcfg(n0=250, panmictic_culture=False), seed=3)
    for _ in range(120):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos) and np.array_equal(a.pop.vel, b.pop.vel)
    assert np.array_equal(a.rep, b.rep)                            # the default path draws no extra RNG


def test_panmictic_diverges_from_local():
    """The panmictic NULL copies a RANDOM global hearth instead of the nearest -> the repertoires it produces
    diverge from the spatially-local path (the manipulation actually changes transmission)."""
    loc = GenesisWorld(_kcfg(n0=250), seed=5)
    pan = GenesisWorld(_kcfg(n0=250, panmictic_culture=True), seed=5)
    for _ in range(200):
        loc.step(); pan.step()
    assert not np.array_equal(loc.rep, pan.rep)                    # different transmission source -> different culture


def test_tradition_test_fields_and_off_empty():
    w = GenesisWorld(_kcfg(n0=250), seed=0)
    for _ in range(150):
        w.step()
    out = w.tradition_test(grid=2)
    assert {"fst", "n_demes", "n_distinct_traditions"} <= set(out)
    assert 0.0 <= out["fst"] <= 1.0
    assert GenesisWorld(_ccfg(), seed=0).tradition_test() == {}    # scalar culture -> empty


def test_local_transmission_builds_structured_traditions():
    """R156 mechanism smoke: local (nearest-hearth) transmission over the open-ended tree partitions the
    living population into >=2 spatial demes carrying MULTIPLE distinct dominant techniques (structured
    traditions, F_ST > 0). The directional local>panmictic claim needs scale + multiple seeds and is the
    REAL-VERIFY headline (scripts/run_genesis_traditions.py) — at this fast unit scale F_ST is noise-bound."""
    loc = GenesisWorld(_kcfg(n0=300), seed=2)
    for _ in range(300):
        loc.step()
    fl = loc.tradition_test(grid=2)
    assert fl and fl["n_demes"] >= 2
    assert 0.0 <= fl["fst"] <= 1.0
    assert fl["n_distinct_traditions"] >= 2                        # demes carry different dominant techniques


# ---------- R157: LOSSY / DECAYING cultural memory (cultural loss — the Tasmania / Henrich effect) ----------
def test_culture_decay_requires_combinatorial():
    with pytest.raises(ValueError):
        GenesisWorld(_ccfg(culture_decay=True), seed=0)           # culture_decay without combinatorial=True


def test_culture_decay_off_is_byte_identical():
    a = GenesisWorld(_kcfg(n0=250), seed=3)
    b = GenesisWorld(_kcfg(n0=250, culture_decay=False), seed=3)
    for _ in range(120):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos) and np.array_equal(a.pop.vel, b.pop.vel)
    assert np.array_equal(a.rep, b.rep)                            # the union path draws no extra RNG, allocates nothing
    assert not hasattr(b, "struct_memory")                        # struct_memory exists only when culture_decay=on


def test_culture_decay_forgets_unmaintained_technique():
    """The core R157 mechanism: a technique recorded at a hearth FADES out of the sensed record once it is no
    longer re-deposited (memory decays below threshold), but stays while it is reinforced each step."""
    w = GenesisWorld(_kcfg(n0=200, culture_decay=True, memory_decay=0.1, memory_threshold=0.5,
                           memory_reinforce=1.0), seed=0)
    h, forget_j, keep_j = 0, 7, 8
    w.struct_alive[:] = False
    w.struct_alive[h] = True
    w.struct_memory[:] = 0.0
    w.struct_memory[h, forget_j] = 1.0                            # deposited once, then never again
    w.struct_memory[h, keep_j] = 1.0
    for _ in range(12):                                           # 0.9**12 ~ 0.28 < 0.5 -> forget_j drops out
        w.struct_memory[h, keep_j] += w.cfg.memory_reinforce     # keep_j is re-deposited every step
        w._decay_memory()
    assert not w.struct_rep[h, forget_j]                         # unmaintained knowledge is LOST
    assert w.struct_rep[h, keep_j]                               # actively-practised knowledge persists


def test_culture_decay_record_is_lossy_vs_union():
    """Cultural loss at the population level: the decaying record holds FEWER techniques across strong hearths
    than R156's never-forgetting union, because disused techniques fade out instead of accumulating forever."""
    union = GenesisWorld(_kcfg(n0=300), seed=4)                  # R156: monotone bitwise-or union
    decay = GenesisWorld(_kcfg(n0=300, culture_decay=True), seed=4)
    for _ in range(250):
        union.step(); decay.step()
    u_rec = int(union.struct_rep[union._strong_hearths()].sum())
    d_rec = int(decay.struct_rep[decay._strong_hearths()].sum())
    assert d_rec < u_rec                                          # forgetting -> a strictly smaller cultural store
    assert not np.array_equal(union.rep, decay.rep)              # lossy transmission -> a different culture


def test_culture_decay_checkpoint_roundtrip(tmp_path):
    w = GenesisWorld(_kcfg(n0=250, culture_decay=True), seed=1)
    for _ in range(120):
        w.step()
    p = str(tmp_path / "decay.npz")
    w.save_checkpoint(p)
    w2 = GenesisWorld(_kcfg(n0=250, culture_decay=True), seed=9)
    w2.load_checkpoint(p)
    assert np.array_equal(w.struct_memory, w2.struct_memory)     # the decaying memory survives a restart
    assert np.array_equal(w.struct_rep, w2.struct_rep)           # and the derived record


# ---------- R151: the integrated capstone — every ladder stage coexisting in ONE world ----------
def _capcfg(**kw):
    """The capstone regime: predator arms race + caste division of labour + niche-construction hearths +
    open-ended combinatorial culture, ALL ON in one world. Every prior stage was verified in isolation
    behind its own flag; this is the first config that runs them together (the integration test). Caste makes
    processors eat ~0 (they live on wages), so the world is food-limited — the regime is food-rich enough that
    harvesters thrive, fund the processor caste, and still feed a persistent predator population."""
    base = _kcfg(specialize=True, n0=kw.pop("n0", 400))
    overrides = dict(capacity=1500, food_cap=900, food_regrow=45,
                     n_predators0=30, pred_capacity=70, pred_base_cost=0.6)
    overrides.update(kw)
    return replace(base, **overrides)


def test_capstone_all_stages_construct_and_run():
    """The integrated world constructs (brain shape composes every channel), runs without crashing, stays
    alive, and every stage's read-out reports — i.e. the mechanisms COEXIST rather than crashing/cancelling."""
    w = GenesisWorld(_capcfg(), seed=0)
    assert w.has_predators and w.specialize and w.building and w.culture and w.combinatorial
    for _ in range(200):
        w.step()
    snap = w.snapshot()
    assert snap["population"] > 80                       # the integrated world is not collapsing
    assert snap["predators"] > 0                         # the arms race partner persists
    assert w.caste_test()                                # caste read-out populated (Stage 3 present)
    assert w.combinatorial_test()                        # open-ended culture read-out populated (Stage 5)
    assert snap["spec_mean"] >= 0.0 and "n_hearths" in snap


def test_harvest_gain_composes_spec_and_tech_multiplicatively():
    """R151 regression: with BOTH specialize and culture on, the harvest payoff must MULTIPLY the caste
    convexity and the learned-technique multiplier — NOT drop culture's tech_gain (the old if/elif bug
    that left the cumulative-culture ratchet with no selective gradient under caste)."""
    w = GenesisWorld(_capcfg(n0=80), seed=0)
    act = w.pop.active()[:4]
    w.pop.spec[act] = 0.0                                # pure harvesters -> convex factor == 1
    w.pop.tech[act] = np.array([0.0, 1.0, 2.0, 4.0])
    g = w._harvest_gain(act)
    expect = w.cfg.food_value * (1.0 + w.cfg.tech_gain * w.pop.tech[act])
    assert np.allclose(g, expect)                        # culture payoff IS applied under caste
    assert g[3] > g[0]                                   # mastery still pays -> the ratchet keeps a gradient
    w.pop.spec[act] = 1.0                                # pure processors -> convex factor == 0
    assert np.allclose(w._harvest_gain(act), 0.0)        # ...and the caste convexity still applies too


def test_harvest_gain_single_flag_matches_legacy_formulas():
    """Byte-identical guard: a single-flag world reproduces the exact R147 / R149 harvest formula, so the
    R151 multiplicative refactor changes ONLY the never-before-run both-on case."""
    cul = GenesisWorld(_ccfg(n0=60), seed=0)             # culture only (no specialize)
    a = cul.pop.active()[:3]; cul.pop.tech[a] = np.array([0.0, 1.5, 3.0])
    assert np.allclose(cul._harvest_gain(a), cul.cfg.food_value * (1.0 + cul.cfg.tech_gain * cul.pop.tech[a]))
    cas = GenesisWorld(fast_cfg(n0=60, processing=True, specialize=True), seed=0)   # caste only (no culture)
    b = cas.pop.active()[:3]; cas.pop.spec[b] = np.array([0.0, 0.5, 1.0])
    assert np.allclose(cas._harvest_gain(b), cas.cfg.food_value * np.power(1.0 - cas.pop.spec[b], cas.cfg.spec_gamma))


# ---------- R153: CULTURE UNLOCKS WORLD-ACTIONS (techniques gate what an agent can physically eat) ----------
def _tacfg(**kw):
    """The R153 regime: the combinatorial-culture world (_kcfg) plus tech_actions — food spawns in recipe-
    locked tiers and only a culturally deep enough agent can eat the richer tiers. tier0 (the free resource)
    sustains a modest population even asocially, so the locked tiers are a real cultural BONUS (the world
    stays alive in both arms; transmission decides how much of it gets exploited)."""
    kw.setdefault("n0", 250)
    base = dict(tech_actions=True, n_food_tiers=3, recipe_level_step=1, tier_value_bonus=2.0,
                tier0_frac=0.6, food_cap=700, food_regrow=35)
    base.update(kw)
    return replace(_kcfg(), **base)


def test_tech_actions_requires_combinatorial():
    with pytest.raises(ValueError):
        GenesisWorld(_ccfg(tech_actions=True), seed=0)         # tech_actions without combinatorial=True


def test_tech_actions_off_is_byte_identical_to_r150():
    a = GenesisWorld(_kcfg(n0=200), seed=4)                    # R150 combinatorial culture
    b = GenesisWorld(_kcfg(n0=200, tech_actions=False), seed=4)
    for _ in range(60):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos)                # tech_actions=False draws no extra RNG
    assert np.array_equal(a.pop.tech, b.pop.tech)
    assert np.array_equal(a.food, b.food)                      # food layout identical (food_tier not drawn)
    assert (a.food_tier == 0).all()                            # all tier 0 when off
    assert not hasattr(a, "_recipe_tech")                      # no recipe table allocated on the off path


def test_recipe_techniques_deterministic_and_deepening():
    from alife.genesis import combinatorial as cb
    _, _, level = cb.build_tech_tree(400, 6)
    r1 = cb.recipe_techniques(level, 6, 4, 3)
    r2 = cb.recipe_techniques(level, 6, 4, 3)
    assert np.array_equal(r1, r2)                              # deterministic in the fixed tree
    assert r1[0] == -1                                         # tier 0 is free (no recipe)
    levs = level[r1[1:]]
    assert (levs >= np.array([3, 6, 9])).all()                # each tier's recipe sits at the required depth
    assert levs[0] < levs[1] < levs[2]                        # higher tiers need a strictly deeper technique


def test_recipe_techniques_raises_when_tree_too_shallow():
    from alife.genesis import combinatorial as cb
    _, _, level = cb.build_tech_tree(30, 6)                    # a tiny, shallow tree
    with pytest.raises(ValueError):
        cb.recipe_techniques(level, 6, 8, 5)                   # demands level>=35, impossible


def test_recipe_gate_blocks_unknowing_eater_and_pays_tier_bonus():
    """The core mechanism: an agent can harvest a tier-t mote ONLY if its repertoire holds that tier's
    recipe; knowing it both unlocks the food AND pays the richer tier value."""
    w = GenesisWorld(_tacfg(n0=2), seed=0)
    a, b = w.pop.active()[:2]
    t = 2                                                      # a mid locked tier
    rt = w._recipe_tech[t]
    w.pop.energy[a] = w.pop.energy[b] = 50.0
    w.rep[a] = False                                           # agent a knows NOTHING (no recipe)
    w.rep[b] = False; w.rep[b, rt] = True                     # agent b knows tier-t's recipe
    w.pop.spec[a] = w.pop.spec[b] = 0.0                        # no caste; isolate the tier effect
    w.pop.tech[a] = w.pop.tech[b] = 0.0                        # no technique multiplier
    w.food = np.array([w.pop.pos[a], w.pop.pos[b]])           # one tier-t mote on EACH agent
    w.food_type = np.zeros(2, dtype=np.int64)
    w.food_tier = np.array([t, t], dtype=np.int64)
    w.food_ripe = np.array([True, True]); w.ripe_age = np.zeros(2, dtype=np.int32)
    w.food_proc = np.full(2, -1, dtype=np.int64)
    w._eat()
    assert w.pop.energy[a] == 50.0                            # a lacks the recipe -> cannot eat the locked tier
    expect = 50.0 + w.cfg.food_value * (1.0 + w.cfg.tier_value_bonus * t)
    assert abs(w.pop.energy[b] - expect) < 1e-9              # b unlocks it AND earns the richer tier value


def test_tier0_is_always_edible():
    w = GenesisWorld(_tacfg(n0=1), seed=0)
    a = w.pop.active()[0]
    w.rep[a] = False                                          # culturally naive
    w.pop.energy[a] = 50.0; w.pop.spec[a] = 0.0; w.pop.tech[a] = 0.0
    w.food = np.array([w.pop.pos[a]]); w.food_type = np.zeros(1, dtype=np.int64)
    w.food_tier = np.zeros(1, dtype=np.int64)                 # tier 0 = the free resource
    w.food_ripe = np.array([True]); w.ripe_age = np.zeros(1, dtype=np.int32)
    w.food_proc = np.full(1, -1, dtype=np.int64)
    w._eat()
    assert abs(w.pop.energy[a] - (50.0 + w.cfg.food_value)) < 1e-9   # base value, no recipe needed


def test_food_tiers_spawn_locked_and_free():
    w = GenesisWorld(_tacfg(n0=50), seed=1)
    assert w.food_tier.max() == w.cfg.n_food_tiers - 1        # locked tiers are actually present
    assert (w.food_tier == 0).any()                          # and so is the free tier
    frac0 = (w.food_tier == 0).mean()
    assert 0.45 < frac0 < 0.72                                # ~tier0_frac (0.6) of food is the free tier


def test_tech_actions_test_fields_and_off_empty():
    w = GenesisWorld(_tacfg(n0=200), seed=0)
    for _ in range(120):
        w.step()
    out = w.tech_actions_test()
    assert {"realized_tiers", "max_tiers", "mean_edible_tiers", "locked_food_frac", "tier_eats"} <= set(out)
    assert out["max_tiers"] == w.cfg.n_food_tiers
    assert 1 <= out["realized_tiers"] <= out["max_tiers"]
    assert GenesisWorld(_kcfg(), seed=0).tech_actions_test() == {}   # off -> empty


def test_transmission_unlocks_more_tiers_than_asocial():
    """The R153 claim (smoke): with social learning the population climbs to the deep RECIPE techniques and
    physically unlocks more food tiers; the asocial control (no transmission) stays locked near tier 0 and
    leaves rich food uneaten (high locked_food_frac)."""
    soc = GenesisWorld(_tacfg(n0=250, learn=True), seed=1)
    aso = GenesisWorld(_tacfg(n0=250, learn=False), seed=1)
    for _ in range(450):
        soc.step(); aso.step()
    s, a = soc.tech_actions_test(), aso.tech_actions_test()
    assert s["realized_tiers"] > a["realized_tiers"]          # transmission unlocks strictly more tiers
    assert s["mean_edible_tiers"] > a["mean_edible_tiers"]    # the average agent eats a wider diet
    assert a["realized_tiers"] <= 2                           # asocial stays near the free tier (can't reach deep recipes)


# ---------- R157: SPATIAL niches -> ECOLOGICALLY-SELECTED divergent traditions ----------
def test_spatial_tiers_requires_tech_actions():
    with pytest.raises(ValueError):
        GenesisWorld(_kcfg(spatial_tiers=True), seed=0)           # spatial_tiers without tech_actions=True


def test_spatial_tiers_off_is_byte_identical_to_r153():
    a = GenesisWorld(_tacfg(n0=220), seed=2)                      # R153 random-tier world
    b = GenesisWorld(_tacfg(n0=220, spatial_tiers=False), seed=2)
    for _ in range(120):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos) and np.array_equal(a.pop.vel, b.pop.vel)
    assert np.array_equal(a.rep, b.rep)
    assert np.array_equal(a.food_tier, b.food_tier)              # the spatial branch consumes no RNG -> identical


def test_spatial_tiers_assigns_tier_by_region():
    """The R157 mechanism: a locked mote's tier is its x-axis REGION index (region r -> tier r+1), so each
    region rewards exactly one recipe branch. Verified directly on hand-placed positions."""
    w = GenesisWorld(_tacfg(n0=200, spatial_tiers=True), seed=0)
    size = w.cfg.world.size
    R = w.cfg.n_food_tiers - 1
    pos = np.zeros((300, 3))
    pos[:, 0] = np.linspace(0.01, size - 0.01, 300)              # sweep across all x-regions
    tiers = w._food_tiers(pos)
    locked = tiers > 0
    expect = 1 + np.clip((pos[:, 0] / size * R).astype(int), 0, R - 1)
    assert np.array_equal(tiers[locked], expect[locked])         # every locked mote carries its region's tier
    assert locked.any() and (tiers == 0).any()                  # both free (tier 0) and locked motes present


def test_ecological_traditions_test_fields_and_off_empty():
    w = GenesisWorld(_tacfg(n0=250, spatial_tiers=True), seed=0)
    for _ in range(150):
        w.step()
    out = w.ecological_traditions_test(min_region=10)
    assert {"alignment", "aligned_regions", "n_regions", "n_branches", "own_frac", "other_frac"} <= set(out)
    assert GenesisWorld(_kcfg(), seed=0).ecological_traditions_test() == {}   # tech_actions off -> empty


def _ecocfg(**kw):
    """The R157 ecological-selection regime: tech_actions with 3 locked-tier branches, a recipe carry-BUDGET
    (forced specialists), a free-tier LIFELINE (tier0_frac high so the population survives while branches sort),
    and spatial_tiers ON. This is the regime where selection sorts each branch into its own region."""
    base = dict(n_food_tiers=4, recipe_level_step=2, tier_value_bonus=3.0, tier0_frac=0.65,
                recipe_budget=2, food_cap=900, food_regrow=45)
    base.update(kw)
    return _tacfg(**base)


def test_spatial_selection_beats_random_null():
    """The R157 headline (smoke, 2 seeds): with spatial_tiers + a recipe budget each region is ECONOMICALLY
    enriched for its OWN branch (own-branch fraction > others'), an alignment the scrambled-niche null
    (random tiers, same budget) does NOT produce -> traditions become spatially locked by SELECTION. The
    magnitude + 3D patches are the REAL-VERIFY headline (scripts/run_genesis_ecotraditions.py)."""
    sp, rn = [], []
    for seed in (0, 1):
        spat = GenesisWorld(_ecocfg(n0=500, spatial_tiers=True), seed=seed)
        rand = GenesisWorld(_ecocfg(n0=500, spatial_tiers=False), seed=seed)
        for _ in range(450):
            spat.step(); rand.step()
        sp.append(spat.ecological_traditions_test(min_region=12).get("alignment", 0.0))
        rn.append(rand.ecological_traditions_test(min_region=12).get("alignment", 0.0))
    assert np.mean(sp) > np.mean(rn)                              # selection sorts branches into regions
    assert np.mean(sp) > 0.0                                      # each region net-enriched for its own branch


def test_recipe_knobs_require_tech_actions():
    for kw in (dict(recipe_budget=1), dict(recipe_upkeep=0.1)):
        with pytest.raises(ValueError):
            GenesisWorld(_kcfg(**kw), seed=0)                     # recipe knobs without tech_actions=True


def test_recipe_budget_caps_carried_branches():
    """With recipe_budget=1 no living agent ever carries more than one LOCKED-tier recipe branch (forced
    specialists) — the keystone that lets spatial selection sort branches into regions."""
    w = GenesisWorld(_ecocfg(n0=300, recipe_budget=1, spatial_tiers=True), seed=0)
    for _ in range(200):
        w.step()
    act = w.pop.active()
    carried = w.rep[np.ix_(act, w._recipe_tech[1:])].sum(axis=1)
    assert carried.max() <= 1                                     # never a generalist holding >1 branch


def test_recipe_budget_off_is_byte_identical():
    a = GenesisWorld(_tacfg(n0=220), seed=2)                      # R153 (recipe_budget=0 default)
    b = GenesisWorld(_tacfg(n0=220, recipe_budget=0, recipe_upkeep=0.0), seed=2)
    for _ in range(120):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos) and np.array_equal(a.rep, b.rep)


def test_checkpoint_roundtrips_food_tier(tmp_path):
    w = GenesisWorld(_tacfg(n0=150), seed=1)
    for _ in range(120):
        w.step()
    p = str(tmp_path / "ck.npz")
    w.save_checkpoint(p)
    w2 = GenesisWorld(_tacfg(n0=150), seed=9)
    w2.load_checkpoint(p)
    assert np.array_equal(w.food_tier, w2.food_tier)          # the tier of every standing mote survives a restart
    assert np.array_equal(w._recipe_tech, w2._recipe_tech)    # recipe table is deterministic from the fixed tree


# ---------- R158: TRADE between region-specialists -> an inter-group ECONOMY ----------
def test_trade_requires_tech_actions():
    with pytest.raises(ValueError):
        GenesisWorld(_kcfg(trade=True), seed=0)                   # trade without tech_actions=True
    with pytest.raises(ValueError):
        GenesisWorld(_tacfg(trade_scramble=True), seed=0)         # scramble null without trade=True


def test_trade_off_is_byte_identical():
    """trade=False draws no extra RNG and transfers no energy -> byte-identical to R157."""
    a = GenesisWorld(_ecocfg(n0=220, spatial_tiers=True), seed=3)
    b = GenesisWorld(_ecocfg(n0=220, spatial_tiers=True, trade=False), seed=3)
    for _ in range(120):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos) and np.array_equal(a.pop.energy, b.pop.energy)
    assert np.array_equal(a.rep, b.rep)


def test_trade_transfers_only_to_complementary_partner():
    """A giver shares ONLY with a hungry agent that LACKS the traded tier's recipe (a complementary specialist
    who could not have eaten this food): a same-branch neighbour is never a recipient. Hand-built two agents."""
    w = GenesisWorld(_ecocfg(n0=50, spatial_tiers=True, trade=True, trade_radius=50.0), seed=0)
    p = w.pop
    act = p.active()
    giver, partner = int(act[0]), int(act[1])
    rt = int(w._recipe_tech[1])                                   # tier-1 branch
    w.rep[giver, rt] = True                                       # giver holds branch 1
    p.pos[partner] = p.pos[giver]                                 # co-located
    p.energy[partner] = 10.0                                      # hungry
    # partner HOLDS the same branch -> NOT complementary -> no transfer
    w.rep[partner, rt] = True
    before = p.energy[partner]
    w._do_trade(np.array([giver]), np.array([w.cfg.food_value]), 1)
    assert p.energy[partner] == before                           # same-branch neighbour is never fed
    # partner LACKS the branch -> complementary -> gets the surplus
    w.rep[partner, rt] = False
    w._do_trade(np.array([giver]), np.array([w.cfg.food_value]), 1)
    assert p.energy[partner] > before                            # complementary hungry neighbour is fed


def _satcfg(**kw):
    """The R158 saturated regime: the eco world tuned so the population robustly fills its ceiling across seeds
    (a high free-tier lifeline + ample food), so trade reliably fires and its effect is measured against a
    STABLE pop rather than the bimodal collapse-or-cap noise. This is the regime the R158 verify uses."""
    base = dict(spatial_tiers=True, recipe_budget=2, tier0_frac=0.72, tier_value_bonus=3.0,
                food_cap=1100, food_regrow=55)
    base.update(kw)
    return _ecocfg(**base)


def test_trade_test_fields_and_real_is_local_and_complementary():
    """Over a real run the trade economy is LOCAL (partners within trade_radius) and fully COMPLEMENTARY (every
    receiver lacks the traded recipe), with substantial volume — and the scramble null is dispersed (partners
    arbitrarily far) and MORE cross-region, isolating the local economic structure from matched energy injection.
    Real trade is mostly WITHIN-region (it feeds nearby off-branch minorities, not a cross-border economy).
    Read-out empty when trade off."""
    real = GenesisWorld(_satcfg(n0=600, trade=True), seed=1)
    scr = GenesisWorld(_satcfg(n0=600, trade=True, trade_scramble=True), seed=1)
    for _ in range(250):
        real.step(); scr.step()
    ro, so = real.trade_test(), scr.trade_test()
    assert {"trade_count", "trade_volume", "mean_partner_dist", "complementary_frac",
            "cross_region_frac"} <= set(ro)
    assert ro["trade_count"] > 0 and so["trade_count"] > 0
    assert ro["trade_volume"] > 0.0
    assert ro["complementary_frac"] == 1.0                       # real: every receiver lacks the recipe
    assert ro["mean_partner_dist"] < real.cfg.trade_radius       # real: a local market (within radius)
    assert ro["mean_partner_dist"] < so["mean_partner_dist"]     # scramble partners are arbitrarily far
    assert ro["cross_region_frac"] < so["cross_region_frac"]     # real trade is LOCAL (within-region); scramble disperses
    assert GenesisWorld(_satcfg(n0=80), seed=0).trade_test() == {}  # off -> empty


def test_trade_is_causally_inert_on_population():
    """HONEST NEGATIVE (the R158 finding, pinned as a regression): the trade economy is real but causally INERT
    on the saturated substrate — the population is hard-constrained, so redistributing harvested energy (here even
    at a super-unit trade_gain that INJECTS energy) does not raise the carrying capacity vs no-trade. Trade does
    not relax the limiting constraint, so an inter-agent economy alone does not drive a population transition."""
    for seed in (0, 1):
        on = GenesisWorld(_satcfg(n0=600, trade=True, trade_gain=2.0), seed=seed)
        off = GenesisWorld(_satcfg(n0=600, trade=False), seed=seed)
        for _ in range(300):
            on.step(); off.step()
        assert abs(on.pop.active().size - off.pop.active().size) <= 5  # energy injection does not lift the ceiling


# ---------- R159: PRODUCTIVE goods trade — an economy that CHANGES THE OUTCOME (vs R158's inert redistribution) ----------
def _goodscfg(**kw):
    """The R159 PRODUCTIVE-economy regime. seed_specialists starts an already-specialized population (per R157)
    so the economic question is isolated from the cultural-emergence bootstrap: a minority of founders each hold
    one recipe (producers who can harvest a locked tier), the rest are naive (free-tier only) -> in every region
    a few specialists sit among many complementary partners. trade_goods then lets a specialist harvest EXTRA
    wasted tier-t motes and ship them as edible GOODS to nearby hungry complementary partners (food-slot freed,
    energy conserved). This is the regime where the productive economy fires reliably and its effect on the
    carrying capacity is measured."""
    base = dict(spatial_tiers=True, recipe_budget=2, tier0_frac=0.35, tier_value_bonus=3.0,
                food_cap=900, food_regrow=45, seed_specialists=True, seed_specialist_frac=0.3, goods_max=3)
    base.update(kw)
    return _ecocfg(**base)


def test_goods_off_is_byte_identical_to_r157():
    # trade_goods/seed_specialists default off add no dynamics and no extra RNG draws: an eco run is bit-for-bit
    # the R157 baseline, and the goods read-out is empty.
    a = GenesisWorld(_ecocfg(n0=300, tier0_frac=0.35), seed=4)
    b = GenesisWorld(_ecocfg(n0=300, tier0_frac=0.35, trade_goods=False, seed_specialists=False), seed=4)
    for _ in range(120):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos) and np.array_equal(a.pop.energy, b.pop.energy)
    assert a.goods_test() == {}                                   # off -> empty read-out


def test_goods_requires_tech_actions_and_excludes_trade():
    import pytest
    with pytest.raises(ValueError):
        GenesisWorld(replace(fast_cfg(), trade_goods=True), seed=0)   # no tech_actions
    with pytest.raises(ValueError):
        GenesisWorld(_goodscfg(n0=80, trade=True, trade_goods=True), seed=0)  # mutually exclusive modes


def test_goods_test_fields_and_local():
    """Over a real run the productive economy fires (motes consumed-for-trade > 0, energy delivered) and is LOCAL
    (partners within trade_radius); the scramble null delivers the same goods to arbitrarily-distant random agents
    (locality destroyed). Read-out empty when off."""
    real = GenesisWorld(_goodscfg(n0=500, trade_goods=True), seed=1)
    scr = GenesisWorld(_goodscfg(n0=500, trade_goods=True, trade_scramble=True), seed=1)
    for _ in range(250):
        real.step(); scr.step()
    ro, so = real.goods_test(), scr.goods_test()
    assert {"goods_count", "goods_motes", "goods_volume", "mean_partner_dist"} <= set(ro)
    assert ro["goods_count"] > 0 and ro["goods_motes"] > 0 and ro["goods_volume"] > 0.0
    assert ro["mean_partner_dist"] < real.cfg.trade_radius        # real: a local market (within radius)
    assert ro["mean_partner_dist"] < so["mean_partner_dist"]      # scramble partners are arbitrarily far
    assert GenesisWorld(_goodscfg(n0=80, trade_goods=False), seed=0).goods_test() == {}


def test_goods_trade_is_causally_inert_on_carrying_capacity():
    """HONEST NEGATIVE (the R159 finding, pinned as a regression) — DEEPER than R158's. The productive goods
    economy is REAL (specialists harvest wasted locked motes and ship them as goods to starving complementary
    partners: goods_motes > 0) yet it does NOT raise the carrying capacity: pop ON == pop OFF. The reason is
    structural and stronger than R158's redistribution result — the population is NOT food-quantity-limited here
    (it equilibrates by foraging/lifespan dynamics, frequently exceeding the standing food count), so UNLOCKING
    otherwise-wasted food cannot lift a ceiling that food abundance never set. Production, like redistribution,
    leaves the binding constraint untouched."""
    for seed in (0, 1):
        on = GenesisWorld(_goodscfg(n0=600, trade_goods=True), seed=seed)
        off = GenesisWorld(_goodscfg(n0=600, trade_goods=False), seed=seed)
        for _ in range(300):
            on.step(); off.step()
        assert on._goods_motes > 0                                       # the productive economy actually fired
        assert abs(on.pop.active().size - off.pop.active().size) <= 8    # yet carrying capacity is unchanged


# ---------- R154: MULTI-AXIS culture-gated PHYSICAL capabilities (techniques reshape movement + reach) ----------
def _tccfg(**kw):
    """The R154 regime: the R153 tech-actions world plus tech_capabilities — deep tech-tree nodes ALSO unlock
    locomotion (a higher max speed) and harvest reach (a larger eat radius), so cultural depth reshapes the
    agent's whole physical phenotype. Small cap_level_step so the test tree is deep enough to place both axes."""
    return replace(_tacfg(**kw), tech_capabilities=True, n_capabilities=2, cap_level_step=2,
                   cap_speed_mult=1.0, cap_reach_mult=1.0)


def test_tech_capabilities_requires_combinatorial():
    with pytest.raises(ValueError):
        GenesisWorld(_ccfg(tech_capabilities=True), seed=0)    # tech_capabilities without combinatorial=True


def test_tech_capabilities_off_is_byte_identical_to_r153():
    a = GenesisWorld(_tacfg(n0=200), seed=4)                   # R153 tech-actions world
    b = GenesisWorld(_tacfg(n0=200, tech_capabilities=False), seed=4)
    for _ in range(60):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos)                # tech_capabilities=False draws no extra RNG / no effect
    assert np.array_equal(a.pop.vel, b.pop.vel)               # movement is byte-identical (speed cap = cfg.speed)
    assert np.array_equal(a.food, b.food)                      # eat reach unchanged -> food layout identical
    assert not hasattr(a, "_cap_tech")                        # no capability table allocated on the off path


def test_capability_techniques_deterministic_and_deepening():
    from alife.genesis import combinatorial as cb
    _, _, level = cb.build_tech_tree(400, 6)
    c1 = cb.capability_techniques(level, 6, 3, 3)
    c2 = cb.capability_techniques(level, 6, 3, 3)
    assert np.array_equal(c1, c2)                              # deterministic in the fixed tree
    levs = level[c1]
    assert (levs >= np.array([3, 6, 9])).all()                # each axis sits at its required depth
    assert levs[0] < levs[1] < levs[2]                        # a later axis needs a strictly deeper technique


def test_capability_techniques_raises_when_tree_too_shallow():
    from alife.genesis import combinatorial as cb
    _, _, level = cb.build_tech_tree(30, 6)                    # a tiny, shallow tree
    with pytest.raises(ValueError):
        cb.capability_techniques(level, 6, 8, 5)              # demands level>=40, impossible


def test_speed_node_caps_are_physical_and_categorical():
    """The locomotion axis: an agent holding the speed node moves at a strictly higher MAX speed, and the cap
    is physically enforced in the step (a non-holder's realized speed never exceeds the base cap)."""
    w = GenesisWorld(_tccfg(n0=40), seed=0)
    act = w.pop.active()
    w.pop.energy[act] = 80.0; w.pop.age[act] = 0               # keep them all alive across the step
    w.rep[act] = False
    holders = act[: act.size // 2]
    w.rep[holders, w._cap_tech[0]] = True                    # half hold the locomotion node
    # force the speed limiter to bind: give everyone a velocity far above any cap
    dirs = w.rng.normal(size=(act.size, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    w.pop.vel[act] = dirs * 100.0
    caps = np.asarray(w._cap_speed(act)).reshape(-1)
    hold_mask = np.isin(act, holders)
    assert np.allclose(caps[hold_mask], w.cfg.speed * 2.0)    # holder cap = speed*(1+cap_speed_mult)=6
    assert np.allclose(caps[~hold_mask], w.cfg.speed)         # non-holder cap = base speed
    w.step()
    spd = np.linalg.norm(w.pop.vel[act], axis=1)              # realized speed right after the step
    assert (spd[~hold_mask] <= w.cfg.speed + 1e-9).all()     # base cap physically enforced for non-holders
    assert (spd[hold_mask] > w.cfg.speed + 1e-6).all()       # holders actually move faster than the base cap


def test_reach_node_enlarges_eat_radius_categorically():
    """The harvest-reach axis: a mote just BEYOND the base eat radius is harvestable ONLY by an agent holding
    the reach node — a categorical physical capability, not a payoff scalar."""
    w = GenesisWorld(_tccfg(n0=2), seed=0)
    a, b = w.pop.active()[:2]
    w.pop.energy[a] = w.pop.energy[b] = 50.0
    w.pop.spec[a] = w.pop.spec[b] = 0.0; w.pop.tech[a] = w.pop.tech[b] = 0.0
    w.rep[a] = w.rep[b] = False
    w.rep[b, w._cap_tech[1]] = True                          # only b holds the reach node
    d = w.cfg.eat_radius * 1.5                                # 4.5: beyond base radius (3), within reach cap (6)
    off = np.array([d, 0.0, 0.0])
    w.food = np.array([w.pop.pos[a] + off, w.pop.pos[b] + off])  # one tier-0 mote 4.5 from each agent
    w.food_type = np.zeros(2, dtype=np.int64)
    w.food_tier = np.zeros(2, dtype=np.int64)                 # tier 0 (free) -> isolate the reach effect, not diet
    w.food_ripe = np.array([True, True]); w.ripe_age = np.zeros(2, dtype=np.int32)
    w.food_proc = np.full(2, -1, dtype=np.int64)
    w._eat()
    assert w.pop.energy[a] == 50.0                            # a's base reach (3) can't touch a mote at 4.5
    assert abs(w.pop.energy[b] - (50.0 + w.cfg.food_value)) < 1e-9   # b's reach node (6) harvests it


def test_tech_capabilities_test_fields_and_off_empty():
    w = GenesisWorld(_tccfg(n0=200), seed=0)
    for _ in range(120):
        w.step()
    out = w.tech_capabilities_test()
    assert {"realized_axes", "n_axes", "frac_unlocked", "mean_axes",
            "mean_speed_cap", "mean_reach", "mean_realized_speed"} <= set(out)
    assert out["n_axes"] == w.cfg.n_capabilities
    assert len(out["frac_unlocked"]) == w.cfg.n_capabilities
    assert out["mean_speed_cap"] >= w.cfg.speed and out["mean_reach"] >= w.cfg.eat_radius
    assert GenesisWorld(_tacfg(), seed=0).tech_capabilities_test() == {}   # off -> empty


def test_transmission_unlocks_capabilities_more_than_asocial():
    """The R154 claim (smoke): with social learning the population climbs to the deep capability nodes and
    physically realizes a faster, longer-reach phenotype; the asocial control stays at the base phenotype
    (speed cap == cfg.speed, reach == cfg.eat_radius — exactly, categorically)."""
    soc = GenesisWorld(_tccfg(n0=250, learn=True), seed=1)
    aso = GenesisWorld(_tccfg(n0=250, learn=False), seed=1)
    for _ in range(450):
        soc.step(); aso.step()
    s, a = soc.tech_capabilities_test(), aso.tech_capabilities_test()
    assert s["realized_axes"] > a["realized_axes"]            # transmission unlocks strictly more capability axes
    assert s["mean_speed_cap"] > a["mean_speed_cap"]          # the social population physically moves faster
    assert a["mean_speed_cap"] == soc.cfg.speed               # asocial: nobody reaches the deep locomotion node
    assert a["mean_reach"] == soc.cfg.eat_radius              # asocial: base harvest reach, categorically


def test_checkpoint_preserves_capability_phenotype(tmp_path):
    w = GenesisWorld(_tccfg(n0=150), seed=1)
    for _ in range(120):
        w.step()
    p = str(tmp_path / "ck.npz")
    w.save_checkpoint(p)
    w2 = GenesisWorld(_tccfg(n0=150), seed=9)
    w2.load_checkpoint(p)
    assert np.array_equal(w._cap_tech, w2._cap_tech)          # capability table is deterministic from the fixed tree
    assert np.allclose(w.tech_capabilities_test()["mean_speed_cap"],
                       w2.tech_capabilities_test()["mean_speed_cap"])   # realized phenotype survives a restart


# ---------- R155: COSTLY/BOUNDED capabilities -> emergent SPECIALIZATION (division of labour via the tech tree) ----------
def _cncfg(**kw):
    """The R155 regime: combinatorial-culture world + tech_capabilities + cap_niches — each capability node is
    the EXCLUSIVE key to a parallel food niche, bounded by a somatic budget (cap_budget) so lineages must
    specialize. No tech_actions: eating routes through the capability-niche path."""
    return replace(_kcfg(**kw), tech_capabilities=True, n_capabilities=2, cap_level_step=2,
                   cap_speed_mult=1.0, cap_reach_mult=1.0, cap_niches=True, cap_budget=1,
                   niche_free_frac=0.5, niche_value_bonus=1.0)


def test_cap_niches_requires_tech_capabilities():
    with pytest.raises(ValueError):
        GenesisWorld(_kcfg(cap_niches=True), seed=0)           # cap_niches without tech_capabilities=True


def test_cap_niches_off_draws_no_niche_labels_and_is_inert():
    a = GenesisWorld(_kcfg(n0=200, tech_capabilities=True, n_capabilities=2, cap_level_step=2), seed=4)
    b = GenesisWorld(_kcfg(n0=200, tech_capabilities=True, n_capabilities=2, cap_level_step=2,
                           cap_niches=False), seed=4)
    assert (a.food_niche == -1).all()                          # OFF -> every mote is FREE, no niche RNG draw
    for _ in range(60):
        a.step(); b.step()
    assert np.array_equal(a.pop.pos, b.pop.pos)                # cap_niches=False is the default -> identical run
    assert np.array_equal(a.food, b.food)


def test_food_niches_partition_into_free_and_keyed():
    w = GenesisWorld(_cncfg(n0=80, niche_free_frac=0.5), seed=2)
    niche = w.food_niche
    assert set(np.unique(niche)).issubset({-1, 0, 1})         # free (-1) + the two keyed niches
    assert (niche == -1).any() and (niche >= 0).any()         # both free and keyed motes spawn
    free_frac = float((niche == -1).mean())
    assert 0.35 < free_frac < 0.65                            # ~niche_free_frac of food is free


def test_keyed_food_needs_the_matching_capability_key():
    """The excludable-resource core: a ripe mote in keyed niche 0 is harvestable ONLY by a holder of capability
    node 0; the FREE niche is edible by anyone. A categorical key, not a payoff scalar."""
    w = GenesisWorld(_cncfg(n0=2), seed=0)
    a, b = w.pop.active()[:2]
    w.pop.energy[a] = w.pop.energy[b] = 50.0
    w.pop.spec[a] = w.pop.spec[b] = 0.0; w.pop.tech[a] = w.pop.tech[b] = 0.0
    w.rep[a] = w.rep[b] = False
    w.rep[b, w._cap_tech[0]] = True                            # only b holds the niche-0 key
    off = np.array([1.0, 0.0, 0.0])                            # within base eat radius (3)
    w.food = np.array([w.pop.pos[a] + off, w.pop.pos[b] + off])
    w.food_type = np.zeros(2, dtype=np.int64); w.food_tier = np.zeros(2, dtype=np.int64)
    w.food_niche = np.array([0, 0], dtype=np.int64)            # both motes are keyed niche 0
    w.food_ripe = np.array([True, True]); w.ripe_age = np.zeros(2, dtype=np.int32)
    w.food_proc = np.full(2, -1, dtype=np.int64)
    w._eat()
    assert w.pop.energy[a] == 50.0                             # a lacks the key -> cannot harvest keyed niche 0
    keyed_value = w.cfg.food_value * (1.0 + w.cfg.niche_value_bonus)
    assert abs(w.pop.energy[b] - (50.0 + keyed_value)) < 1e-9  # b holds the key -> harvests the richer keyed mote


def test_free_niche_is_edible_by_anyone():
    w = GenesisWorld(_cncfg(n0=1), seed=0)
    a = w.pop.active()[0]
    w.pop.energy[a] = 50.0; w.pop.spec[a] = 0.0; w.pop.tech[a] = 0.0
    w.rep[a] = False                                           # no capability keys at all
    w.food = np.array([w.pop.pos[a] + np.array([1.0, 0.0, 0.0])])
    w.food_type = np.zeros(1, dtype=np.int64); w.food_tier = np.zeros(1, dtype=np.int64)
    w.food_niche = np.array([-1], dtype=np.int64)             # the FREE niche
    w.food_ripe = np.array([True]); w.ripe_age = np.zeros(1, dtype=np.int32)
    w.food_proc = np.full(1, -1, dtype=np.int64)
    w._eat()
    assert abs(w.pop.energy[a] - (50.0 + w.cfg.food_value)) < 1e-9   # free food eaten with no key


def test_cap_budget_keep_is_parent_preferential():
    """A newborn that acquires BOTH keys but has budget 1 keeps its PARENT's key (heritable profile)."""
    w = GenesisWorld(_cncfg(n0=4), seed=0)
    cap = w._cap_tech
    w.rep[:] = False
    w.rep[0, cap[0]] = True                                    # parent 0 is a niche-0 specialist
    w.rep[1, cap[1]] = True                                    # parent 1 is a niche-1 specialist
    K = w.cfg.max_techniques
    child = np.zeros((2, K), dtype=bool)
    child[:, cap[0]] = True; child[:, cap[1]] = True          # both children acquired BOTH keys
    out = w._enforce_cap_budget(child.copy(), np.array([0, 1]))
    assert out[0, cap[0]] and not out[0, cap[1]]              # child of parent 0 keeps key 0
    assert out[1, cap[1]] and not out[1, cap[0]]              # child of parent 1 keeps key 1
    assert out[:, cap].sum(axis=1).max() <= w.cfg.cap_budget   # never exceeds the somatic budget


def test_cap_force_mono_collapses_every_profile_to_key0():
    w = GenesisWorld(_cncfg(n0=4, cap_force_mono=True), seed=0)
    cap = w._cap_tech
    K = w.cfg.max_techniques
    child = np.zeros((3, K), dtype=bool)
    child[:, cap[0]] = True; child[:, cap[1]] = True
    out = w._enforce_cap_budget(child.copy(), np.array([0, 1, 2]))
    assert out[:, cap[0]].all() and not out[:, cap[1]].any()  # monoculture: only key 0 survives


def test_cap_budget_bounds_keys_held_over_a_run():
    w = GenesisWorld(_cncfg(n0=250, cap_budget=1), seed=1)
    for _ in range(200):
        w.step()
    act = w.pop.active()
    held = w.rep[np.ix_(act, w._cap_tech)]
    assert held.sum(axis=1).max() <= 1                        # the budget is enforced for every living agent


def test_cap_specialize_test_fields_and_off_empty():
    w = GenesisWorld(_cncfg(n0=200), seed=0)
    for _ in range(150):
        w.step()
    out = w.cap_specialize_test()
    assert {"frac_per_key", "mean_keys", "profile_entropy",
            "frac_keyed", "balance", "keyed_food_frac"} <= set(out)
    assert len(out["frac_per_key"]) == w.cfg.n_capabilities
    assert out["mean_keys"] <= w.cfg.cap_budget + 1e-9
    assert GenesisWorld(_tccfg(), seed=0).cap_specialize_test() == {}   # off (no cap_niches) -> empty


def test_division_of_labour_beats_forced_monoculture():
    """The R155 headline (smoke at unit scale; the full naive-bootstrap claim is the REAL-VERIFY job). Founders
    are seeded 50/50 with the two keys (cap_skew_key0=0.5) so the dynamics — not the slow deep-node bootstrap —
    are under test: a freely-specializing MIXED population keeps BOTH keyed niches covered and out-survives a
    forced MONOCULTURE that can exploit only niche 0 (wasting niche-1 food)."""
    mix = GenesisWorld(_cncfg(n0=300, cap_skew_key0=0.5), seed=3)
    mono = GenesisWorld(_cncfg(n0=300, cap_skew_key0=0.5, cap_force_mono=True), seed=3)
    for _ in range(500):
        mix.step(); mono.step()
    cs_mix = mix.cap_specialize_test()
    assert min(cs_mix["frac_per_key"]) > 0.0                  # mixed: BOTH keyed niches stay covered
    assert cs_mix["profile_entropy"] > 0.3                    # multiple capability profiles coexist
    assert mix.pop.active().size > mono.pop.active().size     # the division of labour out-survives monoculture


# ---------- R160: cultural PHYLOGENETICS (cladistics — reconstruct a cladogram of traditions) ----------
def _phylo_tree_matrix():
    """A hand-built deme x technique matrix with a clean nested ((d0,d1),(d2,d3)) clade structure: demes 0,1
    SHARE one branch's techniques (a synapomorphy bundle), demes 2,3 share another, plus one autapomorphy
    each. The L1 distances are exactly additive on that tree -> treelikeness 1.0, coph_corr 1.0."""
    return np.array([
        [1, 1, 0, 0, 1, 0, 0, 0],   # deme0: branchA + autapomorphy0
        [1, 1, 0, 0, 0, 1, 0, 0],   # deme1: branchA + autapomorphy1
        [0, 0, 1, 1, 0, 0, 1, 0],   # deme2: branchB + autapomorphy2
        [0, 0, 1, 1, 0, 0, 0, 1],   # deme3: branchB + autapomorphy3
    ], dtype=float)


def test_phylogeny_metric_integrity_on_known_tree():
    """A perfectly tree-additive distance matrix returns treelikeness 1.0 and cophenetic correlation 1.0;
    a degenerate STAR (all pairs equidistant) has no quartet information -> treelikeness is nan."""
    from alife.genesis import phylogeny as ph
    f = _phylo_tree_matrix()
    dist = ph.l1_distance_matrix(f)
    # the nested structure makes within-clade pairs close (2/8) and across-clade pairs far (6/8)
    assert dist[0, 1] == pytest.approx(2 / 8) and dist[2, 3] == pytest.approx(2 / 8)
    assert dist[0, 2] == pytest.approx(6 / 8) and dist[1, 3] == pytest.approx(6 / 8)
    assert ph.treelikeness(dist) == pytest.approx(1.0)        # additive quartet -> delta 0
    assert ph.cophenetic_corr(dist) == pytest.approx(1.0)     # ultrametric -> UPGMA fits exactly
    star = np.full((4, 4), 2.0); np.fill_diagonal(star, 0.0)
    assert np.isnan(ph.treelikeness(star))                    # all sums equal -> no information


def test_phylogeny_column_shuffle_destroys_tree_signal():
    """The load-bearing null: shuffling each technique independently across demes preserves every technique's
    frequency but destroys the clade bundling -> mean treelikeness drops well below the real nested matrix's
    1.0. This is what isolates a phylogenetic signal from mere divergence."""
    from alife.genesis import phylogeny as ph
    f = _phylo_tree_matrix()
    real = ph.treelikeness(ph.l1_distance_matrix(f))
    null = ph.column_shuffle_null(f, n_shuffle=50)
    assert real == pytest.approx(1.0)
    assert null["treelikeness"] < real - 0.05                 # shuffle is measurably less tree-like
    assert ph.informative_columns(f).sum() == 8               # every column varies across the 4 demes


def test_phylogeny_test_fields_and_off_empty():
    """phylogeny_test returns the tree-signal fields on the combinatorial substrate and is empty without it."""
    w = GenesisWorld(_ecocfg(n0=500, spatial_tiers=True), seed=0)
    for _ in range(250):
        w.step()
    out = w.phylogeny_test(grid=3, min_deme=12, n_shuffle=8)
    assert {"treelikeness", "coph_corr", "shuffle_treelikeness", "shuffle_coph", "n_demes", "dist"} <= set(out)
    if out["n_demes"] >= 4:
        assert -1.0 <= out["coph_corr"] <= 1.0001
        assert len(out["dist"]) == out["n_demes"]
    assert GenesisWorld(_ccfg(), seed=0).phylogeny_test() == {}   # scalar (non-combinatorial) culture -> empty


def test_phylogeny_signal_beats_shuffle_on_substrate():
    """R160 headline (smoke, 2 seeds): on the R157 ecological-selection substrate the reconstructed cladogram of
    demes is MORE tree-like than the column-shuffle null (real treelikeness > shuffle) -> the cultural
    divergence is hierarchically structured (descent-with-modification), not flat. Magnitude + the cladogram
    render + the panmictic causal contrast are the REAL-VERIFY headline (scripts/run_genesis_phylogeny.py)."""
    wins = 0
    for seed in (0, 1):
        w = GenesisWorld(_ecocfg(n0=600, spatial_tiers=True), seed=seed)
        for _ in range(450):
            w.step()
        out = w.phylogeny_test(grid=3, min_deme=12, n_shuffle=20)
        if out.get("n_demes", 0) >= 4 and not np.isnan(out["treelikeness"]):
            if out["treelikeness"] > out["shuffle_treelikeness"]:
                wins += 1
    assert wins >= 1                                          # at least one seed shows a real tree signal


# --- R161: GROUND-TRUTH cultural cladistics (does the cladogram recover the true descent?) ---

def _balanced_forest():
    """A clean balanced bifurcating birth tree, append-ordered (parent id < child id):
    one root 0; children 1,2; grandchildren 3,4 (of 1) and 5,6 (of 2). Patristic distances are exact and
    known: siblings 3,4 are 2 apart; 3 vs 5 (cousins under the same root) are 4 apart."""
    return np.array([-1, 0, 0, 1, 1, 2, 2], dtype=np.int64)


def test_genealogy_depths_and_patristic_on_known_tree():
    from alife.genesis import genealogy as gn
    parent = _balanced_forest()
    depth = gn.build_depths(parent)
    assert depth.tolist() == [0, 1, 1, 2, 2, 2, 2]
    P = gn.patristic_distance_matrix(parent, np.array([3, 4, 5, 6]))
    # 3,4 are siblings (LCA=1, depth1) -> 2+2-2*1 = 2; 3,5 share only root (depth0) -> 2+2-0 = 4
    assert P[0, 1] == pytest.approx(2.0) and P[2, 3] == pytest.approx(2.0)
    assert P[0, 2] == pytest.approx(4.0) and P[1, 3] == pytest.approx(4.0)
    assert np.allclose(P, P.T) and np.allclose(np.diag(P), 0.0)


def test_genealogy_cross_founder_uses_virtual_root():
    """Two separate founder trees (a forest) are joined at a virtual super-root at depth -1, so a cross-founder
    pair's patristic distance = depth[a]+depth[b]+2 (strictly greater than any within-tree pair)."""
    from alife.genesis import genealogy as gn
    parent = np.array([-1, 0, -1, 2], dtype=np.int64)         # tree A: 0->1 ; tree B: 2->3
    P = gn.patristic_distance_matrix(parent, np.array([1, 3]))
    assert P[0, 1] == pytest.approx(1 + 1 + 2)                # depth1 + depth1 - 2*(-1)


def test_mantel_recovers_and_rejects():
    """Mantel correlation is ~1 when the reconstructed matrix equals the true one, and the label-permutation
    null sits near 0 with the observed far above it; an unrelated matrix gives a low z."""
    from alife.genesis import genealogy as gn
    rng = np.random.default_rng(0)
    d_true = rng.random((6, 6)); d_true = d_true + d_true.T; np.fill_diagonal(d_true, 0.0)
    assert gn.mantel_corr(d_true, d_true) == pytest.approx(1.0)
    mt = gn.mantel_test(d_true, d_true, n_perm=200, seed=1)
    assert mt["corr"] == pytest.approx(1.0) and mt["z"] > 3 and mt["p"] <= 0.02
    other = rng.random((6, 6)); other = other + other.T; np.fill_diagonal(other, 0.0)
    assert abs(gn.mantel_corr(d_true, other)) < 0.9           # an unrelated matrix is not perfectly correlated


def test_partial_mantel_removes_a_shared_confound():
    """Partial Mantel controlling for a confound: when two matrices are correlated ONLY because both track a
    third (control) matrix, the full Mantel is high but the partial Mantel ~ 0 (the spurious association is
    removed). When they share signal BEYOND the control, the partial stays positive. This is the
    isolation-by-distance red-team: does cultural distance track genealogy beyond shared spatial structure?"""
    from alife.genesis import genealogy as gn
    rng = np.random.default_rng(3)
    def sym(n):
        m = rng.random((n, n)); m = m + m.T; np.fill_diagonal(m, 0.0); return m
    n = 12
    ctrl = sym(n)
    # both d1 and d2 = ctrl + INDEPENDENT noise -> high full Mantel, ~0 partial (conditionally independent)
    d1 = ctrl + 0.15 * sym(n)
    d2 = ctrl + 0.15 * sym(n)
    assert gn.mantel_corr(d1, d2) > 0.6                        # spuriously correlated via the shared control
    assert abs(gn.partial_mantel_corr(d1, d2, ctrl)) < 0.3     # ...but the partial removes it
    pt = gn.partial_mantel_test(d1, d2, ctrl, n_perm=200, seed=1)
    assert pt["p"] > 0.05                                      # not significant once space is controlled
    # now give them shared signal BEYOND the control -> partial recovers it
    shared = sym(n)
    e1 = ctrl + shared + 0.1 * sym(n)
    e2 = ctrl + shared + 0.1 * sym(n)
    assert gn.partial_mantel_corr(e1, e2, ctrl) > 0.5
    pt2 = gn.partial_mantel_test(e1, e2, ctrl, n_perm=200, seed=1)
    assert pt2["z"] > 3 and pt2["p"] <= 0.02


def test_genealogy_phylogeny_test_reports_partial_mantel_and_spatial():
    """genealogy_phylogeny_test now also returns an inter-deme spatial distance matrix and a partial Mantel
    (cultural vs genealogical controlling for space). Fields present and well-shaped on a live run."""
    w = GenesisWorld(_ecocfg(n0=850, spatial_tiers=False, recipe_budget=2, tier0_frac=0.8,
                             track_genealogy=True, vertical_only=True), seed=0)
    for _ in range(200):
        w.step()
    o = w.genealogy_phylogeny_test(grid=3, min_deme=12, sample_per_deme=10, n_perm=99)
    if o.get("n_demes", 0) >= 4:
        D = o["n_demes"]
        assert np.array(o["d_spatial"]).shape == (D, D)
        assert "partial_mantel_corr" in o and "partial_mantel_p" in o


def test_track_genealogy_is_byte_identical_off_vs_on():
    """track_genealogy is a PASSIVE observer (no RNG, no state change): the sim trajectory must be identical
    whether it is on or off. Compare positions + energy + repertoire after a run."""
    base = dict(n0=400, spatial_tiers=True)
    off = GenesisWorld(_ecocfg(**base, track_genealogy=False), seed=0)
    on = GenesisWorld(_ecocfg(**base, track_genealogy=True), seed=0)
    for _ in range(120):
        off.step(); on.step()
    a, b = off.pop.active(), on.pop.active()
    assert np.array_equal(a, b)
    assert np.allclose(off.pop.pos[a], on.pop.pos[b])
    assert np.allclose(off.pop.energy[a], on.pop.energy[b])
    assert np.array_equal(off.rep[a], on.rep[b])


def test_genealogy_log_grows_and_maps_living_agents():
    """With tracking on, every living agent maps to a valid genealogy node and the parent log is append-ordered
    (each child's parent id is smaller than the child's own id -> a valid forest)."""
    w = GenesisWorld(_ecocfg(n0=400, spatial_tiers=True, track_genealogy=True), seed=0)
    for _ in range(150):
        w.step()
    act = w.pop.active()
    nodes = w._gen_node[act]
    assert (nodes >= 0).all() and nodes.max() < len(w._gen_parent)
    parent = np.array(w._gen_parent)
    children = np.where(parent >= 0)[0]
    assert (parent[children] < children).all()                # append-ordered: parent precedes child


def test_genealogy_phylogeny_test_fields_and_gating():
    """genealogy_phylogeny_test returns the Mantel/ground-truth fields on the tracked substrate, is empty
    without track_genealogy, and its Mantel correlation is a valid number in [-1, 1] when >=4 demes form."""
    w = GenesisWorld(_ecocfg(n0=600, spatial_tiers=True, track_genealogy=True), seed=0)
    for _ in range(300):
        w.step()
    out = w.genealogy_phylogeny_test(grid=3, min_deme=12, sample_per_deme=10, n_perm=200)
    assert {"mantel_corr", "mantel_null_mean", "mantel_z", "mantel_p", "n_demes", "d_cult", "d_gen"} <= set(out)
    if out["n_demes"] >= 4 and not np.isnan(out["mantel_corr"]):
        assert -1.0001 <= out["mantel_corr"] <= 1.0001
        assert len(out["d_gen"]) == out["n_demes"] == len(out["d_cult"])
    # gated off without tracking
    w2 = GenesisWorld(_ecocfg(n0=400, spatial_tiers=True, track_genealogy=False), seed=0)
    for _ in range(20):
        w2.step()
    assert w2.genealogy_phylogeny_test() == {}


def test_vertical_only_off_is_deterministic_default_on_changes_world():
    """vertical_only=False uses the exact default oblique-transmission code path (deterministic: two runs
    match). vertical_only=True disables nearest-hearth copying so newborns inherit only the parent's
    repertoire + innovation; that changed culture feeds harvest/energy, so the realized population genuinely
    diverges from the horizontal-transmission run (a real regime change, NOT a passive observer)."""
    base = dict(n0=400, spatial_tiers=True, track_genealogy=True)
    off = GenesisWorld(_ecocfg(**base, vertical_only=False), seed=0)
    ref = GenesisWorld(_ecocfg(**base, vertical_only=False), seed=0)
    on = GenesisWorld(_ecocfg(**base, vertical_only=True), seed=0)
    for _ in range(150):
        off.step(); ref.step(); on.step()
    a, r = off.pop.active(), ref.pop.active()
    assert np.array_equal(a, r) and np.array_equal(off.rep[a], ref.rep[r])   # default path is deterministic
    # vertical-only diverges (culture -> survival feedback); at minimum its mean repertoire differs
    assert not np.allclose(off.rep[off.pop.active()].mean(0), on.rep[on.pop.active()].mean(0))


# ---------- R164: GENUINELY UNBOUNDED generative tech space ----------
def test_unbounded_combine_materializes_and_dedups():
    from alife.genesis import unbounded as ub
    s = ub.TechSpace(n_seed=4)
    assert s.n == 4
    k = s.combine(0, 1, step=5)
    assert k == 4 and s.n == 5
    assert s.levels[k] == 1 and s.parents[k] == (0, 1) and s.first_step[k] == 5
    assert s.combine(1, 0, step=9) == k and s.n == 5            # same pair (order-free) -> same id, no growth


def test_unbounded_level_is_composition_depth():
    from alife.genesis import unbounded as ub
    s = ub.TechSpace(n_seed=4)
    a = s.combine(0, 1)                                          # level 1
    b = s.combine(a, 2)                                          # 1 + max(1,0) = 2
    c = s.combine(a, b)                                          # 1 + max(1,2) = 3
    assert s.levels[a] == 1 and s.levels[b] == 2 and s.levels[c] == 3
    with pytest.raises(ValueError):
        s.combine(a, a)                                          # cannot compose with itself


def test_unbounded_chain_len_equals_level_invariant():
    """The cumulative-descent invariant: a level-L technique descends through exactly L compositions from
    the seeds. chain_len (computed by recursion on parents) must equal level for every materialized node."""
    from alife.genesis import unbounded as ub
    out = ub.run_population(n_agents=20, n_seed=5, steps=60, fidelity=0.5, seed=3)
    s = out["space"]
    assert s.n > 50                                             # the space actually grew well past the seeds
    assert all(s.chain_len(k) == s.levels[k] for k in range(s.n))


def test_cap_freezes_the_space():
    from alife.genesis import unbounded as ub
    s = ub.TechSpace(n_seed=4, cap=6)
    assert s.combine(0, 1) == 4
    assert s.combine(0, 2) == 5
    assert s.n == 6
    assert s.combine(1, 2) is None                              # full -> refuses to materialize a new one
    assert s.combine(0, 1) == 4                                 # but an EXISTING pair still resolves
    assert s.n == 6


def test_unbounded_depth_climbs_without_plateau():
    """Open-endedness: frontier depth keeps rising across the run — the last third climbs strictly more than
    a flat line would, i.e. there is no asymptote within the run."""
    from alife.genesis import unbounded as ub
    out = ub.run_population(n_agents=40, n_seed=6, steps=150, fidelity=0.5, cap=None, seed=1)
    ml = out["max_level"]
    third = len(ml) // 3
    early_gain = ml[third] - ml[0]
    late_gain = ml[-1] - ml[2 * third]
    assert ml[-1] > ml[third] > ml[0]                          # monotone climb across thirds
    assert late_gain > 0                                       # still climbing in the final third -> no plateau


def test_capped_plateaus_and_unbounded_beats_it():
    """The decisive control: IDENTICAL dynamics/seed, the ONLY difference is the cap. The capped run's depth
    freezes once the registry fills; the uncapped run climbs far past it."""
    from alife.genesis import unbounded as ub
    cap_k = 80
    capped = ub.run_population(n_agents=40, n_seed=6, steps=150, fidelity=0.5, cap=cap_k, seed=1)
    free = ub.run_population(n_agents=40, n_seed=6, steps=150, fidelity=0.5, cap=None, seed=1)
    assert capped["n_distinct"][-1] == cap_k                   # capped fills exactly to the cap
    assert free["n_distinct"][-1] > 5 * cap_k                  # uncapped materializes a far larger space
    # capped depth plateaus: no gain in the final third once the space is full
    cm = capped["max_level"]
    third = len(cm) // 3
    assert cm[-1] == cm[2 * third]                             # frozen
    assert free["max_level"][-1] > capped["max_level"][-1]     # uncapped frontier is strictly deeper


def test_unbounded_temporal_ladder_holds():
    """Over the unbounded climb the temporal ladder persists: deeper techniques appear later (positive
    level<->first_step Spearman) — the R163 ladder survives lifting the ceiling."""
    from alife.genesis import unbounded as ub
    from alife.genesis.phylogeny import _spearman
    out = ub.run_population(n_agents=40, n_seed=6, steps=150, fidelity=0.5, seed=2)
    first, lvl = ub.ladder_arrays(out["space"])
    assert first.size > 100
    assert _spearman(lvl, first) > 0.3                         # deeper == later, robustly


def test_unbounded_run_is_deterministic():
    from alife.genesis import unbounded as ub
    a = ub.run_population(n_agents=30, n_seed=5, steps=80, fidelity=0.5, seed=7)
    b = ub.run_population(n_agents=30, n_seed=5, steps=80, fidelity=0.5, seed=7)
    assert np.array_equal(a["max_level"], b["max_level"])
    assert np.array_equal(a["n_distinct"], b["n_distinct"])


# ---------------------------------------------------------------------------
# R165 — PHYLORATE: the RATE law of cumulative innovation (additive saturates,
# fixed-effort linear, autocatalytic+open super-linear, autocatalytic+capped collapses)
# ---------------------------------------------------------------------------

def test_phylorate_additive_saturates():
    """Independent invention from a FIXED pool decelerates: cumulative N approaches pool_size and the
    per-step rate falls (negative acceleration)."""
    from alife.genesis import phylorate as pr
    out = pr.run_additive(steps=200, base=40, pool_size=500, seed=0)
    assert out["n_distinct"][-1] <= 500
    assert out["n_distinct"][-1] > 400                          # gets most of the pool
    assert pr.acceleration(out["step"], out["n_distinct"]) < 0  # decelerating


def test_phylorate_fixed_is_linear():
    """Fixed-effort combinatorial on the open space: constant rate -> near-zero curvature, and the
    per-step novelty stays close to `base` (collisions are rare on an open space)."""
    from alife.genesis import phylorate as pr
    out = pr.run_fixed(steps=200, base=40, seed=0)
    acc = pr.acceleration(out["step"], out["n_distinct"])
    # essentially flat rate: |curvature| tiny vs the additive saturation curvature
    assert abs(acc) < 0.05
    assert out["new"][50:].mean() > 0.8 * 40                    # ~base novelties/step sustained


def test_phylorate_autocatalytic_open_is_superlinear():
    """Autocatalytic effort on the OPEN space -> rate RISES with N (accelerating, super-linear)."""
    from alife.genesis import phylorate as pr
    out = pr.run_autocatalytic(steps=22, base=10, alpha=0.5, cap=None, seed=0)
    assert pr.acceleration(out["step"], out["n_distinct"]) > 0  # accelerating
    centers, rate = pr.rate_vs_size(out, bins=6)
    assert rate[-1] > 3 * rate[0]                               # rate grows with size
    # exponential growth: late power-law exponent is well above linear
    assert pr.growth_exponent(out["step"], out["n_distinct"], frac=0.5) > 1.5


def test_phylorate_autocatalytic_open_collision_falls():
    """The non-trivial result: on the open space the collision fraction FALLS as N grows (pair-space
    grows as N^2 while discoveries grow as N), so the adjacent possible stays fed."""
    from alife.genesis import phylorate as pr
    out = pr.run_autocatalytic(steps=22, base=10, alpha=0.5, cap=None, seed=0)
    early = out["collision_frac"][2:6].mean()
    late = out["collision_frac"][-5:].mean()
    assert late <= early + 1e-9                                 # collisions do not grow; stay low/fall
    assert late < 0.3


def test_phylorate_autocatalytic_capped_collapses():
    """DECISIVE control: identical alpha*N effort but a CAPPED space -> once full, every attempt
    collides (collision_frac -> ~1) and the rate collapses to 0, despite the unchanged effort law.
    So sustained super-linearity is the OPEN adjacent possible, not the effort multiplier alone."""
    from alife.genesis import phylorate as pr
    cap_k = 300
    out = pr.run_autocatalytic(steps=22, base=10, alpha=0.5, cap=cap_k, seed=0)
    assert out["n_distinct"][-1] == cap_k                       # frozen at the ceiling
    assert out["new"][-3:].sum() == 0                           # no novelties once full
    assert out["collision_frac"][-1] > 0.9                      # nearly all attempts collide


def test_phylorate_capped_vs_open_decisive():
    """Same effort law, only the space differs: open keeps climbing far past the cap; capped freezes."""
    from alife.genesis import phylorate as pr
    cap_k = 300
    openrun = pr.run_autocatalytic(steps=22, base=10, alpha=0.5, cap=None, seed=1)
    capped = pr.run_autocatalytic(steps=22, base=10, alpha=0.5, cap=cap_k, seed=1)
    assert openrun["n_distinct"][-1] > 5 * capped["n_distinct"][-1]


def test_phylorate_deterministic():
    from alife.genesis import phylorate as pr
    a = pr.run_autocatalytic(steps=18, base=10, alpha=0.5, seed=4)
    b = pr.run_autocatalytic(steps=18, base=10, alpha=0.5, seed=4)
    assert np.array_equal(a["n_distinct"], b["n_distinct"])
    assert np.array_equal(a["new"], b["new"])


# --- R166: LIVE phylorate — the rate law emerges from the live economy ---

def _live_combinatorial_cfg(tech_gain: float, capacity: int = 1500):
    """A small but real combinatorial GenesisWorld for fast live-trajectory tests. capacity must leave
    the economy room to grow a bigger workforce than the decoupled control (a tighter cap clips both
    regimes at the same ceiling and the endogenous contrast vanishes)."""
    from alife.world3d import World3D
    return replace(GenesisConfig(world=World3D(size=60.0), n0=120, capacity=capacity),
                   processing=True, building=True, culture=True, combinatorial=True,
                   max_techniques=400, n_seed_tech=8, innov_steps=1,
                   hearth_reach_per_strength=3.0, hearth_radius=12.0, tech_gain=tech_gain)


def test_rate_slope_sign_on_synthetic_trajectories():
    """rate_slope is the live discriminator: a rising-rate trajectory -> positive, a flat one -> ~0."""
    from alife.genesis import livephylorate as lp
    steps = np.arange(1, 41)
    # rising rate: discoveries per step grow with cumulative N (autocatalytic-like)
    rising_new = np.maximum(1, (steps // 3)).astype(int)
    rising = {"step": steps, "n_distinct": np.cumsum(rising_new), "new": rising_new}
    # flat rate: constant discoveries per step
    flat_new = np.full(steps.size, 4, dtype=int)
    flat = {"step": steps, "n_distinct": np.cumsum(flat_new), "new": flat_new}
    assert lp.rate_slope(rising, bins=6) > 0
    assert abs(lp.rate_slope(flat, bins=6)) < 1e-6


def test_step_trajectory_shape_and_determinism():
    """step_trajectory emits the phylorate-shaped keys, N is non-decreasing, and it is deterministic."""
    from alife.genesis.genesis import GenesisWorld
    from alife.genesis import livephylorate as lp
    w1 = GenesisWorld(_live_combinatorial_cfg(0.35), seed=0)
    o1 = lp.step_trajectory(w1, 30)
    assert set(o1) == {"step", "n_distinct", "new", "active"}
    assert o1["n_distinct"].size == 30
    assert np.all(np.diff(o1["n_distinct"]) >= 0)           # cumulative repertoire never shrinks
    assert np.all(o1["new"] >= 0)
    w2 = GenesisWorld(_live_combinatorial_cfg(0.35), seed=0)
    o2 = lp.step_trajectory(w2, 30)
    assert np.array_equal(o1["n_distinct"], o2["n_distinct"])  # same seed -> byte-identical trajectory


def test_live_economy_accelerates_vs_decoupled_control():
    """HEADLINE smoke: with mastery paying energy (tech_gain>0) the live world accumulates a larger
    repertoire than the decoupled control (tech_gain=0) on the SAME combinatorial machinery — the
    endogenous economy feeds the innovation. (The full rising-vs-flat rate contrast is the REAL-VERIFY
    run; this is the fast deterministic smoke.)"""
    from alife.genesis.genesis import GenesisWorld
    from alife.genesis import livephylorate as lp
    econ = lp.step_trajectory(GenesisWorld(_live_combinatorial_cfg(0.35), seed=0), 300)
    ctrl = lp.step_trajectory(GenesisWorld(_live_combinatorial_cfg(0.0), seed=0), 300)
    assert econ["n_distinct"][-1] > ctrl["n_distinct"][-1]
    assert econ["active"].max() > ctrl["active"].max()      # the economy grows a bigger workforce


# --- R167: TECH DEPTH — connected cumulative DAG vs flat scatter ---

def test_closure_and_connected_depth_on_a_known_chain():
    """A hand-built tree: connected_depth counts the longest fully-known prereq chain; a missing prereq
    breaks it; closure is the fraction of known non-seed techniques standing on known prereqs."""
    from alife.genesis import combinatorial as cb
    from alife.genesis import techdepth as td
    # seeds 0,1 (level 0); 2 = f(0,1) lvl1; 3 = f(2,0) lvl2; 4 = f(3,1) lvl3
    pa = np.array([-1, -1, 0, 2, 3], dtype=np.int64)
    pb = np.array([-1, -1, 1, 0, 1], dtype=np.int64)
    level = np.array([0, 0, 1, 2, 3], dtype=np.int64)
    n_seed = 2
    full = np.array([True, True, True, True, True])
    assert td.connected_depth(full, pa, pb, level, n_seed) == 3      # 0/1 -> 2 -> 3 -> 4
    assert td.closure_fraction(full, pa, pb, n_seed) == 1.0          # every non-seed has both prereqs
    # drop technique 2 (a prereq of 3): 3's chain breaks (cd 0); 4=f(3,1) still has both prereqs known
    # so it stands one rung up on a broken foundation -> connected depth collapses from 3 to 1
    broken = np.array([True, True, False, True, True])
    assert td.connected_depth(broken, pa, pb, level, n_seed) == 1    # 4 on (known 3, known 1); 3 rootless
    assert td.closure_fraction(broken, pa, pb, n_seed) == 0.5        # known non-seed {3,4}: only 4 prereq-closed


def test_connected_depth_array_matches_level_when_fully_closed():
    """On a fully-known repertoire, connected depth equals the tree level (the chain is intact end-to-end)."""
    from alife.genesis import combinatorial as cb
    from alife.genesis import techdepth as td
    pa, pb, level = cb.build_tech_tree(80, 6)
    known = np.ones(80, dtype=bool)
    cd = td.connected_depth_array(known, pa, pb, level, 6)
    assert np.array_equal(cd, level)                                 # closed DAG: connected depth == level


def test_additive_null_is_broad_but_disconnected():
    """The structural HEADLINE as a fast deterministic smoke: same machinery, same tree, the ONLY change is
    combo_prereqs. Combinatorial discovery yields a prereq-closed deep CONNECTED DAG; the additive null
    reaches a comparable nominal depth but a DISCONNECTED scatter — high max_level, collapsed connected depth
    and low closure. (The full multi-seed contrast is the REAL-VERIFY run.)"""
    from alife.genesis.genesis import GenesisWorld
    from alife.genesis import techdepth as td
    # a tree large enough that the additive null stays a sparse SUBSET (so the structure is visible, not a
    # saturated tree where everything-known is trivially closed).
    cfg = replace(_live_combinatorial_cfg(0.35), max_techniques=8000)
    oc = td.depth_trajectory(GenesisWorld(cfg, seed=0), 200)
    oa = td.depth_trajectory(GenesisWorld(replace(cfg, combo_prereqs=False), seed=0), 200)
    # by BREADTH and NOMINAL depth the additive null looks MORE advanced -- it is broader and reaches a
    # higher tree level, because it discovers without respecting prerequisites.
    assert oa["breadth"][-1] > oc["breadth"][-1]
    assert oa["max_level"][-1] >= oc["max_level"][-1]
    # but the STRUCTURE inverts the verdict: combinatorial is a prereq-closed CONNECTED ladder, the additive
    # scatter is broken -- low closure and a collapsed connected depth despite its higher nominal level.
    assert oc["closure"][-1] > 0.9
    assert oc["conn_depth"][-1] >= 0.8 * oc["max_level"][-1]
    assert oa["closure"][-1] < 0.5
    assert oa["conn_depth"][-1] < oc["conn_depth"][-1]


def test_depth_trajectory_shape_and_determinism():
    """depth_trajectory emits the documented keys, is the right length, and is byte-identical per seed."""
    from alife.genesis.genesis import GenesisWorld
    from alife.genesis import techdepth as td
    o1 = td.depth_trajectory(GenesisWorld(_live_combinatorial_cfg(0.35), seed=1), 40)
    assert set(o1) == {"step", "breadth", "max_level", "conn_depth", "closure", "active"}
    assert o1["conn_depth"].size == 40
    assert np.all(o1["conn_depth"] <= o1["max_level"])              # connected depth never exceeds nominal
    o2 = td.depth_trajectory(GenesisWorld(_live_combinatorial_cfg(0.35), seed=1), 40)
    assert np.array_equal(o1["conn_depth"], o2["conn_depth"])


def test_civ_config_is_full_stack_and_deterministic():
    """civ_config builds the viable full civilization regime (building+culture+combinatorial+tech-actions+
    capabilities) and the world is byte-identical per seed."""
    from alife.genesis import civdev
    cfg = civdev.civ_config()
    assert cfg.building and cfg.culture and cfg.combinatorial and cfg.tech_actions and cfg.tech_capabilities
    a = civdev.develop_trajectory(GenesisWorld(civdev.civ_config(), seed=3), 60)
    b = civdev.develop_trajectory(GenesisWorld(civdev.civ_config(), seed=3), 60)
    assert np.array_equal(a["conn_depth"], b["conn_depth"])
    assert np.array_equal(a["breadth"], b["breadth"])


def test_develop_trajectory_keys_and_capability_color():
    """develop_trajectory emits the documented civilization signals; capability_color is a valid RGB per agent
    within the locked->unlocked palette."""
    from alife.genesis import civdev
    o = civdev.develop_trajectory(GenesisWorld(civdev.civ_config(), seed=0), 50, every=10)
    assert set(o) == {"step", "population", "conn_depth", "closure", "breadth",
                      "realized_axes", "edible_tiers", "diversity", "max_gen"}
    assert o["conn_depth"].size == 5
    col = civdev.capability_color(GenesisWorld(civdev.civ_config(), seed=0))  # before any step: base phenotype
    assert col.ndim == 2 and col.shape[1] == 3
    assert col.min() >= 0.0 and col.max() <= 1.0


def test_full_civilization_develops_only_with_social_learning():
    """The R168 falsifiable HEADLINE as a fast deterministic check: same world, same physics, the ONLY change
    is whether culture is transmitted. The full stack (social learning + evolution) DEVELOPS — a deep connected
    tech ladder, unlocked physical capability axes, and a broadened edible diet — while the ASOCIAL control
    (learn=False) cannot accumulate and stays at the seed floor. (The multi-seed render is the REAL-VERIFY.)"""
    from alife.genesis import civdev
    out = civdev.develop_vs_control(300, seed=0, every=25)
    f, c = out["full"], out["control"]
    # the civilization develops a CONNECTED cumulative tech ladder; the asocial control never climbs it.
    assert f["conn_depth"][-1] >= 5
    assert f["conn_depth"][-1] > c["conn_depth"][-1]
    # culture unlocks EMBODIED capability: more physical axes and a wider edible diet than the control.
    assert f["realized_axes"][-1] > c["realized_axes"][-1]
    assert f["edible_tiers"][-1] > c["edible_tiers"][-1] + 0.5


def test_persist_resume_is_bit_for_bit_continuous(tmp_path):
    """R169 FALSIFIABLE HEADLINE: a chain of resumed segments — each a freshly-built world that loads the
    previous checkpoint (simulated process death) — yields a development trajectory BIT-FOR-BIT IDENTICAL
    to one uninterrupted run of the same total length. Proves resume is lossless: process death is invisible
    to the civilization's development. If any stepped state or RNG were not restored, the arrays would diverge."""
    from alife.genesis import civdev, persist
    cfg = civdev.civ_config()
    cont = persist.continuous_trajectory(cfg, seed=1, total_steps=120, log_every=20)
    chain = persist.chained_trajectory(cfg, seed=1, n_segments=3, segment_steps=40,
                                       ckpt_path=str(tmp_path / "ck.npz"), log_every=20)
    # the world actually developed in the window (a trivial flat trajectory would pass continuity vacuously).
    assert cont["step"].size == chain["step"].size >= 4
    assert cont["breadth"][-1] > cont["breadth"][0]
    for k in persist._KEYS:
        assert np.array_equal(cont[k], chain[k], equal_nan=True), f"resume diverged on {k}"
    assert persist.continuity_max_abs_diff(cont, chain) == 0.0


def test_run_segment_extends_persistent_world_on_disk(tmp_path):
    """run_segment is the persistent driver primitive: each call loads the latest on-disk checkpoint +
    rolling trajectory and extends BOTH by one segment. The first call bootstraps; later calls resume and
    the global step strictly advances; the on-disk trajectory grows monotonically in step and never resets."""
    from alife.genesis import civdev, persist
    cfg = civdev.civ_config()
    sd = str(tmp_path / "world")
    r1 = persist.run_segment(sd, cfg, seed=2, segment_steps=40, log_every=20)
    assert r1["bootstrap"] and r1["start_step"] == 0 and r1["end_step"] == 40
    r2 = persist.run_segment(sd, cfg, seed=2, segment_steps=40, log_every=20)
    assert (not r2["bootstrap"]) and r2["start_step"] == 40 and r2["end_step"] == 80
    traj = persist.load_trajectory(sd)
    assert traj["step"][0] == 0.0 and traj["step"][-1] == 80.0
    assert np.all(np.diff(traj["step"]) > 0)            # strictly increasing, no duplicated boundary sample
    # the on-disk trajectory IS the live record a rolling panel reads — it must reflect real development.
    assert traj["breadth"][-1] >= traj["breadth"][0]


def test_persist_continuity_proof_is_not_vacuous(tmp_path):
    """R169 RED-TEAM as a permanent control: the bit-for-bit continuity proof is CAUSED by lossless checkpoint
    reload, not by a fresh world being reconstructable from the seed alone. Two load-bearing negative controls
    that make checkpoint reload the ONLY difference MUST break continuity: (A) rebuild a fresh world at each
    boundary but DON'T reload the checkpoint (step resets) -> diverges; (B) reload a DIFFERENT-seed checkpoint
    -> diverges. If either matched the uninterrupted run, the proof would be vacuous."""
    from alife.genesis import civdev, persist
    from alife.genesis.genesis import GenesisWorld
    cfg = civdev.civ_config()
    total, seg, le = 120, 40, 20
    cont = persist.continuous_trajectory(cfg, seed=1, total_steps=total, log_every=le)

    def boundary_chain(reload_fn):
        samples, w = [], GenesisWorld(cfg, seed=1, evolve=True)
        while w.step_count < total:
            if w.step_count % le == 0:
                samples.append(persist._observe(w))
            if w.step_count > 0 and w.step_count % seg == 0:
                del w
                w = GenesisWorld(cfg, seed=1, evolve=True)
                reload_fn(w)
            w.step()
        return persist._stack(samples)

    # control A: no reload -> step_count resets each segment, so the sampled history diverges.
    no_load = boundary_chain(lambda w: None)
    assert persist.continuity_max_abs_diff(cont, no_load) > 0.0

    # control B: reload a checkpoint built from a DIFFERENT seed -> mid-stream state is wrong -> diverges.
    wrong = GenesisWorld(cfg, seed=999, evolve=True)
    for _ in range(seg):
        wrong.step()
    wrong_path = str(tmp_path / "wrong.npz")
    wrong.save_checkpoint(wrong_path)
    wrong_chain = boundary_chain(lambda w: w.load_checkpoint(wrong_path))
    assert persist.continuity_max_abs_diff(cont, wrong_chain) > 0.0


# ---------- R171: DEPTH GATES — open-ended culture causally drives EMBODIED capability ----------
def _depth_gate_cfg(K, innov_steps=3):
    """A full-stack viable generative world whose diet tiers + capability axes are gated on cultural DEPTH."""
    from alife.genesis.civdev import civ_config
    return civ_config(
        tech_actions=False, tech_capabilities=False, generative_tree=True, depth_gates=True,
        max_techniques=K, innov_steps=innov_steps, n_food_tiers=5, recipe_level_step=2,
        n_capabilities=2, cap_level_step=2, tier0_frac=0.4,
        n0=300, capacity=1000, food_cap=600, food_regrow=40)


def test_depth_gates_requires_generative_tree():
    """depth_gates gates on the GROWN tree's depth, so it is meaningless without it -> must raise."""
    from alife.genesis.civdev import civ_config
    cfg = civ_config(tech_actions=False, tech_capabilities=False, generative_tree=False, depth_gates=True)
    with pytest.raises(ValueError, match="depth_gates"):
        GenesisWorld(cfg, seed=1)


def test_depth_gates_off_leaves_food_unlocked_and_is_byte_identical():
    """depth_gates=False adds NO RNG and no tiers: food_tier all-zero and the generative trajectory is
    bit-for-bit identical to the same world without the flag (the off path is a true no-op)."""
    from alife.genesis.civdev import civ_config
    base = dict(tech_actions=False, tech_capabilities=False, generative_tree=True, max_techniques=2000,
                innov_steps=2, n0=200, capacity=600, food_cap=400)
    w_off = GenesisWorld(civ_config(depth_gates=False, **base), seed=3)
    w_off2 = GenesisWorld(civ_config(**base), seed=3)              # flag never mentioned -> same default
    assert not w_off.depth_gates
    assert (w_off.food_tier == 0).all()                           # no tier draw -> all free
    for _ in range(60):
        w_off.step(); w_off2.step()
    a, b = w_off.snapshot(), w_off2.snapshot()
    assert a["population"] == b["population"]
    assert np.array_equal(w_off.pop.pos[w_off.pop.active()], w_off2.pop.pos[w_off2.pop.active()])


def test_diet_capability_ceiling_readout_matches_hand_set_depth():
    """The read-out converts realized cultural depth -> embodied ceiling correctly (recipe_level_step=2,
    n_food_tiers=5 -> tiers 0..4 at depth 0/2/4/6/8; cap_level_step=2, 2 axes at depth 2/4)."""
    w = GenesisWorld(_depth_gate_cfg(4000), seed=1)
    act = w.pop.active()
    w.pop.tech[act] = 0.0
    w.pop.tech[act[0]] = 7.0                                       # one deep agent: floor(7/2)=3, axes(>=2,>=4)=2
    tier, axes = w.diet_capability_ceiling()
    assert tier == 3 and axes == 2
    w.pop.tech[act] = 0.0                                          # everyone shallow -> only the free tier, no axes
    assert w.diet_capability_ceiling() == (0, 0)


def test_depth_gates_embodied_ceiling_open_ended_vs_capped():
    """HEADLINE: with the grown tree UNCAPPED the embodied ceiling climbs to the top diet tier and both
    capability axes; CAP the tree small and the SAME machinery freezes the ceiling at the free tier / no axes
    -> open-ended culture is now CAUSAL on the body, bounded only by the cultural cap."""
    big = GenesisWorld(_depth_gate_cfg(4000), seed=1)
    small = GenesisWorld(_depth_gate_cfg(20), seed=1)
    for _ in range(180):
        big.step(); small.step()
    bt, ba = big.diet_capability_ceiling()
    st, sa = small.diet_capability_ceiling()
    assert bt == big.cfg.n_food_tiers - 1 and ba == big.cfg.n_capabilities   # full diet + all axes
    assert st == 0 and sa == 0                                                # frozen at the free tier, no axes
    assert big._tier_eat_count[1:].sum() > 0                                  # the uncapped pop EATS locked tiers
    assert small._tier_eat_count[1:].sum() == 0                               # the capped pop physically cannot


def test_depth_gates_ceiling_monotone_in_cap():
    """The freeze is the CAP, not chance: the embodied diet ceiling is non-decreasing in the capacity cap."""
    tiers = []
    for K in (20, 80, 4000):
        w = GenesisWorld(_depth_gate_cfg(K), seed=2)
        for _ in range(150):
            w.step()
        tiers.append(w.diet_capability_ceiling()[0])
    assert tiers[0] <= tiers[1] <= tiers[2]
    assert tiers[2] > tiers[0]                                     # uncapped strictly out-reaches the small cap


def test_depth_gates_null_no_composition_no_unlock():
    """Load-bearing null: innov_steps=0 -> the tree never grows -> depth stays 0 -> NOT A SINGLE locked tier
    or axis ever unlocks, even at a huge cap. So the embodied climb is driven by the population's real
    compositions, not by the cap or the gate being trivially open."""
    w = GenesisWorld(_depth_gate_cfg(4000, innov_steps=0), seed=1)
    for _ in range(120):
        w.step()
    assert w._tree.n == w.cfg.n_seed_tech                          # never composed -> only the seeds materialized
    assert w.diet_capability_ceiling() == (0, 0)
    assert w._tier_eat_count[1:].sum() == 0


# ---------- R172: the OPEN-ENDED tree survives process death — the climb persists across restarts ----------
def test_growing_tree_state_restore_roundtrip():
    """R172 unit: GrowingTree.state()/restore() round-trips the grown tree losslessly. After restoring a fresh
    tree from a saved state, the materialized arrays + node count match, the (a,b)->id registry is rebuilt so an
    ALREADY-COMPOSED pair returns its original id, and a genuinely NEW composition extends from `n` without
    colliding. This is the per-node guarantee the checkpoint relies on."""
    from alife.genesis import combinatorial as cb
    rng = np.random.default_rng(0)
    src = cb.GrowingTree(capacity=200, n_seed=6)
    rep = np.zeros((40, 200), dtype=bool)
    rep[:, :6] = True
    src.discover_inplace(rep, rng, steps=8)                 # grow a real tree
    assert src.n > 6                                        # something was composed
    st = src.state()

    dst = cb.GrowingTree(capacity=200, n_seed=6)
    dst.restore(st["pa"], st["pb"], st["level"], int(st["n"]))
    assert dst.n == src.n
    assert np.array_equal(dst.pa, src.pa) and np.array_equal(dst.pb, src.pb)
    assert np.array_equal(dst.level, src.level)
    assert dst.registry == src.registry                    # registry rebuilt from parents, not stored
    # an already-known pair returns its original id on BOTH trees (registry consistent)...
    a, b = int(src.pa[6]), int(src.pb[6])
    assert dst.combine(a, b) == src.registry[(min(a, b), max(a, b))]
    # ...and a brand-new composition extends from n identically on both. Search over ALL known nodes for a
    # still-uncomposed pair (the 15 seed pairs may already be exhausted after a real discovery run).
    fresh_pair = next((i, j) for i in range(src.n) for j in range(i + 1, src.n)
                      if (i, j) not in src.registry)
    n_before = dst.n
    nid = dst.combine(*fresh_pair)
    assert nid == n_before and dst.n == n_before + 1


def test_persist_resume_generative_tree_is_bit_for_bit_continuous(tmp_path):
    """R172 HEADLINE: persistence now works on the OPEN-ENDED generative substrate. A chain of resumed segments
    (each a fresh world that loads the previous checkpoint = simulated process death) on the generative_tree +
    depth_gates world yields a development trajectory BIT-FOR-BIT IDENTICAL to one uninterrupted run — INCLUDING
    the grown tree's connected depth AND the embodied ceiling (edible diet tiers). Before R172 the grown tree was
    not checkpointed, so resumed deep nodes collapsed to a fresh seed-only tree and the trajectory diverged."""
    from alife.genesis import persist
    cfg = _depth_gate_cfg(1000, innov_steps=3)
    cont = persist.continuous_trajectory(cfg, seed=1, total_steps=120, log_every=20)
    chain = persist.chained_trajectory(cfg, seed=1, n_segments=3, segment_steps=40,
                                       ckpt_path=str(tmp_path / "ck.npz"), log_every=20)
    # the open-ended depth AND the embodied diet ceiling genuinely CLIMBED in the window (not a flat trajectory).
    assert cont["conn_depth"][-1] > cont["conn_depth"][0]
    assert cont["edible_tiers"][-1] > cont["edible_tiers"][0]
    for k in persist._KEYS:
        assert np.array_equal(cont[k], chain[k], equal_nan=True), f"generative resume diverged on {k}"
    assert persist.continuity_max_abs_diff(cont, chain) == 0.0


def test_persist_generative_tree_restore_is_load_bearing(tmp_path):
    """R172 RED-TEAM (permanent not-vacuous control): the bit-for-bit continuity on the generative substrate is
    CAUSED by restoring the grown tree, not by the tree being trivially reconstructable. A boundary chain that
    reloads the checkpoint but then RESETS the tree to a fresh seed-only GrowingTree (the pre-R172 behavior) MUST
    diverge — the deep nodes in `rep` no longer map to their real levels, so depth/diet collapse."""
    from alife.genesis import persist
    from alife.genesis.genesis import GenesisWorld
    from alife.genesis import combinatorial as cb
    cfg = _depth_gate_cfg(1000, innov_steps=3)
    total, seg, le = 120, 40, 20
    cont = persist.continuous_trajectory(cfg, seed=1, total_steps=total, log_every=le)

    samples, w = [], GenesisWorld(cfg, seed=1, evolve=True)
    ckpt = str(tmp_path / "ck.npz")
    while w.step_count < total:
        if w.step_count % le == 0:
            samples.append(persist._observe(w))
        if w.step_count > 0 and w.step_count % seg == 0:
            w.save_checkpoint(ckpt)
            del w
            w = GenesisWorld(cfg, seed=1, evolve=True)
            w.load_checkpoint(ckpt)
            # sabotage: throw away the restored grown tree (emulate the pre-R172 fresh-tree-on-resume bug).
            w._tree = cb.GrowingTree(cfg.max_techniques, cfg.n_seed_tech)
            w._tree_pa, w._tree_pb, w._tree_level = w._tree.pa, w._tree.pb, w._tree.level
        w.step()
    sabotaged = persist._stack(samples)
    assert persist.continuity_max_abs_diff(cont, sabotaged) > 0.0


# ---------- R173: UNATTENDED MULTI-DAY CLIMB — tick driver + rolling live dashboard ----------
def _r173_cfg(K=1000):
    """The open-ended generative + depth-gated world (== R172 gen_cfg) the unattended daemon ticks."""
    from alife.genesis.civdev import civ_config
    return civ_config(
        tech_actions=False, tech_capabilities=False, generative_tree=True, depth_gates=True,
        max_techniques=K, innov_steps=3, n_food_tiers=5, recipe_level_step=2,
        n_capabilities=2, cap_level_step=2, tier0_frac=0.4,
        n0=300, capacity=1000, food_cap=600, food_regrow=40)


def test_daemon_tick_extends_world_and_writes_live_panel(tmp_path):
    """R173: one tick = run one more segment + regenerate the rolling live dashboard. Across ticks the
    world extends on disk (bootstrap then resume, global step advances, tick_index increments) and the
    live panel is a real PNG REGENERATED each tick over a GROWING accumulated trajectory."""
    from alife.genesis import daemon, persist
    cfg = _r173_cfg()
    sd = str(tmp_path / "world")
    r1 = daemon.tick(sd, cfg, seed=2, segment_steps=40, log_every=20)
    assert r1["bootstrap"] and r1["tick_index"] == 1 and r1["start_step"] == 0 and r1["end_step"] == 40
    panel = os.path.join(sd, "live_panel.png")
    assert r1["panel_path"] == panel and os.path.getsize(panel) > 1000      # a real rendered PNG
    n1 = r1["panel_n_samples"]
    r2 = daemon.tick(sd, cfg, seed=2, segment_steps=40, log_every=20)
    assert (not r2["bootstrap"]) and r2["tick_index"] == 2
    assert r2["start_step"] == 40 and r2["end_step"] == 80
    assert r2["panel_n_samples"] > n1                  # panel now drawn over MORE history (regenerated)
    traj = persist.load_trajectory(sd)
    assert traj["step"][0] == 0.0 and traj["step"][-1] == 80.0 and np.all(np.diff(traj["step"]) > 0)


def test_daemon_irregular_tick_cadence_one_continuous_history(tmp_path):
    """R173: a real scheduler does NOT fire on an exact cadence. Ticks with DIFFERENT segment_steps still
    accumulate into ONE strictly-increasing on-disk history whose final step is the EXACT sum — the world
    doesn't care how it was sliced, only that it keeps being ticked."""
    from alife.genesis import daemon, persist
    cfg = _r173_cfg()
    sd = str(tmp_path / "world")
    seps = [40, 60, 20, 50]
    for s in seps:
        daemon.tick(sd, cfg, seed=5, segment_steps=s, log_every=20)
    traj = persist.load_trajectory(sd)
    assert traj["step"][-1] == float(sum(seps))        # 170 — accumulated across irregular ticks
    assert np.all(np.diff(traj["step"]) > 0)           # one continuous monotone climb, no resets/dups


def test_daemon_live_panel_renders_from_full_trajectory(tmp_path):
    """R173: render_live_panel is a PURE function of the accumulated trajectory dict (the rolling dashboard
    a cron tick refreshes) — given a longer trajectory it draws more samples and writes a valid PNG."""
    from alife.genesis import daemon, persist
    cfg = _r173_cfg()
    sd = str(tmp_path / "world")
    daemon.tick(sd, cfg, seed=7, segment_steps=60, log_every=20)
    traj = persist.load_trajectory(sd)
    p = str(tmp_path / "panel.png")
    n = daemon.render_live_panel(traj, p, title="t")
    assert n == traj["step"].size >= 3 and os.path.getsize(p) > 1000


# ---------- R174: the SUSTAINED multi-tick climb — open-ended keeps developing, capped freezes ----------
def _r174_cfg(K, n_food_tiers=8, n_caps=4):
    """The SUSTAINED-climb regime: a LARGE tree cap + gentler innovation (so the open-ended tree has
    headroom to keep climbing tick after tick instead of saturating in tick 1) and DEEPER diet/capability
    gates (so the embodied ceiling keeps rising with the depth, not maxing out at once). The ONLY knob the
    capped control changes is `max_techniques` (K) — everything else is identical."""
    from alife.genesis.civdev import civ_config
    return civ_config(
        tech_actions=False, tech_capabilities=False, generative_tree=True, depth_gates=True,
        max_techniques=K, innov_steps=2, n_food_tiers=n_food_tiers, recipe_level_step=2,
        n_capabilities=n_caps, cap_level_step=3, tier0_frac=0.4,
        n0=300, capacity=1000, food_cap=600, food_regrow=40)


def test_sustained_climb_open_ended_keeps_rising_while_capped_freezes(tmp_path):
    """R174 HEADLINE (falsifiable): driven as REAL resumed ticks, the OPEN-ENDED world (large cap) keeps
    climbing across the WHOLE horizon — breadth strictly rises even in the LATE ticks, and the depth AND
    the EMBODIED diet ceiling end strictly higher than they began (the body keeps developing). The CAPPED
    world (small cap, otherwise identical) FREEZES: its tree fills, so its late ticks add nothing. The only
    difference is the cap, so a sustained-vs-frozen split is the open-ended signature, not just 'ran longer'."""
    from alife.genesis import daemon
    n_ticks, seg = 8, 60
    op = daemon.climb_curve(str(tmp_path / "open"), _r174_cfg(K=20000), seed=0, segment_steps=seg, n_ticks=n_ticks)
    cap = daemon.climb_curve(str(tmp_path / "capped"), _r174_cfg(K=250), seed=0, segment_steps=seg, n_ticks=n_ticks)

    # continuity: both are one monotone on-disk history (real resumed ticks, no resets/dups)
    assert np.all(np.diff(op["step"]) > 0) and op["step"][-1] == n_ticks * seg

    # OPEN-ENDED: breadth STILL rising in the LATE ticks (not saturated), depth + body climbed end-to-end
    half = n_ticks // 2
    assert op["breadth"][-1] > op["breadth"][half]                 # late-tick breadth still climbing
    assert op["breadth"][-1] - op["breadth"][-2] >= 50             # and the VERY last tick still adds a lot
    assert op["breadth"][-1] < 20000                               # genuinely below the cap (headroom remains)
    assert op["conn_depth"][-1] > op["conn_depth"][0]              # connected DEPTH climbed across the horizon
    assert op["edible_tiers"][-1] > op["edible_tiers"][0]          # the BODY's diet ceiling climbed (embodied)
    assert op["realized_axes"][-1] > op["realized_axes"][0]        # the BODY's capability axes climbed
    assert op["population"][-1] >= 500                             # and it stayed a healthy living population

    # CAPPED: tree fills, so the LATE ticks add ~no new breadth — the climb is FROZEN (only the cap differs)
    assert cap["breadth"][-1] - cap["breadth"][-2] <= 3            # capped breadth flat at the cap (frozen)
    assert cap["population"][-1] >= 200                            # a genuinely FROZEN world, not a dead one
    assert op["breadth"][-1] > 10 * cap["breadth"][-1]            # open-ended ends an order past the capped ceiling
    assert op["conn_depth"][-1] > cap["conn_depth"][-1]           # and climbs strictly deeper than the capped world


def test_render_climb_panel_writes_open_vs_capped_png(tmp_path):
    """R174: render_climb_panel is a PURE function of the two climb-curve dicts — it draws the open-ended
    and capped curves side by side and writes a valid PNG (the eye-checkable sustained-climb deliverable)."""
    from alife.genesis import daemon
    op = {k: np.arange(1.0, 6.0) for k in daemon._CLIMB_KEYS}
    cap = {k: np.ones(5) for k in daemon._CLIMB_KEYS}
    p = str(tmp_path / "climb.png")
    n = daemon.render_climb_panel(op, cap, p, title="t")
    assert n == 5 and os.path.getsize(p) > 1000


# ---------------------------------------------------------------------------------------------------------
# R175 — DEPTH-REWARDING SELECTION PRESSURE: keep connected DEPTH climbing across many ticks, not just breadth.
# R174's honest caveat was that under the UNIFORM composition draw breadth climbs the whole horizon while
# connected DEPTH plateaus by ~tick 6 (the current-deepest node is re-picked only ~2/|known| of the time, a
# probability that vanishes as breadth grows). depth_bias>0 makes the per-composition draw a softmax over tree
# LEVEL, so the deepest frontier is preferentially re-composed and DEPTH keeps extending tick after tick.
# ---------------------------------------------------------------------------------------------------------

def test_depth_bias_zero_is_byte_identical_to_uniform_draw():
    """depth_bias=0.0 (level_bias<=0) is the EXACT uniform rng.choice path — no extra RNG, default-off safe.
    Same seed + same level_bias=0 must materialize a bit-identical tree to the no-arg call (R170-R174 path)."""
    from alife.genesis import combinatorial as cb

    def grow(level_bias_arg):
        tree = cb.GrowingTree(capacity=400, n_seed=6)
        rep = np.zeros((40, 400), dtype=bool)
        rep[:, :6] = True
        rng = np.random.default_rng(7)
        if level_bias_arg is None:
            tree.discover_inplace(rep, rng, steps=12)            # the pre-R175 call signature (no bias arg)
        else:
            tree.discover_inplace(rep, rng, steps=12, level_bias=level_bias_arg)
        return tree.n, tree.pa.copy(), tree.pb.copy(), tree.level.copy(), rep.copy()

    n0, pa0, pb0, lv0, rep0 = grow(None)
    n1, pa1, pb1, lv1, rep1 = grow(0.0)
    assert n0 == n1
    assert np.array_equal(pa0, pa1) and np.array_equal(pb0, pb1) and np.array_equal(lv0, lv1)
    assert np.array_equal(rep0, rep1)


def test_depth_bias_grows_a_strictly_deeper_tree_than_uniform():
    """On the SAME fresh tree + SAME seed, a positive depth_bias re-composes the frontier preferentially, so the
    deepest realized level is strictly greater than the uniform draw's — the mechanism, isolated from the world."""
    from alife.genesis import combinatorial as cb

    def deepest(level_bias_arg):
        tree = cb.GrowingTree(capacity=2000, n_seed=6)
        rep = np.zeros((30, 2000), dtype=bool)
        rep[:, :6] = True
        rng = np.random.default_rng(3)
        tree.discover_inplace(rep, rng, steps=40, level_bias=level_bias_arg)
        return int(tree.level[:tree.n].max())

    d_uniform = deepest(0.0)
    d_biased = deepest(1.0)
    assert d_biased > d_uniform                     # depth-biased reuse drives a strictly deeper frontier
    assert d_biased >= 2 * d_uniform                # and substantially so (decisive, not marginal)


def _r175_cfg(depth_bias, K=20000):
    """The R175 regime == the R174 SUSTAINED-climb regime (large cap, gentle innovation, deep gates) with the
    ONE added knob `depth_bias`. The biased-vs-unbiased control changes depth_bias ALONE — everything else,
    including the cap K, is identical — so a sustained-depth-vs-plateau split is the depth-pressure signature."""
    from alife.genesis.civdev import civ_config
    return civ_config(
        tech_actions=False, tech_capabilities=False, generative_tree=True, depth_gates=True,
        max_techniques=K, innov_steps=2, n_food_tiers=8, recipe_level_step=2,
        n_capabilities=4, cap_level_step=3, tier0_frac=0.4,
        n0=300, capacity=1000, food_cap=600, food_regrow=40, depth_bias=depth_bias)


def test_depth_bias_sustains_depth_climb_while_unbiased_plateaus(tmp_path):
    """R175 HEADLINE (falsifiable): driven as REAL resumed ticks at a LARGE cap (so breadth is never the limiter),
    the depth-BIASED world keeps connected DEPTH climbing across the WHOLE horizon — still deepening on the very
    last tick — while the UNBIASED world (identical regime, same cap, only depth_bias=0) PLATEAUS its depth by
    mid-horizon. The only difference is the depth-reward, so sustained-depth-vs-plateau is its signature, not a
    cap or run-length artifact (both run the same K and the same number of ticks)."""
    from alife.genesis import daemon
    n_ticks, seg = 10, 60
    half = n_ticks // 2
    bias = daemon.climb_curve(str(tmp_path / "bias"), _r175_cfg(1.0), seed=0, segment_steps=seg, n_ticks=n_ticks)
    unb = daemon.climb_curve(str(tmp_path / "unb"), _r175_cfg(0.0), seed=0, segment_steps=seg, n_ticks=n_ticks)

    # both are one monotone on-disk history of the SAME length (genuine resumed ticks, no resets/dups)
    assert np.all(np.diff(bias["step"]) > 0) and bias["step"][-1] == n_ticks * seg
    assert np.all(np.diff(unb["step"]) > 0) and unb["step"][-1] == n_ticks * seg

    # BIASED: connected DEPTH keeps climbing late (not plateaued) and is STILL deepening on the final tick
    assert bias["conn_depth"][-1] > bias["conn_depth"][half] + 5    # decisive late-horizon depth climb
    assert bias["conn_depth"][-1] - bias["conn_depth"][-2] >= 1     # still deepening on the VERY last tick

    # UNBIASED (R174 regime, only depth_bias differs): DEPTH plateaus — late ticks add ~nothing
    assert unb["conn_depth"][-1] - unb["conn_depth"][half] <= 2     # depth flat across the late half
    assert unb["conn_depth"][-1] - unb["conn_depth"][-2] <= 1       # and flat on the final tick

    # the split: biased ends MULTIPLES deeper, body's diet ceiling no lower, both a healthy living population
    assert bias["conn_depth"][-1] > 3 * unb["conn_depth"][-1]
    assert bias["edible_tiers"][-1] >= unb["edible_tiers"][-1]
    assert bias["population"][-1] >= 500 and unb["population"][-1] >= 500


# ---- R176: OPEN-ENDED EMBODIMENT — a CONTINUOUS depth-scaled phenotype (the body keeps deepening too) ----
# R171's depth_gates made the body causal on culture but CATEGORICALLY (diet floor(depth/step) clipped, axes
# count(depth>=step*(i+1)) clipped), so the EMBODIED ceiling SATURATES the instant depth crosses the last fixed
# threshold (R175 caveat: diet 7 / axes 4 frozen by ~tick 1 while connected DEPTH climbs 32->76). depth_phenotype
# makes speed+reach scale CONTINUOUSLY and UNBOUNDEDLY with realized cultural depth, so the body keeps deepening.
def _r176_cfg(depth_phenotype, gain, K=20000):
    """The R175 SUSTAINED-DEPTH regime (depth_bias on, large cap) + the R176 continuous body. The phenotype-vs-
    categorical control changes depth_phenotype/gain ALONE — same depth-climbing world underneath."""
    from alife.genesis.civdev import civ_config
    return civ_config(
        tech_actions=False, tech_capabilities=False, generative_tree=True, depth_gates=True,
        depth_phenotype=depth_phenotype, pheno_speed_gain=gain, pheno_reach_gain=gain,
        max_techniques=K, innov_steps=2, n_food_tiers=8, recipe_level_step=2,
        n_capabilities=4, cap_level_step=3, tier0_frac=0.4, depth_bias=1.0,
        n0=300, capacity=1000, food_cap=600, food_regrow=40)


def test_depth_phenotype_requires_depth_gates():
    """depth_phenotype gates on realized cultural DEPTH, which only the generative depth_gates path provides."""
    from alife.genesis.civdev import civ_config
    with pytest.raises(ValueError):
        GenesisWorld(civ_config(depth_phenotype=True, pheno_speed_gain=0.02), seed=0)  # depth_gates off


def test_depth_phenotype_off_is_byte_identical():
    """depth_phenotype=False adds NO code path and consumes NO extra RNG — even with gains set, an OFF world is
    bit-identical to the depth_gates (R171) world, and an ON world genuinely DIFFERS (the continuous speed acts)."""
    off_default = GenesisWorld(_r176_cfg(False, 0.0), seed=1)
    off_gains = GenesisWorld(_r176_cfg(False, 0.05), seed=1)        # gains set but OFF -> must be ignored
    on = GenesisWorld(_r176_cfg(True, 0.05), seed=1)
    for _ in range(30):
        off_default.step(); off_gains.step(); on.step()
    assert np.array_equal(off_default.pop.pos, off_gains.pop.pos)   # gains have no effect while off
    assert np.array_equal(off_default.pop.vel, off_gains.pop.vel)
    assert not np.array_equal(off_default.pop.pos, on.pop.pos)      # the continuous phenotype actually moves bodies


def test_embodied_scale_is_the_continuous_depth_mapping():
    """embodied_scale() is exactly the living-pop mean of (1+gain*depth): a pure continuous function of the depth
    distribution (no threshold, no clip), so it has no ceiling — unlike diet_capability_ceiling's clipped ints."""
    w = GenesisWorld(_r176_cfg(True, 0.02), seed=2)
    for _ in range(60):
        w.step()
    act = w.pop.active()
    depth = w.pop.tech[act].astype(float)
    es = w.embodied_scale()
    assert es["mean_speed_mult"] == pytest.approx(float((1.0 + 0.02 * depth).mean()))
    assert es["max_speed_mult"] == pytest.approx(float((1.0 + 0.02 * depth).max()))
    # the contrast: the categorical ceiling is a clipped integer (saturable); embodied_scale is unbounded-by-form
    max_tier, n_axes = w.diet_capability_ceiling()
    assert n_axes <= w.cfg.n_capabilities and max_tier <= w.cfg.n_food_tiers - 1   # categorical caps bind
    assert es["max_speed_mult"] > 1.0                                              # continuous body has no such cap


def test_depth_phenotype_body_keeps_deepening_while_categorical_saturates(tmp_path):
    """R176 HEADLINE (falsifiable): driven as REAL resumed ticks, the CONTINUOUS embodied phenotype (embodied_scale
    = mean realized speed multiplier) keeps RISING across the whole horizon — still rising on the last tick — while
    the CATEGORICAL body (realized_axes) SATURATES at its ceiling by ~tick 1 in the SAME run. The decisive control
    is the GAIN: with gain=0 the body is FROZEN at 1.0 though connected DEPTH still climbs identically — proving it
    is the continuous MAPPING that converts depth-gain into body-gain, not a relabel of depth or a run-length effect."""
    from alife.genesis import daemon
    n_ticks, seg = 6, 50
    half = n_ticks // 2
    pheno = daemon.climb_curve(str(tmp_path / "pheno"), _r176_cfg(True, 0.02), seed=0, segment_steps=seg, n_ticks=n_ticks)
    ctrl = daemon.climb_curve(str(tmp_path / "ctrl"), _r176_cfg(True, 0.0), seed=0, segment_steps=seg, n_ticks=n_ticks)

    # CONTINUOUS body keeps deepening: embodied_scale climbs the late horizon and is STILL rising on the last tick
    assert pheno["embodied_scale"][-1] > pheno["embodied_scale"][half] + 0.05
    assert pheno["embodied_scale"][-1] - pheno["embodied_scale"][-2] > 0.0

    # CATEGORICAL body SATURATES early in the SAME run: axes ceiling at n_capabilities, flat across the late half
    assert pheno["realized_axes"][-1] == pheno["realized_axes"][half]               # axes frozen late (no deepening)
    assert pheno["realized_axes"][-1] <= 4

    # CONTROL (gain=0, same regime): connected DEPTH still climbs strongly, but the body is FROZEN at 1.0 ->
    # the body-deepening is the continuous MAPPING converting depth-gain into body-gain, not a relabel of depth.
    assert ctrl["conn_depth"][-1] > ctrl["conn_depth"][0] + 10                      # depth climbs WITHOUT the body
    assert pheno["conn_depth"][-1] > pheno["conn_depth"][0] + 10                    # depth climbs WITH it too
    assert np.allclose(ctrl["embodied_scale"], 1.0)                                 # zero-gain body never deepens
    assert pheno["population"][-1] >= 500 and ctrl["population"][-1] >= 500         # both healthy living worlds


# ---- R177: CUMULATIVE-CULTURE BODY — drive embodiment off ACCESSIBLE BANKED culture, not personal mastery ----
# R176's body is continuous but its DRIVER (personal pop.tech) saturates at the transmission-loss equilibrium, so
# the body's climb decelerates to an asymptote. pheno_cumulative drives the body off max(personal, nearest banked
# hearth record): the banked record (struct_tech) is a running MAX over every builder (lossless external memory),
# so it RATCHETS and never saturates — the body keeps deepening with the SOCIETY's cumulative culture.
def _r177_cfg(pheno_cumulative, gain, K=20000):
    """R176's SUSTAINED-DEPTH regime + the R177 cumulative-culture body. The cumulative-vs-personal control
    changes pheno_cumulative ALONE (both depth_phenotype=True, same gain) — same depth-climbing world underneath."""
    return replace(_r176_cfg(True, gain, K), pheno_cumulative=pheno_cumulative)


def test_pheno_cumulative_requires_depth_phenotype_and_building():
    """pheno_cumulative reads the banked hearth record, so it needs both the continuous body (depth_phenotype)
    and the built world that accumulates culture (building)."""
    from alife.genesis.civdev import civ_config
    with pytest.raises(ValueError):                                       # depth_phenotype off
        GenesisWorld(replace(_r176_cfg(False, 0.0), pheno_cumulative=True), seed=0)
    with pytest.raises(ValueError):                                       # building off
        GenesisWorld(replace(_r177_cfg(True, 0.02), building=False), seed=0)


def test_pheno_cumulative_off_is_byte_identical():
    """pheno_cumulative=False adds NO code path and consumes NO extra RNG -> bit-identical to the R176 world;
    ON genuinely DIFFERS (the banked-culture driver moves bodies differently than personal mastery)."""
    off = GenesisWorld(_r177_cfg(False, 0.05), seed=1)
    on = GenesisWorld(_r177_cfg(True, 0.05), seed=1)
    r176 = GenesisWorld(_r176_cfg(True, 0.05), seed=1)                    # the R176 reference (cumulative absent)
    for _ in range(40):
        off.step(); on.step(); r176.step()
    assert np.array_equal(off.pop.pos, r176.pop.pos)                      # OFF == plain R176, bit-for-bit
    assert np.array_equal(off.pop.vel, r176.pop.vel)
    assert not np.array_equal(off.pop.pos, on.pop.pos)                    # the banked-culture body actually differs


def test_pheno_driver_returns_personal_when_no_hearth_else_banked_max():
    """_pheno_driver is exactly max(personal, accessible banked record): with no strong hearth it is the personal
    depth verbatim; once a hearth banks a deeper record an in-range agent's driver picks it up (>= personal)."""
    w = GenesisWorld(_r177_cfg(True, 0.02), seed=3)
    act = w.pop.active()
    assert np.array_equal(w._pheno_driver(act), w.pop.tech[act])          # no hearths yet -> personal verbatim
    # plant a strong hearth at agent 0 with a record far deeper than any living agent's personal mastery
    a0 = int(act[0])
    deep = float(w.pop.tech[act].max()) + 50.0
    w.struct_alive[0] = True
    w.struct_strength[0] = w.cfg.hearth_min_strength + 1.0
    w.struct_pos[0] = w.pop.pos[a0]
    w.struct_tech[0] = deep
    drv = np.asarray(w._pheno_driver(act))
    assert drv[0] == pytest.approx(deep)                                  # in-range agent inherits the banked depth
    assert np.all(drv >= w.pop.tech[act] - 1e-9)                          # driver is never below personal mastery
    es = w.embodied_scale()
    assert es["mean_depth"] >= es["mean_personal_depth"] - 1e-9           # banked driver >= personal baseline


def test_pheno_cumulative_body_outclimbs_personal_mastery(tmp_path):
    """R177 HEADLINE (falsifiable): in the SAME depth-climbing regime, the CUMULATIVE-CULTURE body (driver = the
    banked hearth record, a ratchet) ends DEEPER than the R176 PERSONAL-mastery body (driver = the saturating
    living-pop mean) — the only knob that differs is pheno_cumulative. And within the cumulative run the body's
    driver depth rises ABOVE the personal-mastery baseline it would otherwise be stuck at."""
    from alife.genesis import daemon
    n_ticks, seg = 6, 50
    cum = daemon.climb_curve(str(tmp_path / "cum"), _r177_cfg(True, 0.02), seed=0, segment_steps=seg, n_ticks=n_ticks)
    per = daemon.climb_curve(str(tmp_path / "per"), _r177_cfg(False, 0.02), seed=0, segment_steps=seg, n_ticks=n_ticks)

    # within the cumulative run the body's actual driver outruns personal mastery (the banked ratchet pays off)
    assert cum["body_driver_depth"][-1] > cum["personal_depth"][-1] + 1.0
    # the cumulative body ends deeper than the personal-mastery (R176) body in the same regime
    assert cum["embodied_scale"][-1] > per["embodied_scale"][-1]
    # both are genuine living worlds with depth still climbing (not a collapse artifact)
    assert cum["conn_depth"][-1] > cum["conn_depth"][0] + 10
    assert cum["population"][-1] >= 400 and per["population"][-1] >= 400
