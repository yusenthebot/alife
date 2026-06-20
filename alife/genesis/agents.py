"""The agent pool — a fixed-capacity Structure-of-Arrays population with free-slot reuse.

A persistent world must run for days without its memory growing, so the population lives in
pre-allocated arrays of fixed CAPACITY. Death frees a slot (alive=False); birth reuses a free
slot. Nothing is ever appended, so memory is bounded by construction (<100 MB at capacity 1e4).

Per-agent state:
- pos, vel        : 3D kinematics
- energy, age     : metabolism + mortality
- brains          : the genome (a flat weight vector, see alife.brain) — the ONLY thing that evolves
- lineage         : the root-founder id, copied on reproduction -> proves a trait was *evolved*
- generation      : depth in the family tree
- color           : a heritable visual tag (so lineages are legible in the 3D render)
- alive           : slot occupancy

Body parameters (speed, sense range, metabolism) are NOT here — they are fixed and identical for
every agent (set in GenesisConfig), so any measured improvement is attributable to the brain.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PopConfig:
    capacity: int
    n_weights: int


class Population:
    """Fixed-capacity SoA agent pool. Slots 0..capacity-1; `alive` marks occupancy."""

    def __init__(self, cfg: PopConfig):
        c = cfg.capacity
        self.cfg = cfg
        self.pos = np.zeros((c, 3))
        self.vel = np.zeros((c, 3))
        self.energy = np.zeros(c)
        self.age = np.zeros(c, dtype=np.int32)
        self.brains = np.zeros((c, cfg.n_weights))
        self.lineage = np.full(c, -1, dtype=np.int32)
        self.generation = np.zeros(c, dtype=np.int32)
        self.color = np.zeros((c, 3))
        self.diet = np.zeros(c)              # heritable food-type preference (R142 resource niches)
        self.cooldown = np.zeros(c, dtype=np.int32)   # predator digestion timer (R143); 0 for prey
        self.utterance = np.zeros(c)         # last-step emitted signal (R144 emergent signalling); 0 if mute
        self.spec = np.zeros(c)              # heritable caste trait in [0,1] (R147): 0=harvester, 1=processor
        self.alive = np.zeros(c, dtype=bool)

    # --- queries ---
    @property
    def capacity(self) -> int:
        return self.cfg.capacity

    @property
    def n_alive(self) -> int:
        return int(self.alive.sum())

    def active(self) -> np.ndarray:
        """Global indices of living agents."""
        return np.where(self.alive)[0]

    # --- mutation of occupancy ---
    def kill(self, idx: np.ndarray) -> None:
        """Mark the given global slot indices as free."""
        self.alive[idx] = False

    def alloc(self, k: int) -> np.ndarray:
        """Claim up to k free slots, mark them alive, and return their global indices.

        Returns fewer than k (possibly 0) when the pool is near capacity — the caller must
        cope with a short array. age is reset here; all other fields are written by the caller.
        """
        if k <= 0:
            return np.empty(0, dtype=int)
        free = np.where(~self.alive)[0]
        take = free[:k]
        self.alive[take] = True
        self.age[take] = 0
        return take

    # --- persistence ---
    def state(self) -> dict:
        """A pure snapshot of all arrays (for checkpointing)."""
        return {
            "pos": self.pos, "vel": self.vel, "energy": self.energy, "age": self.age,
            "brains": self.brains, "lineage": self.lineage, "generation": self.generation,
            "color": self.color, "diet": self.diet, "cooldown": self.cooldown,
            "utterance": self.utterance, "spec": self.spec, "alive": self.alive,
        }

    def load(self, st: dict) -> None:
        for k, v in st.items():
            getattr(self, k)[...] = v
