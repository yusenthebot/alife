"""R96 — Kuramoto oscillators: spontaneous synchronization from coupling alone.

Fireflies flashing in unison, metronomes on a shared table, pacemaker cells, power-grid generators —
all are populations of oscillators with slightly different natural rhythms that nonetheless lock into
step. Kuramoto's model captures it with one equation: each phase advances at its own frequency plus a
pull toward its neighbours, dθ_i/dt = ω_i + (K/N) Σ_j sin(θ_j − θ_i). Below a critical coupling Kc
the oscillators drift incoherently (order parameter r ≈ 0); above it a synchronized cluster nucleates
and grows (r → 1) — a continuous phase transition whose threshold Kc = 2/(π g(0)) depends only on the
spread of natural frequencies. Collective rhythm emerging from coupling, with no leader and no clock.

Mean-field exact-sum form (O(N) per step via the order parameter); pure numpy/CPU.
"""

from __future__ import annotations

import numpy as np


def order_parameter(theta):
    """r e^{iψ} = mean of e^{iθ}; r in [0,1] measures phase coherence (0 incoherent, 1 locked)."""
    z = np.mean(np.exp(1j * theta))
    return np.abs(z), np.angle(z)


def gaussian_kc(sigma):
    """Kuramoto's critical coupling for Gaussian natural frequencies: Kc = 2/(π g(0))."""
    g0 = 1.0 / (sigma * np.sqrt(2 * np.pi))
    return 2.0 / (np.pi * g0)                              # = 2σ√(2/π) ≈ 1.596 σ


def run(n=800, K=2.0, sigma=1.0, dt=0.05, steps=1200, seed=0, track_freq=False):
    """Integrate the Kuramoto model; return r over time (and optionally effective frequencies)."""
    rng = np.random.default_rng(seed)
    omega = rng.normal(0.0, sigma, n)
    theta = rng.uniform(-np.pi, np.pi, n)
    r_hist = []
    phase_acc = np.zeros(n)
    burn = steps // 2
    for t in range(steps):
        z = np.mean(np.exp(1j * theta))
        r, psi = np.abs(z), np.angle(z)
        dtheta = omega + K * r * np.sin(psi - theta)       # mean-field form of the coupling sum
        theta = theta + dt * dtheta
        r_hist.append(r)
        if track_freq and t >= burn:
            phase_acc += dtheta * dt
    out = {"r": np.asarray(r_hist), "final_r": float(np.mean(r_hist[burn:])),
           "theta": np.mod(theta + np.pi, 2 * np.pi) - np.pi, "omega": omega}
    if track_freq:
        out["eff_freq"] = phase_acc / ((steps - burn) * dt)
    return out


def sweep_coupling(Ks, n=800, sigma=1.0, dt=0.05, steps=1200, seed=0):
    """Steady-state coherence r as a function of coupling K (the synchronization transition)."""
    rng = np.random.default_rng(seed)
    out = []
    for K in Ks:
        out.append(run(n, float(K), sigma, dt, steps, seed=int(rng.integers(1 << 30)))["final_r"])
    return np.asarray(Ks, float), np.asarray(out)
