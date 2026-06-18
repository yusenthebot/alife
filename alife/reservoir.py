"""R73 — Reservoir computing: a random recurrent network learns to dream a chaotic attractor.

A different idea of a brain. Instead of training a whole network, an Echo State Network fixes a
large RANDOM recurrent reservoir — a tangle of neurons at the edge of stability — and trains only
a linear readout off its activity. Drive the reservoir with a chaotic signal (the Lorenz system),
fit the readout to predict one step ahead, then close the loop: feed the network's own output back
as input and let it run free. With no further training it AUTONOMOUSLY regenerates the Lorenz
dynamics — tracking the true trajectory for several Lyapunov times before chaos pulls them apart,
yet continuing to trace the same butterfly "climate". High-dimensional random dynamics, harnessed
by a single linear layer. (Jaeger 2001; Pathak et al. 2018.) Pure numpy/CPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def lorenz_series(n: int, dt: float = 0.02, seed: int = 0, sigma=10.0, rho=28.0, beta=8.0 / 3.0):
    """Integrate the Lorenz system with RK4; return an (n, 3) trajectory."""
    rng = np.random.default_rng(seed)
    s = np.array([1.0, 1.0, 1.0]) + 0.01 * rng.standard_normal(3)

    def f(v):
        x, y, z = v
        return np.array([sigma * (y - x), x * (rho - z) - y, x * y - beta * z])

    out = np.empty((n, 3))
    for i in range(n):
        out[i] = s
        k1 = f(s); k2 = f(s + dt / 2 * k1); k3 = f(s + dt / 2 * k2); k4 = f(s + dt * k3)
        s = s + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    return out


@dataclass(frozen=True)
class ESNConfig:
    n_res: int = 400
    spectral_radius: float = 1.1     # edge of stability — long memory without blowing up
    sparsity: float = 0.1            # fraction of nonzero reservoir weights
    leak: float = 0.7                # leaky-integrator rate
    input_scale: float = 0.6
    ridge: float = 1e-6              # readout regularisation
    washout: int = 200               # transient steps discarded before fitting


def build_reservoir(cfg: ESNConfig, n_in: int, seed: int = 0):
    rng = np.random.default_rng(seed)
    W = rng.standard_normal((cfg.n_res, cfg.n_res)) * (rng.random((cfg.n_res, cfg.n_res)) < cfg.sparsity)
    radius = np.max(np.abs(np.linalg.eigvals(W)))
    W = W * (cfg.spectral_radius / radius)            # scale to target spectral radius
    W_in = cfg.input_scale * rng.uniform(-1, 1, (cfg.n_res, n_in))
    return W, W_in


def _update(cfg, W, W_in, r, u):
    return (1 - cfg.leak) * r + cfg.leak * np.tanh(W @ r + W_in @ u)


def harvest(cfg, W, W_in, inputs):
    """Drive the reservoir with the input series; return the collected states (T, n_res)."""
    r = np.zeros(cfg.n_res)
    states = np.empty((len(inputs), cfg.n_res))
    for t, u in enumerate(inputs):
        r = _update(cfg, W, W_in, r, u)
        states[t] = r
    return states


def train_readout(cfg, states, targets):
    """Ridge regression W_out mapping reservoir state -> next-step output (after washout)."""
    X = states[cfg.washout:]
    Y = targets[cfg.washout:]
    A = X.T @ X + cfg.ridge * np.eye(X.shape[1])
    return np.linalg.solve(A, X.T @ Y).T            # (n_out, n_res)


def free_run(cfg, W, W_in, W_out, r0, u0, n_steps):
    """Closed-loop: feed the network's own prediction back as input. Returns generated outputs."""
    r = r0.copy(); u = u0.copy()
    out = np.empty((n_steps, len(u0)))
    for t in range(n_steps):
        r = _update(cfg, W, W_in, r, u)
        u = W_out @ r                                # prediction becomes the next input
        out[t] = u
    return out


def normalize(series):
    mu, sd = series.mean(0), series.std(0)
    return (series - mu) / sd, mu, sd


def fit_and_predict(cfg: ESNConfig, train_len=5000, predict_len=2000, dt=0.02, seed=0):
    """Train an ESN on Lorenz, then free-run it. Returns dict with the true vs generated
    trajectories (denormalised) and the reservoir pieces."""
    data = lorenz_series(train_len + predict_len + 1, dt=dt, seed=seed)
    norm, mu, sd = normalize(data)
    W, W_in = build_reservoir(cfg, 3, seed=seed)
    inp = norm[:train_len]
    tgt = norm[1:train_len + 1]                       # one-step-ahead target
    states = harvest(cfg, W, W_in, inp)
    W_out = train_readout(cfg, states, tgt)
    # warm the reservoir up to the prediction start, then close the loop
    r = states[-1]
    u0 = norm[train_len]
    gen = free_run(cfg, W, W_in, W_out, r, u0, predict_len)
    true = norm[train_len + 1:train_len + 1 + predict_len]
    return {"gen": gen * sd + mu, "true": true * sd + mu, "gen_n": gen, "true_n": true,
            "W": W, "W_in": W_in, "W_out": W_out, "mu": mu, "sd": sd, "dt": dt}


def valid_time(gen_n, true_n, dt, lyap=0.906, thresh=0.4):
    """Lyapunov times until the normalised prediction error first exceeds `thresh` (RMS over dims)."""
    err = np.sqrt(np.mean((gen_n - true_n) ** 2, axis=1))
    norm = np.sqrt(np.mean(true_n ** 2)) + 1e-9
    over = np.where(err / norm > thresh)[0]
    steps = over[0] if len(over) else len(err)
    return steps * dt * lyap                          # in Lyapunov times (Lorenz λ_max ≈ 0.906)
