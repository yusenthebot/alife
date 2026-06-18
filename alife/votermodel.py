"""R82 — The voter model: consensus without surface tension (and the contrast that needs it).

A foundational interacting-particle system, and a clean counterpoint to this project's other
lattice models. Each site holds one of two opinions; in the VOTER model a site simply copies a
random neighbour. From a random start, opinion domains coarsen — but with NO SURFACE TENSION:
boundaries stay rough and fractal, coarsening crawls, and the mean opinion drifts only by an
unbiased random walk (conserved on average — a martingale). Swap the rule for MAJORITY (a site
adopts its neighbours' majority, plus a little noise) and SURFACE TENSION appears: boundaries
pull straight, round domains grow fast (curvature-driven, L~t^1/2), and the interface density
collapses. Same lattice, two rules, two universality classes — imitation vs conformity.

(The exact voter result that fixation probability equals the initial density needs asynchronous
single-site updates; here we use synchronous half-site updates — fast and faithful for the
coarsening / surface-tension contrast and the driftless mean opinion.)

Pure numpy/CPU.
"""

from __future__ import annotations

import numpy as np


def _neighbors(grid):
    return (np.roll(grid, 1, 0), np.roll(grid, -1, 0), np.roll(grid, 1, 1), np.roll(grid, -1, 1))


def voter_step(grid, rng, frac=0.5):
    """Each updated site copies a uniformly-random one of its 4 neighbours."""
    up, dn, lf, rt = _neighbors(grid)
    choice = rng.integers(0, 4, grid.shape)
    nb = np.where(choice == 0, up, np.where(choice == 1, dn, np.where(choice == 2, lf, rt)))
    mask = rng.random(grid.shape) < frac
    out = grid.copy(); out[mask] = nb[mask]
    return out


def majority_step(grid, rng, frac=0.5, noise=0.0):
    """Each updated site adopts the majority of its 4 neighbours (ties keep current); optional
    noise flips a small fraction (temperature). Majority introduces surface tension."""
    up, dn, lf, rt = _neighbors(grid)
    s = up + dn + lf + rt
    nb = np.where(s > 0, 1, np.where(s < 0, -1, grid))
    if noise:
        flip = rng.random(grid.shape) < noise
        nb = np.where(flip, -nb, nb)
    mask = rng.random(grid.shape) < frac
    out = grid.copy(); out[mask] = nb[mask]
    return out


def interface_density(grid):
    """Fraction of nearest-neighbour bonds joining DIFFERENT opinions (boundary length / area)."""
    diff = 0
    for ax in (0, 1):
        diff += np.mean(grid != np.roll(grid, 1, axis=ax))
    return float(diff / 2)


def magnetization(grid):
    return float(grid.mean())


def run(size=128, steps=300, rule="voter", p_up=0.5, seed=0, noise=0.0, record_every=0):
    """Run voter/majority dynamics from a random start with +1 fraction p_up."""
    rng = np.random.default_rng(seed)
    grid = np.where(rng.random((size, size)) < p_up, 1, -1).astype(np.int8)
    step = voter_step if rule == "voter" else (lambda g, r: majority_step(g, r, noise=noise))
    iface, mag, snaps = [interface_density(grid)], [magnetization(grid)], {}
    if record_every:
        snaps[0] = grid.copy()
    for t in range(1, steps + 1):
        grid = step(grid, rng)
        iface.append(interface_density(grid)); mag.append(magnetization(grid))
        if record_every and (t % record_every == 0 or t == steps):
            snaps[t] = grid.copy()
    return {"grid": grid, "interface": np.array(iface), "mag": np.array(mag), "snaps": snaps}


def ensemble_mag_drift(size=64, steps=300, rule="voter", trials=12, seed=0, noise=0.03):
    """Final magnetizations across trials. Voter: driftless random walk (ensemble mean ~ initial
    0 = martingale/conservation). Majority: surface tension drives each run toward consensus."""
    rng = np.random.default_rng(seed)
    finals = []
    for _ in range(trials):
        r = run(size, steps, rule, p_up=0.5, seed=int(rng.integers(1 << 30)), noise=noise)
        finals.append(r["mag"][-1])
    return np.array(finals)
