"""R105 — Explosive synchronization: when sync snaps on like a switch.

R96's Kuramoto oscillators, on an all-to-all mean field, synchronize through a smooth second-order
transition: coherence rises continuously past the critical coupling. Put the same oscillators on a
SCALE-FREE network and correlate each node's natural frequency with its degree (hubs beat fastest)
and the transition changes character entirely — it becomes EXPLOSIVE: coherence stays near zero, then
jumps abruptly to near one at a critical coupling, and the path back down follows a *different* curve,
leaving a HYSTERESIS loop (Gómez-Gardeñes et al. 2011). A first-order, switch-like, irreversible
synchronization — the kind blamed for sudden onsets like epileptic seizures and power-grid cascades.
Destroy the frequency-degree correlation (shuffle the frequencies) and the smooth, reversible
transition returns: the control that proves the correlation is what makes sync explosive.

Reuses alife.network (Barabási-Albert graph) and alife.kuramoto (order parameter). Pure numpy.
"""

from __future__ import annotations

import numpy as np

from alife.network import ba_graph, degrees
from alife.kuramoto import order_parameter


def _equilibrate(theta, omega, i, j, n, K, mean_k, dt, equil, measure):
    """Integrate Kuramoto on a graph (edge list i,j); return mean coherence over the measure window."""
    rs = []
    for t in range(equil + measure):
        diff = np.sin(theta[j] - theta[i])
        coup = np.zeros(n)
        np.add.at(coup, i, diff)
        np.add.at(coup, j, -diff)
        theta = theta + dt * (omega + (K / mean_k) * coup)
        if t >= equil:
            rs.append(order_parameter(theta)[0])
    return theta, float(np.mean(rs))


def hysteresis_sweep(omega, edges, n, Ks, dt=0.05, equil=400, measure=120, seed=0):
    """Adiabatic forward (ascending K, from incoherent) then backward (descending, continuing from the
    synced state) sweep. Returns r_forward, r_backward — they differ when sync is explosive."""
    i, j = edges[:, 0], edges[:, 1]
    mean_k = 2 * len(edges) / n
    rng = np.random.default_rng(seed)
    theta = rng.uniform(-np.pi, np.pi, n)
    rf = []
    for K in Ks:
        theta, r = _equilibrate(theta, omega, i, j, n, float(K), mean_k, dt, equil, measure)
        rf.append(r)                                          # carry state forward (adiabatic)
    rb = []
    for K in Ks[::-1]:
        theta, r = _equilibrate(theta, omega, i, j, n, float(K), mean_k, dt, equil, measure)
        rb.append(r)
    return np.asarray(rf), np.asarray(rb[::-1])


def hysteresis_area(Ks, rf, rb):
    """Area between the forward and backward coherence curves (>0 = first-order/explosive)."""
    return float(np.trapezoid(np.abs(rf - rb), Ks)) if hasattr(np, "trapezoid") else float(np.trapz(np.abs(rf - rb), Ks))


def degree_frequencies(edges, n, shuffle=False, seed=0):
    """Natural frequencies = node degree (zero-mean). shuffle=True breaks the degree-frequency
    correlation while keeping the same frequency distribution (the control)."""
    k = degrees(edges, n).astype(float)
    omega = (k - k.mean()) / (k.std() + 1e-9)                 # zero-mean, unit-std (correlation with k preserved)
    if shuffle:
        omega = np.random.default_rng(seed).permutation(omega)
    return omega


def run(n=500, m=3, Ks=None, seed=0, shuffle=False, **kw):
    """Build a scale-free net, set frequency=degree (or shuffled control), sweep coupling both ways."""
    edges = ba_graph(n, m=m, seed=seed)
    omega = degree_frequencies(edges, n, shuffle=shuffle, seed=seed)
    Ks = np.asarray(Ks) if Ks is not None else np.linspace(0.0, 3.0, 16)
    rf, rb = hysteresis_sweep(omega, edges, n, Ks, seed=seed, **kw)
    return {"Ks": Ks, "rf": rf, "rb": rb, "area": hysteresis_area(Ks, rf, rb)}
