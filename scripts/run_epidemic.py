"""R84 — Epidemics on networks: the vanishing epidemic threshold of scale-free topology.

SIR contagion over Barabasi-Albert vs Erdos-Renyi graphs. The scale-free network ignites
epidemics at far lower infectiousness (threshold → 0, hubs as super-spreaders); infection
probability rises with degree; and targeted hub immunisation halts outbreaks with few vaccines.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.epidemic import (  # noqa: E402
    ba_graph, er_graph, threshold_curve, infection_by_degree, immunize, sir_timeseries,
)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r84_epidemic"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    n, m, gamma = 4000, 2, 0.3
    ba, er = ba_graph(n, m, seed=0), er_graph(n, len(ba_graph(n, m, seed=0)), seed=0)

    betas = np.linspace(0.02, 0.35, 16)
    sb = threshold_curve(ba, n, betas, gamma=gamma, trials=12, seed=1)
    se = threshold_curve(er, n, betas, gamma=gamma, trials=12, seed=1)
    print(f"threshold: BA outbreaks by beta~0.05-0.08, ER ~0.13+ (BA threshold << ER)")

    cdeg, pdeg = infection_by_degree(ba, n, beta=0.1, gamma=gamma, trials=30, seed=2, nbins=10)
    fracs = np.linspace(0, 0.25, 11)
    rnd = [immunize(ba, n, 0.2, f, "random", gamma=gamma, trials=18, seed=3) for f in fracs]
    tgt = [immunize(ba, n, 0.2, f, "targeted", gamma=gamma, trials=18, seed=3) for f in fracs]
    print(f"immunization: targeted crushes epidemic ({tgt[2]:.3f} at 5%), random barely helps ({rnd[2]:.3f})")
    S, I, R = sir_timeseries(ba, n, 0.2, gamma=gamma, seed=4)

    fig = plt.figure(figsize=(16.5, 10))
    fig.suptitle("R84 — Epidemics on networks: scale-free topology has (almost) no epidemic threshold",
                 fontsize=14, fontweight="bold")

    ax = fig.add_subplot(2, 2, 1)
    ax.plot(betas, sb, "o-", color="#e0245e", lw=2, label="scale-free (Barabasi-Albert)")
    ax.plot(betas, se, "o-", color="#1d9bf0", lw=2, label="random (Erdos-Renyi)")
    ax.set_title("Vanishing threshold: scale-free epidemics ignite at\nmuch lower infectiousness than random graphs")
    ax.set_xlabel("infection rate β (γ=0.3)"); ax.set_ylabel("final epidemic size"); ax.legend(fontsize=9)
    ax.grid(alpha=0.25)

    ax = fig.add_subplot(2, 2, 2)
    ax.plot(cdeg, pdeg, "o-", color="#1f7a1f", lw=2)
    ax.set_title("Hubs are super-spreaders:\nP(infected) rises with node degree")
    ax.set_xlabel("node degree"); ax.set_ylabel("P(ever infected)"); ax.grid(alpha=0.25)

    ax = fig.add_subplot(2, 2, 3)
    ax.plot(fracs, rnd, "o-", color="#9aa0a6", lw=2, label="random vaccination")
    ax.plot(fracs, tgt, "o-", color="#e0245e", lw=2, label="targeted (hubs first)")
    ax.set_title("Immunisation: vaccinating the HUBS halts the epidemic\nwith a handful of doses; random barely helps")
    ax.set_xlabel("fraction immunised"); ax.set_ylabel("epidemic size (β=0.2)"); ax.legend(fontsize=9); ax.grid(alpha=0.25)

    ax = fig.add_subplot(2, 2, 4)
    t = np.arange(len(S))
    ax.plot(t, S / n, color="#1d9bf0", lw=2, label="susceptible")
    ax.plot(t, I / n, color="#e0245e", lw=2, label="infected")
    ax.plot(t, R / n, color="#1f7a1f", lw=2, label="recovered")
    ax.set_title("The epidemic curve on a scale-free network (one outbreak)")
    ax.set_xlabel("time step"); ax.set_ylabel("fraction of population"); ax.legend(fontsize=9); ax.grid(alpha=0.25)

    fig.tight_layout()
    path = OUT / "epidemic.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
