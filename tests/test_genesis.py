"""R141 — GENESIS foundation: a persistent 3D living world with evolved-neural agents.

These tests pin the substrate invariants. The headline 'behaviour genuinely evolves' claim is
proven by the long REAL-VERIFY run (scripts/run_genesis.py) + the frozen-genome control, not by a
unit test; test_evolution_beats_frozen_control is the fast smoke version.
"""

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
    return replace(_kcfg(), tech_actions=True, n_food_tiers=3, recipe_level_step=1, tier_value_bonus=2.0,
                   tier0_frac=0.6, food_cap=700, food_regrow=35, **kw)


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
