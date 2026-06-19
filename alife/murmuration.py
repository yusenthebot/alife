"""R134 — Murmuration vs a predator: why a flock flees as one.

A starling murmuration boiling away from a falcon is collective ANTI-PREDATOR behaviour: no bird sees
the whole flock, yet the group flows around the hawk, splits, and reforms, and the hawk mostly goes
hungry. The ingredient on top of plain flocking (cohesion + alignment + separation) is a FLEE response:
a bird that senses the predator steers directly away, and because its neighbours align with it the
turn propagates outward as a wave. The pay-off is dramatic and measurable: a flock that flees
collectively is caught vastly less often than the same prey ignoring the predator — safety in motion.

Model: boids (Reynolds) prey on a toroidal arena + a predator that chases the nearest prey; a prey
within sense range adds a strong flee force away from the predator; the predator catches (and the prey
respawns, holding the flock size). Flee ON -> the flock evades and the catch count collapses; flee OFF
(control) -> the predator parks in the herd and feeds. Neighbour queries via a periodic KD-tree. numpy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree


@dataclass(frozen=True)
class MurmurConfig:
    N: int = 160
    L: float = 55.0
    r_sep: float = 1.2
    r_nb: float = 5.0
    w_coh: float = 0.02
    w_ali: float = 0.18
    w_sep: float = 0.35
    flee: float = 1.8         # flee force from the predator (0 = no anti-predator behaviour, control)
    sense: float = 8.0        # distance at which prey notice the predator
    vmax: float = 1.1
    pvmax: float = 1.5        # predator slightly faster than prey
    catch: float = 1.3        # capture radius
    steps: int = 1500
    seed: int = 0


def _wrap(d, L):
    d = d.copy()
    d -= L * np.round(d / L)
    return d


def run(cfg: MurmurConfig, record_every: int = 0):
    rng = np.random.default_rng(cfg.seed)
    L, N = cfg.L, cfg.N
    p = rng.uniform(0, L, (N, 2)); v = rng.normal(0, 0.3, (N, 2))
    pp = rng.uniform(0, L, 2); pv = np.zeros(2)
    catches = 0
    near_d, pol_s, spread_s, snaps = [], [], [], []
    for t in range(cfg.steps):
        nbr = cKDTree(p % L, boxsize=L).query_ball_point(p % L, cfg.r_nb)
        coh = np.zeros((N, 2)); ali = np.zeros((N, 2)); sep = np.zeros((N, 2))
        for i, nb in enumerate(nbr):
            nb = [j for j in nb if j != i]
            if nb:
                coh[i] = _wrap(p[nb].mean(0) - p[i], L); ali[i] = v[nb].mean(0)
                dj = _wrap(p[i] - p[nb], L)
                close = (dj ** 2).sum(1) < cfg.r_sep ** 2
                if close.any():
                    sep[i] = dj[close].sum(0)
        dp = _wrap(p - pp, L); dist = np.hypot(dp[:, 0], dp[:, 1]); seen = dist < cfg.sense
        fl = np.zeros((N, 2)); fl[seen] = dp[seen] / np.maximum(dist[seen, None], 0.1)
        v = v + cfg.w_coh * coh + cfg.w_ali * ali + cfg.w_sep * sep + cfg.flee * fl
        sp = np.hypot(v[:, 0], v[:, 1]); v = v / np.maximum(sp[:, None], 1e-9) * np.minimum(sp, cfg.vmax)[:, None]
        p = (p + v) % L
        # predator chases nearest prey
        d = _wrap(p - pp, L); dd = np.hypot(d[:, 0], d[:, 1]); j = int(np.argmin(dd))
        pv = pv + 0.6 * (-_wrap(pp - p[j], L)) / max(dd[j], 0.1)
        ps = np.hypot(*pv); pv = pv / max(ps, 1e-9) * min(ps, cfg.pvmax); pp = (pp + pv) % L
        # catch (respawn to hold N)
        d = _wrap(p - pp, L); dd = np.hypot(d[:, 0], d[:, 1]); hit = np.where(dd < cfg.catch)[0]
        if hit.size:
            catches += 1; p[hit[0]] = rng.uniform(0, L, 2); v[hit[0]] = rng.normal(0, 0.3, 2)
        near_d.append(float(dd.min()))
        vu = v / np.maximum(np.hypot(v[:, 0], v[:, 1])[:, None], 1e-9)
        pol_s.append(float(np.hypot(*vu.mean(0))))
        spread_s.append(flock_spread(p, L))
        if record_every and (t % record_every == 0 or t == cfg.steps - 1):
            snaps.append((p.copy(), v.copy(), pp.copy()))
    half = len(pol_s) // 2
    return {"catches": catches, "near_dist": np.asarray(near_d),
            "polarization": float(np.mean(pol_s[half:])), "spread": float(np.mean(spread_s[half:])),
            "p": p, "v": v, "pp": pp, "snaps": snaps}


def flock_spread(p, L) -> float:
    """RMS distance of prey from the flock centroid (toroidal) — small = cohesive."""
    c = p.mean(0)
    d = _wrap(p - c, L)
    return float(np.sqrt((d ** 2).sum(1).mean()))
