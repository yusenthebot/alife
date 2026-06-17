"""A bounded 3D arena. Unlike the 2D toroidal world, creatures fly inside a box
and are steered back from the walls — so a 3D flock stays whole and on-camera
instead of teleporting across wrap seams (which read badly in perspective).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class World3D:
    size: float = 120.0

    @property
    def extent(self) -> np.ndarray:
        return np.array([self.size, self.size, self.size], dtype=float)

    @property
    def center(self) -> np.ndarray:
        return self.extent / 2.0

    def pairwise_delta(self, pos: np.ndarray) -> np.ndarray:
        """d[i, j] = pos[j] - pos[i], shape (N, N, 3). Non-toroidal."""
        return pos[None, :, :] - pos[:, None, :]

    def clamp(self, pos: np.ndarray) -> np.ndarray:
        return np.clip(pos, 0.0, self.size)

    def boundary_push(self, pos: np.ndarray, margin: float, strength: float) -> np.ndarray:
        """Steering that turns creatures back toward the interior near each wall."""
        low = np.maximum(margin - pos, 0.0)            # how far inside the near margin
        high = np.maximum(pos - (self.size - margin), 0.0)
        return (low - high) / margin * strength
