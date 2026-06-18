"""R62 — Autocatalytic sets (RAF): the spontaneous birth of self-sustaining chemistry.

Every digital self-replicator so far (the R51–R53 Avida arc) was *handed* a copy
loop. This round asks the deeper origin-of-life question: how does a set of reactions
that collectively make and catalyse themselves arise from inert food molecules with no
replicator built in? Stuart Kauffman's answer — autocatalytic sets — formalised by
Hordijk & Steel as **RAF** (Reflexively Autocatalytic and Food-generated) sets:

  * RA — every reaction is catalysed by a molecule the set itself produces (or food),
  * F  — every reactant is buildable from the food set using only the set's reactions.

We use the standard binary-polymer model: molecules are bit strings up to length L;
food = the short strings; reactions are ligations a+b -> ab. Each molecule catalyses
each reaction with some probability; `f` = mean reactions catalysed per molecule is the
order parameter. The maximal RAF is the unique greatest sub-RAF, found by a monotone
forward closure (a reaction switches on once its reactants are available AND it has an
available catalyst; availability only grows, so the fixpoint is the maxRAF).

The headline (Kauffman; Hordijk-Steel 2004): a sharp phase transition — RAFs appear
almost surely once f reaches a small O(1) value, and that threshold barely grows with
system size. Self-sustaining chemistry is close to inevitable.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class RAFConfig:
    max_len: int = 7      # molecules are bit strings of length 1..max_len
    food_len: int = 2     # food set = all strings of length <= food_len


def build_polymer_model(cfg: RAFConfig):
    """Return (mols, idx, reactions, food).

    mols: list of bit-string molecules. idx: string->index. food: set of food indices.
    reactions: list of (a_idx, b_idx, prod_idx) ligations a+b -> ab with |ab| <= max_len.
    """
    mols = []
    for L in range(1, cfg.max_len + 1):
        for k in range(2 ** L):
            mols.append(format(k, f"0{L}b"))
    idx = {m: i for i, m in enumerate(mols)}
    food = {idx[m] for m in mols if len(m) <= cfg.food_len}
    reactions = []
    for prod, p in enumerate(mols):           # every split of every string is one ligation
        for cut in range(1, len(p)):
            a, b = p[:cut], p[cut:]
            reactions.append((idx[a], idx[b], prod))
    return mols, idx, reactions, food


def random_catalysis(n_rxn: int, n_mol: int, f: float, rng) -> list:
    """Per-reaction set of catalyst molecules; each molecule catalyses each reaction
    with prob p = f / n_rxn, so each molecule catalyses ~f reactions on average."""
    p = min(1.0, f / max(n_rxn, 1))
    counts = rng.binomial(n_mol, p, size=n_rxn)
    return [set(rng.integers(0, n_mol, c).tolist()) if c else set() for c in counts]


def production_closure(reactions, food: set, active) -> set:
    """Molecules producible from the food set using `active` reactions (catalysis ignored —
    that is the F axiom). A circular set can still close: r1 makes r2's input and vice versa."""
    avail = set(food)
    grew = True
    while grew:
        grew = False
        for ri in active:
            a, b, prod = reactions[ri]
            if prod not in avail and a in avail and b in avail:
                avail.add(prod)
                grew = True
    return avail


def max_raf(reactions, food: set, catalysts: list):
    """Maximal RAF (Hordijk-Steel): iterate production-closure then catalysis-prune to a
    fixpoint. Decoupling production from catalysis is what finds CIRCULARLY-supported sets
    (the whole point of autocatalysis). Returns (active_rxn_set, available_mols)."""
    active = set(range(len(reactions)))
    while True:
        W = production_closure(reactions, food, active)
        new_active = {ri for ri in active
                      if reactions[ri][0] in W and reactions[ri][1] in W
                      and not catalysts[ri].isdisjoint(W)}
        if new_active == active:
            return active, W
        active = new_active


def has_raf(reactions, food, catalysts) -> bool:
    active, _ = max_raf(reactions, food, catalysts)
    return len(active) > 0


def verify_raf(reactions, food, catalysts, active: set) -> bool:
    """Independently check both RAF axioms hold for `active` against the production closure
    (not via the construction loop)."""
    if not active:
        return True
    W = production_closure(reactions, food, active)
    for ri in active:
        a, b, _ = reactions[ri]
        if a not in W or b not in W:                  # F: reactants food-generated
            return False
        if catalysts[ri].isdisjoint(W):               # RA: catalysed by a producible molecule
            return False
    return True


def phase_transition(cfg: RAFConfig, f_values, trials: int, seed: int = 0):
    """Sweep f; return (f_values, P(RAF exists), mean RAF size). The Kauffman transition."""
    mols, _, reactions, food = build_polymer_model(cfg)
    nm, nr = len(mols), len(reactions)
    rng = np.random.default_rng(seed)
    prob = np.zeros(len(f_values))
    size = np.zeros(len(f_values))
    for i, f in enumerate(f_values):
        hits, total = 0, 0
        for _ in range(trials):
            cat = random_catalysis(nr, nm, f, rng)
            active, _ = max_raf(reactions, food, cat)
            if active:
                hits += 1
                total += len(active)
        prob[i] = hits / trials
        size[i] = total / max(hits, 1)
    return np.asarray(f_values, float), prob, size, (nm, nr)
