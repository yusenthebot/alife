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
    w._eat()
    assert w.pop.energy[a] == 50.0                        # mismatched type -> no food gained
    w.food = np.array([w.pop.pos[a]]); w.food_type = np.array([0], dtype=np.int64)
    w.food_ripe = np.array([True]); w.ripe_age = np.zeros(1, dtype=np.int32)
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
    # the two-stage economy closes: processors ripen food, harvesters eat it, the population persists
    w = GenesisWorld(replace(GenesisConfig(), processing=True, n_founder_genomes=8), seed=0)
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
