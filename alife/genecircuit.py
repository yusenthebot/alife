"""R108 — Synthetic gene circuits: the repressilator clock and the toggle switch.

Life computes with gene circuits, and the founding demonstration that we can DESIGN them was a pair of
1990s constructs. The REPRESSILATOR (Elowitz & Leibler 2000) is a ring of three genes each repressing
the next, A⊣B⊣C⊣A: the loop can never settle, so protein levels chase each other forever — a genetic
oscillator, life's clock built from three parts. The TOGGLE SWITCH (Gardner, Cantor & Collins 2000)
is two genes repressing each other: it has two stable states and remembers which one it's in — a
one-bit memory. Both run on the same Hill-repression kinetics; what decides oscillation vs memory is
the LOOP PARITY (an odd repression ring oscillates, an even one is bistable) and the COOPERATIVITY
(the Hill coefficient must exceed ~1 for either to work). Designed dynamics from the logic of
repression.

ODE integration (scipy solve_ivp); CPU.
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp


def repressor_ring(n_genes=3, hill=2.0, alpha=10.0, alpha0=0.1, beta=1.0, t_max=200.0,
                   seed=0, n_eval=2000):
    """Ring of n_genes, gene i repressed by protein of gene i-1 (mod n). mRNA m_i, protein p_i.
    Returns time + protein trajectories. Odd ring -> oscillates; even ring -> bistable."""
    rng = np.random.default_rng(seed)
    n = n_genes

    def deriv(t, y):
        m = y[:n]; p = y[n:]
        rep = p[np.arange(n) - 1]                            # protein of the upstream repressor (i-1)
        dm = -m + alpha / (1.0 + rep ** hill) + alpha0
        dp = beta * (m - p)
        return np.concatenate([dm, dp])

    y0 = np.concatenate([rng.uniform(0, 2, n), rng.uniform(0, 2, n)])
    sol = solve_ivp(deriv, (0, t_max), y0, t_eval=np.linspace(0, t_max, n_eval),
                    method="LSODA", rtol=1e-7, atol=1e-9)
    return {"t": sol.t, "proteins": sol.y[n:], "mrna": sol.y[:n]}


def oscillation_amplitude(result, tail=0.4):
    """Peak-to-peak amplitude of gene 0's protein over the late (steady) portion — 0 if it settled."""
    p = result["proteins"][0]
    seg = p[int((1 - tail) * len(p)):]
    return float(seg.max() - seg.min())


def is_oscillating(result, thresh=0.2):
    return oscillation_amplitude(result) > thresh


def oscillation_period(result, tail=0.6):
    """Period from the autocorrelation of gene 0's protein (steady portion)."""
    p = result["proteins"][0]
    seg = p[int((1 - tail) * len(p)):].astype(float)
    seg = seg - seg.mean()
    if seg.std() < 1e-9:
        return 0.0
    ac = np.correlate(seg, seg, "full")[len(seg) - 1:]
    ac /= ac[0]
    below = np.where(ac < 0)[0]
    if not below.size:
        return 0.0
    start = below[0]
    dt = result["t"][1] - result["t"][0]
    return float((start + np.argmax(ac[start:start + len(seg) // 2])) * dt)


def toggle_final_state(hill=3.0, alpha=10.0, beta=1.0, bias=0.0, seed=0, t_max=100.0):
    """Two mutually-repressing genes; return (p0, p1) at steady state. Bistable: the larger one wins,
    set by the initial condition (bias)."""
    rng = np.random.default_rng(seed)

    def deriv(t, y):
        m, p = y[:2], y[2:]
        rep = p[::-1]                                        # gene 0 repressed by p1, gene 1 by p0
        dm = -m + alpha / (1.0 + rep ** hill)
        dp = beta * (m - p)
        return np.concatenate([dm, dp])

    y0 = np.array([0.0, 0.0, 1.0 + bias, 1.0 - bias]) + rng.uniform(0, 0.05, 4)
    sol = solve_ivp(deriv, (0, t_max), y0, method="LSODA", rtol=1e-7, atol=1e-9)
    return float(sol.y[2, -1]), float(sol.y[3, -1])
