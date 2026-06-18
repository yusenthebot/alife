"""R78 — Diffusion-limited aggregation (Witten-Sander 1981): growth into a fractal.

Another route to emergent form. Particles wander by Brownian motion and freeze the instant they
touch a growing cluster. Because a wanderer almost always hits a protruding tip before it can
work its way into a fjord, the cluster grows into a sprawling, self-similar DENDRITE — the shape
of mineral dendrites, electrodeposits, coral, soot and lightning. Its fractal dimension is a
universal ~1.71 in 2D (mass grows with radius as r^1.71, not r^2 — the cluster is mostly empty
space). One local rule, stick-on-contact, makes a fractal; lowering the sticking probability lets
walkers probe deeper before freezing, growing a denser, less ramified cluster.

Fast random walk: huge isotropic jumps when far from the cluster (statistically exact for an
unbiased walk), unit steps only near the front; respawn walkers that escape a kill radius.
Pure numpy/CPU.
"""

from __future__ import annotations

import numpy as np


def grow(size: int = 301, n_particles: int = 4000, stick: float = 1.0, seed: int = 0,
         seed_shape: str = "point"):
    """Grow a DLA cluster. Returns the occupancy grid, an 'arrival order' grid (-1 empty, else
    the step a cell froze, for colouring) and the cluster radius."""
    rng = np.random.default_rng(seed)
    occ = np.zeros((size, size), bool)
    order = np.full((size, size), -1, dtype=np.int64)
    c = size // 2
    front = size - 2                                   # for line seed: current tallest reached (min row)
    if seed_shape == "line":
        occ[size - 2, :] = True; order[size - 2, :] = 0
        rmax = 0.0
    else:
        occ[c, c] = True; order[c, c] = 0
        rmax = 1.0
    placed = 0
    for p in range(1, n_particles + 1):
        if seed_shape == "line":                       # rain particles from just above the front
            x = float(rng.integers(1, size - 1)); y = float(max(1, front - 3))
        else:
            ang = rng.uniform(0, 2 * np.pi)
            r0 = min(rmax + 5, c - 2)
            x, y = c + r0 * np.cos(ang), c + r0 * np.sin(ang)
        kill = (rmax + 25) if seed_shape != "line" else size
        while True:
            ix, iy = int(round(x)), int(round(y))
            if ix < 1 or ix >= size - 1 or iy < 1 or iy >= size - 1:
                break                                  # left the grid -> abandon this walker
            if (not occ[iy, ix]) and (occ[iy - 1, ix] or occ[iy + 1, ix]
                                      or occ[iy, ix - 1] or occ[iy, ix + 1]):
                if rng.random() < stick:
                    occ[iy, ix] = True; order[iy, ix] = p; placed += 1
                    rmax = max(rmax, np.hypot(ix - c, iy - c))
                    front = min(front, iy)
                    break
            if seed_shape == "line":
                if y < front - 10:                     # wandered too high above the front -> respawn
                    break
                step = 1.0
            else:
                d = np.hypot(x - c, y - c)
                if d > kill:
                    break                              # escaped -> respawn next particle
                step = max(1.0, d - rmax - 2.0)        # big jumps far away, unit steps near front
            a = rng.uniform(0, 2 * np.pi)
            x += step * np.cos(a); y += step * np.sin(a)
    return {"occ": occ, "order": order, "rmax": rmax, "placed": placed, "center": c}


def fractal_dimension(occ: np.ndarray, center: int, rmin: int = 4, rmax: int = None):
    """Mass-radius scaling: M(r) = occupied cells within radius r ~ r^D. Returns (radii, mass, D)."""
    ys, xs = np.nonzero(occ)
    d = np.hypot(xs - center, ys - center)
    rmax = rmax or int(d.max() * 0.8)
    radii = np.arange(rmin, rmax)
    mass = np.array([(d <= r).sum() for r in radii], float)
    ok = mass > 0
    D = np.polyfit(np.log(radii[ok]), np.log(mass[ok]), 1)[0]
    return radii[ok], mass[ok], float(D)
