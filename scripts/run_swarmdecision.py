"""R75 — Swarm cognition: how a honeybee colony decides (cross-inhibition consensus).

Scout bees pick the best nest site with no leader and no bee comparing options. Recruitment
(quality-weighted waggle dancing) plus a cross-inhibition stop-signal turns the swarm into a
decision-maker: it locks onto the better site, and — crucially — breaks the deadlock between two
equal sites into a decisive consensus, which recruitment alone cannot do.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.swarmdecision import SwarmConfig, simulate  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r75_swarmdecision"
COLORS = ["#1d9bf0", "#e0245e", "#1f7a1f"]


def _series(ax, r, title, steps_dt=1.0):
    f = r["frac"]
    t = np.arange(len(f))
    for i in range(r["n"]):
        ax.plot(t, f[:, i], color=COLORS[i % 3], lw=2, label=f"site {i} (v={r['v'][i]:g})")
    ax.plot(t, r["uncommitted"], color="#9aa0a6", lw=1.2, ls=":", label="uncommitted")
    ax.set_title(title, fontsize=10); ax.set_xlabel("time"); ax.set_ylabel("fraction of swarm")
    ax.set_ylim(0, 1.02); ax.legend(fontsize=8)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = SwarmConfig()

    val = simulate([1.5, 1.0], cfg, steps=600, seed=0)
    eq_ci = simulate([1.2, 1.2], cfg, steps=600, seed=1, cross_inhibition=True)
    eq_no = simulate([1.2, 1.2], cfg, steps=600, seed=1, cross_inhibition=False)
    print(f"value-sensitive [1.5,1.0]: final {val['frac'][-1].round(2)} (best=site0)")
    print(f"equal +CI: final {eq_ci['frac'][-1].round(2)} (decisive)")
    print(f"equal noCI: final {eq_no['frac'][-1].round(2)} (split)")

    # loser-suppression statistics across seeds
    def stats(ci):
        losers = []
        for s in range(20):
            r = simulate([1.2, 1.2], cfg, steps=700, seed=s, cross_inhibition=ci)
            losers.append(np.sort(r["frac"][-1])[-2])
        return np.mean(losers)
    loser_ci, loser_no = stats(True), stats(False)
    print(f"mean loser fraction: CI {loser_ci:.2f} vs noCI {loser_no:.2f}")

    fig = plt.figure(figsize=(16.5, 10))
    fig.suptitle("R75 — Swarm cognition: a honeybee colony decides by recruitment + cross-inhibition",
                 fontsize=14, fontweight="bold")

    _series(fig.add_subplot(2, 2, 1), val,
            "Value-sensitive: the swarm locks onto the BETTER site")
    _series(fig.add_subplot(2, 2, 2), eq_ci,
            "Two EQUAL sites + cross-inhibition:\nsymmetry breaks → decisive consensus")
    _series(fig.add_subplot(2, 2, 3), eq_no,
            "Two EQUAL sites, NO cross-inhibition:\nswarm stays split — deadlock, no decision")

    ax = fig.add_subplot(2, 2, 4)
    x = np.arange(2)
    ax.bar(x - 0.18, [1 - loser_ci, 1 - loser_no], 0.36, color="#1f7a1f", label="winner")
    ax.bar(x + 0.18, [loser_ci, loser_no], 0.36, color="#e0245e", label="loser (rival)")
    ax.set_xticks(x); ax.set_xticklabels(["with\ncross-inhibition", "without\n(recruitment only)"])
    ax.set_title("Equal sites (20 seeds): cross-inhibition suppresses the rival\n→ consensus; without it the swarm stays divided")
    ax.set_ylabel("final committed fraction"); ax.legend(fontsize=8); ax.set_ylim(0, 1.05)

    fig.tight_layout()
    path = OUT / "swarmdecision.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
