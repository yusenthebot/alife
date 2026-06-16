"""World topology: a 2D arena, optionally toroidal (wrap-around).

The world owns space semantics — distance, displacement, wrapping — so that
the rest of the sim never hard-codes boundary behavior. A toroidal world has
no edges, which keeps flocking artifact-free; bounded reflection is available
for later rounds that need walls.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class World:
    width: float = 200.0
    height: float = 200.0
    toroidal: bool = True

    @property
    def size(self) -> np.ndarray:
        return np.array([self.width, self.height], dtype=float)

    def wrap(self, pos: np.ndarray) -> np.ndarray:
        """Map positions back into the arena. Wrap if toroidal, else clamp."""
        if self.toroidal:
            return np.mod(pos, self.size)
        return np.clip(pos, 0.0, self.size - 1e-9)

    def pairwise_delta(self, pos: np.ndarray) -> np.ndarray:
        """Displacement tensor d[i, j] = vector from i to j (pos[j] - pos[i]).

        Under a toroidal topology this uses the minimum-image convention so the
        shortest wrap-around path is taken.
        """
        d = pos[None, :, :] - pos[:, None, :]
        if self.toroidal:
            size = self.size
            d -= size * np.round(d / size)
        return d

    def delta_to(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Cross-set displacement d[i, j] = b[j] - a[i] (e.g. agents → food).

        Returns (len(a), len(b), 2), minimum-image under a toroidal topology.
        """
        d = b[None, :, :] - a[:, None, :]
        if self.toroidal:
            size = self.size
            d -= size * np.round(d / size)
        return d

    def reflect(self, pos: np.ndarray, vel: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Bounce off walls (bounded worlds). Returns (pos, vel) flipped at edges."""
        size = self.size
        over = pos > size
        under = pos < 0.0
        vel = np.where(over | under, -vel, vel)
        pos = np.where(over, 2 * size - pos, pos)
        pos = np.where(under, -pos, pos)
        return np.clip(pos, 0.0, size - 1e-9), vel
