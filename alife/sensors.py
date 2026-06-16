"""Egocentric senses: what a creature's brain actually sees.

The world is projected into the creature's own frame: a ring of angular sectors
around its heading, each reporting how close the nearest food (and nearest
neighbor) is in that direction, plus its own energy. Everything is relative to
heading, so an evolved brain learns directions like "food ahead-left" rather
than absolute coordinates — the same network works no matter which way the
creature faces.
"""

from __future__ import annotations

import numpy as np

from .world import World

K_SECTORS = 6  # angular resolution of the retina


def n_inputs(k: int = K_SECTORS) -> int:
    return 2 * k + 1  # food sectors + neighbor sectors + own energy


def _sector_proximity(rel: np.ndarray, dist: np.ndarray, heading: np.ndarray,
                      sense_range: float, k: int) -> np.ndarray:
    """For each agent and sector, the proximity (0..1) of the nearest target.

    rel:(N,M,2) relative offsets, dist:(N,M) their lengths, heading:(N,) angle.
    """
    n = rel.shape[0]
    ang = np.arctan2(rel[..., 1], rel[..., 0]) - heading[:, None]
    ang = (ang + np.pi) % (2 * np.pi) - np.pi
    sector = np.clip(((ang + np.pi) / (2 * np.pi) * k).astype(int), 0, k - 1)
    within = dist < sense_range
    prox = np.where(within, 1.0 - dist / sense_range, 0.0)
    out = np.zeros((n, k))
    for s in range(k):
        masked = np.where((sector == s) & within, prox, 0.0)
        out[:, s] = masked.max(axis=1) if masked.shape[1] else 0.0
    return out


def sense(world: World, pos: np.ndarray, vel: np.ndarray, energy: np.ndarray,
          food: np.ndarray, sense_range: float, e_norm: float, k: int = K_SECTORS) -> np.ndarray:
    """Assemble the full sensory vector (N, 2k+1) for the whole population."""
    n = pos.shape[0]
    heading = np.arctan2(vel[:, 1], vel[:, 0])

    if food.shape[0]:
        fr = world.delta_to(pos, food)
        fd = np.sqrt(np.einsum("nfk,nfk->nf", fr, fr))
        food_ch = _sector_proximity(fr, fd, heading, sense_range, k)
    else:
        food_ch = np.zeros((n, k))

    nr = world.pairwise_delta(pos)
    nd = np.sqrt(np.einsum("ijk,ijk->ij", nr, nr))
    nd[np.arange(n), np.arange(n)] = np.inf  # ignore self
    nb_ch = _sector_proximity(nr, nd, heading, sense_range, k)

    e = np.clip(energy / e_norm, 0.0, 1.0)[:, None]
    return np.concatenate([food_ch, nb_ch, e], axis=1)
