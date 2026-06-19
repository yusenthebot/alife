"""R104 — Granular media: why an hourglass keeps perfect time (Beverloo's law).

Sand is neither solid nor liquid. Drain a tank of water and the flow slows as it empties (the
pressure head drops); drain a hopper of sand and it pours at a CONSTANT rate until nearly empty —
which is exactly why an hourglass keeps time. The reason is that grains, unlike a fluid, carry stress
in force chains that screen the weight above the orifice, so only grains within ~one opening-width
feel the exit. The discharge rate follows Beverloo's law, W ~ (D - k·d)^{3/2} in 2D-ish scaling, and
below a few grain diameters the opening JAMS and flow stops altogether. This is a soft-sphere
Discrete Element Method: disks under gravity with linear spring-dashpot repulsion, draining through a
gap in the floor. Constant-rate flow and jamming emerge from the contacts; no rule says "flow
steadily".

Pure numpy + scipy cKDTree; symplectic Euler. CPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree


@dataclass(frozen=True)
class HopperConfig:
    n: int = 900
    radius: float = 1.0
    width: float = 80.0       # container width
    orifice: float = 12.0     # opening width at the centre of the floor
    g: float = 0.02
    k_n: float = 1.0
    gamma_n: float = 0.4
    dt: float = 0.5
    steps: int = 4000


def _accel(pos, vel, cfg):
    n = len(pos)
    F = np.zeros((n, 2))
    F[:, 1] -= cfg.g
    r = cfg.radius
    tree = cKDTree(pos)
    pairs = tree.query_pairs(2 * r, output_type="ndarray")
    if len(pairs):
        i, j = pairs[:, 0], pairs[:, 1]
        d = pos[i] - pos[j]
        dist = np.hypot(d[:, 0], d[:, 1]) + 1e-12
        overlap = 2 * r - dist
        hit = overlap > 0
        i, j, d, dist, overlap = i[hit], j[hit], d[hit], dist[hit], overlap[hit]
        nrm = d / dist[:, None]
        vn = ((vel[i] - vel[j]) * nrm).sum(1)
        fn = np.maximum(cfg.k_n * overlap - cfg.gamma_n * vn, 0.0)
        force = fn[:, None] * nrm
        np.add.at(F, i, force); np.add.at(F, j, -force)
    # side walls (repulsive)
    left = pos[:, 0] < r
    F[left, 0] += cfg.k_n * (r - pos[left, 0])
    right = pos[:, 0] > cfg.width - r
    F[right, 0] -= cfg.k_n * (pos[right, 0] - (cfg.width - r))
    # floor at y=0 EXCEPT the central orifice (grains over the gap fall through)
    cx = cfg.width / 2
    over_gap = np.abs(pos[:, 0] - cx) < cfg.orifice / 2
    on_floor = (pos[:, 1] < r) & (~over_gap)
    if on_floor.any():
        F[on_floor, 1] += np.maximum(cfg.k_n * (r - pos[on_floor, 1]) - cfg.gamma_n * vel[on_floor, 1], 0.0)
    return F


def simulate(cfg=HopperConfig(), seed=0, settle=600):
    """Fill the hopper, let it settle, then drain through the orifice. Returns the cumulative number
    discharged over time (grains that fell well below the floor)."""
    rng = np.random.default_rng(seed)
    n = cfg.n
    cols = int(cfg.width / (2 * cfg.radius))
    # pack grains in a grid above the floor (jittered) to fill the container
    xs = (np.arange(n) % cols) * 2 * cfg.radius + cfg.radius
    ys = (np.arange(n) // cols) * 2 * cfg.radius + cfg.radius + 4
    pos = np.column_stack([xs, ys]).astype(float) + rng.uniform(-0.2, 0.2, (n, 2))
    vel = np.zeros((n, 2))
    discharged = np.zeros(n, bool)
    exit_y = -6 * cfg.radius
    cum = []
    for t in range(cfg.steps):
        active = ~discharged
        F = _accel(pos, vel, cfg)
        vel[active] += F[active] * cfg.dt
        vel[active] *= 0.999
        pos[active] += vel[active] * cfg.dt
        newly = active & (pos[:, 1] < exit_y)
        discharged |= newly
        # recycle discharged grains far away & frozen so they don't interact
        pos[discharged] = np.array([-100.0, -100.0])
        vel[discharged] = 0.0
        if t >= settle:
            cum.append(int(discharged.sum()))
    return {"cum": np.asarray(cum), "discharged": int(discharged.sum()), "pos": pos}


def discharge_rate(result, n_total=None):
    """Steady discharge rate (grains/step): slope over the STEADY-FLOW window — after start-up and
    before the hopper runs low — so it isn't corrupted by the empty-out tail of a fast drain."""
    cum = result["cum"].astype(float)
    if len(cum) < 60 or cum[-1] < 5:
        return 0.0
    total = cum[-1]
    # window where the hopper is steadily flowing: between 10% and 70% discharged
    win = (cum >= 0.10 * total) & (cum <= 0.70 * total)
    if win.sum() < 20:                                       # very fast/slow drain: use a head window
        win = np.zeros(len(cum), bool); win[: max(20, len(cum) // 3)] = True
    t = np.arange(len(cum))[win]
    return float(np.polyfit(t, cum[win], 1)[0])


def beverloo_curve(orifices, cfg=HopperConfig(), seed=0):
    """Steady discharge rate vs orifice width (Beverloo: rate grows super-linearly; jams when small)."""
    from dataclasses import replace
    rates = []
    for D in orifices:
        r = simulate(replace(cfg, orifice=float(D)), seed=seed)
        rates.append(discharge_rate(r))
    return np.asarray(orifices, float), np.asarray(rates)
