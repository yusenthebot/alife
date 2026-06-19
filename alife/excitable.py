"""R88 — Excitable media: spiral waves and re-entry (Greenberg-Hastings).

A new flavor of self-organization: not reaction-diffusion (R45 Gray-Scott PDE) and not a life-like CA
(R46 Conway), but an EXCITABLE medium. Each cell cycles rest -> excited -> refractory -> rest: a
resting cell fires only when enough neighbours are firing, then is forced through a refractory period
before it can fire again (Greenberg & Hastings 1978). Two consequences set excitable media apart from
ordinary waves: colliding waves ANNIHILATE (each runs into the other's refractory tail and dies), and
a BROKEN wavefront curls around its own free end into a SELF-SUSTAINING SPIRAL that rotates forever
with no pacemaker — re-entry. It is the textbook model of BZ chemical spirals and, ominously, of
cardiac arrhythmia (a rotating spiral = tachycardia; spiral breakup = fibrillation).

State encoding: 0 = resting, 1 = excited (the wavefront), 2..k-1 = refractory, then back to 0.
Vectorized via scipy convolution; CPU-fast.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import convolve2d

MOORE = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.int32)


def gh_step(state, k, thresh=1, kernel=MOORE):
    """One Greenberg-Hastings update. Resting cells fire if >= thresh excited neighbours; everything
    non-resting advances along the refractory cycle (k-1 -> 0)."""
    excited = (state == 1).astype(np.int32)
    n_exc = convolve2d(excited, kernel, mode="same", boundary="fill")
    fired = (state == 0) & (n_exc >= thresh)
    nxt = np.where(state == 0, 0, (state + 1) % k)        # advance refractory; rest stays rest
    nxt[fired] = 1
    return nxt.astype(state.dtype)


def run(state0, k, thresh=1, steps=300, record_every=4, kernel=MOORE):
    """Evolve; return recorded frames and the per-step excited-cell count (activity)."""
    s = state0.copy()
    frames, activity = [s.copy()], [int((s == 1).sum())]
    for t in range(1, steps + 1):
        s = gh_step(s, k, thresh, kernel)
        activity.append(int((s == 1).sum()))
        if t % record_every == 0:
            frames.append(s.copy())
    return frames, np.asarray(activity)


def planar_wave_ic(h, w, k, col=8):
    """A vertical wavefront at `col` with its refractory tail behind it (waves travel right)."""
    s = np.zeros((h, w), np.int32)
    s[:, col] = 1                                          # excited front
    for r in range(1, k - 1):                              # refractory tail to the left
        c = col - r
        if c >= 0:
            s[:, c] = r + 1
    return s


def two_wave_ic(h, w, k, gap=30):
    """Two planar waves set to travel toward each other (to test annihilation on collision)."""
    s = np.zeros((h, w), np.int32)
    cL, cR = w // 2 - gap, w // 2 + gap
    s[:, cL] = 1
    s[:, cR] = 1
    for r in range(1, k - 1):
        if cL - r >= 0:
            s[:, cL - r] = r + 1                           # left wave's tail behind it -> moves right
        if cR + r < w:
            s[:, cR + r] = r + 1                           # right wave's tail behind it -> moves left
    return s


def spiral_ic(h, w, k):
    """A BROKEN planar wave: a full wavefront whose lower half is erased to resting. The free end at
    mid-height curls around itself into a rotating spiral (re-entry)."""
    s = planar_wave_ic(h, w, k, col=w // 2)
    s[h // 2:, :] = 0                                      # cut the wave -> a free end at the middle
    return s


def wavefront_speed(frames, record_every):
    """Mean rightward speed (cells/step) of a planar wavefront, from the front column over frames."""
    cols = []
    for f in frames:
        ex = np.argwhere(f == 1)
        cols.append(ex[:, 1].max() if ex.size else np.nan)
    cols = np.asarray(cols, float)
    good = ~np.isnan(cols)
    if good.sum() < 2:
        return 0.0
    idx = np.arange(len(cols))[good] * record_every
    return float(np.polyfit(idx, cols[good], 1)[0])


def dominant_period(activity, burn=50):
    """Rotation period of a sustained spiral, from the autocorrelation of the activity series."""
    a = activity[burn:].astype(float)
    a = a - a.mean()
    if a.std() < 1e-9:
        return 0.0
    ac = np.correlate(a, a, mode="full")[len(a) - 1:]
    ac /= ac[0]
    # first local maximum after the autocorrelation dips below zero = the period
    below = np.where(ac < 0)[0]
    if not below.size:
        return 0.0
    start = below[0]
    peak = start + int(np.argmax(ac[start:start + len(a) // 2]))
    return float(peak)
