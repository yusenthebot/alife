"""R118 — Phyllotaxis: why sunflowers count in Fibonacci and turn by the golden angle.

Look down the head of a sunflower, a pinecone, a pineapple: the florets spiral, and if you count the
spiral arms you get consecutive Fibonacci numbers (34 one way, 55 the other). The seeds sit at a fixed
DIVERGENCE ANGLE from one to the next, and that angle is the golden angle, 360*(2-phi) ~ 137.507deg.
Two questions: why that angle, and how does a plant "know" it?

WHY (Vogel 1979): place organ n at angle n*alpha and radius proportional to sqrt(n) (constant area per
organ). The packing is uniform and gap-free only when alpha is the MOST IRRATIONAL number — the golden
ratio — so that no two organs ever line up radially. Any rational fraction p/q gives q radial spokes
with big gaps between; even a tenth of a degree off golden opens visible gaps. The golden angle
uniquely maximises how spread-out (least-crowded) the packing is.

HOW (Douady & Couder 1992): no plant computes phi. Each new primordium simply forms at the edge of the
growing tip in the LEAST CROWDED spot — wherever the repulsion from existing primordia (which drift
outward) is weakest. Iterating that purely local rule, the divergence angle self-organises onto the
golden angle (with a secondary "Lucas" branch near 99.5deg for other growth rates). The famous
Fibonacci spirals fall out of a one-line greedy rule, no global plan.

This module builds Vogel's static lattice, measures packing uniformity vs angle, and runs the
Douady-Couder dynamical rule to show the golden angle emerging. Pure numpy/scipy.
"""

from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree

PHI = (1.0 + np.sqrt(5.0)) / 2.0
GOLDEN_ANGLE = 360.0 * (2.0 - PHI)        # ~137.5077 degrees


def vogel(alpha_deg: float, n: int = 600, c: float = 1.0):
    """Vogel spiral: organ k at angle k*alpha, radius c*sqrt(k) (equal area per organ)."""
    k = np.arange(1, n + 1)
    th = np.radians(alpha_deg) * k
    r = c * np.sqrt(k)
    return np.column_stack([r * np.cos(th), r * np.sin(th)])


def nn_distance(points):
    """Distance from each point to its nearest neighbour."""
    d, _ = cKDTree(points).query(points, k=2)
    return d[:, 1]


def packing_uniformity(points):
    """min nearest-neighbour distance (large = no two organs crowd) and coefficient of variation."""
    nn = nn_distance(points)
    return {"min_nn": float(nn.min()), "mean_nn": float(nn.mean()),
            "cv": float(nn.std() / nn.mean())}


def uniformity_curve(alphas, n: int = 600):
    """min-NN distance vs divergence angle: peaks sharply at the golden angle."""
    mn = np.array([packing_uniformity(vogel(a, n))["min_nn"] for a in alphas])
    return np.asarray(alphas, float), mn


def douady_couder(n: int = 320, G: float = 0.28, p: float = 3.0, R0: float = 1.0, n_ang: int = 2880):
    """Greedy least-crowding rule: each new primordium appears on the apex circle at the angle that
    minimises repulsion (sum 1/d^p) from existing primordia, which drift out radially (r *= exp(G))."""
    cand = np.linspace(0.0, 2.0 * np.pi, n_ang, endpoint=False)
    r = np.zeros(0)
    th = np.zeros(0)
    div = []
    for _ in range(n):
        r = r * np.exp(G)
        if r.size:
            d2 = R0 ** 2 + r[:, None] ** 2 - 2.0 * R0 * r[:, None] * np.cos(cand[None, :] - th[:, None])
            new = cand[int(np.argmin((d2 ** (-p / 2.0)).sum(0)))]
        else:
            new = 0.0
        if th.size:
            div.append(np.degrees((new - th[-1]) % (2.0 * np.pi)))
        r = np.append(r, R0)
        th = np.append(th, new)
    d = np.asarray(div)
    return {"r": r, "theta": th, "divergence": np.where(d > 180.0, 360.0 - d, d)}


def emergent_angle(G: float = 0.28, n: int = 320, drop: int = 150, **kw) -> float:
    """The divergence angle the least-crowding rule locks onto (mean of the converged tail)."""
    return float(np.mean(douady_couder(n=n, G=G, **kw)["divergence"][drop:]))


def bifurcation(Gs, n: int = 260, drop: int = 120):
    """Emergent locked divergence angle vs growth rate G — reveals the golden and Lucas branches."""
    return np.asarray(Gs, float), np.array([emergent_angle(G=float(g), n=n, drop=drop) for g in Gs])


def fibonacci_convergents(k: int = 8):
    """The continued-fraction convergents of the golden angle are ratios of consecutive Fibonacci
    numbers — which is exactly why the visible spiral-arm (parastichy) counts are Fibonacci."""
    fib = [1, 1]
    for _ in range(k):
        fib.append(fib[-1] + fib[-2])
    return fib
