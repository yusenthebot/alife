"""R132 — Wolf-Sheep-Grass: a three-level food chain you can watch breathe.

The classic agent ecosystem (the NetLogo "Wolf Sheep Predation" model): grass regrows on a timer,
SHEEP wander and graze it for energy, breed when fed and starve when not; WOLVES wander and eat sheep,
breed and starve likewise. Nothing is tuned to oscillate, yet the three populations fall into the
textbook boom-and-bust of predator and prey: sheep multiply on lush grass, wolves multiply on the
sheep, the sheep crash, the wolves starve in their wake, the grass recovers, and it begins again. The
predator population LAGS the prey (it can only grow after its food does), and the sheep ANTI-correlate
with the grass (a sheep boom eats the field bare). It is the simplest world that is recognisably ALIVE.

Agent-based on a toroidal grid (sheep/wolves are arrays of position+energy; grass is a regrow-timer
grid), so you watch the spatial herds AND the population cycles. Pure numpy/CPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class WolfSheepConfig:
    L: int = 45
    regrow: int = 30          # steps for a grazed patch to regrow
    s_gain: float = 4.0       # energy a sheep gets from grass
    w_gain: float = 25.0      # energy a wolf gets from a sheep
    s_repro: float = 0.04     # sheep reproduction probability (when fed)
    w_repro: float = 0.05     # wolf reproduction probability (when fed)
    move_cost: float = 1.0    # energy lost per step
    n_sheep: int = 300
    n_wolf: int = 60
    steps: int = 3000
    seed: int = 0
    no_wolves: bool = False   # control: remove predators


def run(cfg: WolfSheepConfig, record_every: int = 0):
    rng = np.random.default_rng(cfg.seed)
    L = cfg.L
    grass = np.ones((L, L), bool)
    timer = np.zeros((L, L), int)
    sx = rng.integers(0, L, cfg.n_sheep); sy = rng.integers(0, L, cfg.n_sheep); se = rng.uniform(2, 8, cfg.n_sheep)
    wx = rng.integers(0, L, cfg.n_wolf); wy = rng.integers(0, L, cfg.n_wolf); we = rng.uniform(5, 20, cfg.n_wolf)
    if cfg.no_wolves:
        wx, wy, we = wx[:0], wy[:0], we[:0]
    S, W, G, snaps = [], [], [], []
    for t in range(cfg.steps):
        # sheep move, graze, breed, starve
        sx = (sx + rng.integers(-1, 2, sx.size)) % L; sy = (sy + rng.integers(-1, 2, sy.size)) % L
        se = se - cfg.move_cost
        al = grass[sy, sx]
        se[al] += cfg.s_gain; grass[sy[al], sx[al]] = False; timer[sy[al], sx[al]] = cfg.regrow
        rep = (se > 4) & (rng.random(se.size) < cfg.s_repro)
        if rep.any():
            se[rep] /= 2; sx = np.r_[sx, sx[rep]]; sy = np.r_[sy, sy[rep]]; se = np.r_[se, se[rep]]
        k = se > 0; sx, sy, se = sx[k], sy[k], se[k]
        # wolves move, eat sheep, breed, starve
        if we.size:
            wx = (wx + rng.integers(-1, 2, wx.size)) % L; wy = (wy + rng.integers(-1, 2, wy.size)) % L
            we = we - cfg.move_cost
            sidx = -np.ones((L, L), int); sidx[sy, sx] = np.arange(sx.size)
            hit = sidx[wy, wx]; eat = hit >= 0; we[eat] += cfg.w_gain
            eaten = np.unique(hit[eat][hit[eat] >= 0])
            sm = np.ones(sx.size, bool); sm[eaten] = False; sx, sy, se = sx[sm], sy[sm], se[sm]
            rep = (we > 20) & (rng.random(we.size) < cfg.w_repro)
            if rep.any():
                we[rep] /= 2; wx = np.r_[wx, wx[rep]]; wy = np.r_[wy, wy[rep]]; we = np.r_[we, we[rep]]
            k = we > 0; wx, wy, we = wx[k], wy[k], we[k]
        # grass regrows
        timer[~grass] -= 1; grass[(timer <= 0) & ~grass] = True
        S.append(sx.size); W.append(wx.size); G.append(int(grass.sum()))
        if record_every and (t % record_every == 0 or t == cfg.steps - 1):
            snaps.append((grass.copy(), np.c_[sx, sy], np.c_[wx, wy]))
        if sx.size == 0:
            break
    return {"sheep": np.asarray(S), "wolves": np.asarray(W), "grass": np.asarray(G),
            "snaps": snaps, "L": L}


def predator_lag(sheep, wolves, max_lag=200, burn=400) -> int:
    """Cross-correlation lag of wolves vs sheep (positive => the predator FOLLOWS the prey)."""
    s = sheep[burn:].astype(float); w = wolves[burn:].astype(float)
    if s.size < 50 or s.std() < 1e-9 or w.std() < 1e-9:
        return 0
    s = s - s.mean(); w = w - w.mean()
    xc = np.correlate(w, s, "full")
    lags = np.arange(-s.size + 1, s.size)
    near = np.abs(lags) <= max_lag
    return int(lags[near][np.argmax(xc[near])])


def coexists(res, burn=400) -> bool:
    return bool(len(res["sheep"]) >= burn and res["sheep"][-1] > 0 and res["wolves"][-1] > 0)
