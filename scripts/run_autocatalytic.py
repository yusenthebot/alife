"""R62 — Autocatalytic sets (RAF): self-sustaining chemistry appears at a phase transition.

Binary-polymer reaction network; `f` = mean reactions catalysed per molecule. As f rises,
a giant Reflexively-Autocatalytic Food-generated set appears suddenly — the spontaneous
birth of a self-making, self-catalysing chemistry from inert food, with no replicator
built in (Kauffman; Hordijk & Steel).
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.autocatalytic import (  # noqa: E402
    RAFConfig, build_polymer_model, phase_transition, random_catalysis,
    max_raf, production_closure,
)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r62_autocatalytic"


def _layered_positions(active, reactions, food, mols_in):
    """Place molecules in generation layers (food=0), reactions between their reactants & product."""
    gen = {m: 0 for m in food if m in mols_in}
    changed = True
    while changed:
        changed = False
        for ri in active:
            a, b, prod = reactions[ri]
            if a in gen and b in gen and prod not in gen:
                gen[prod] = max(gen[a], gen[b]) + 1
                changed = True
    for m in mols_in:                       # any stragglers
        gen.setdefault(m, max(gen.values()) + 1 if gen else 0)
    layers = {}
    for m, g in gen.items():
        layers.setdefault(g, []).append(m)
    mpos = {}
    for g, ms in layers.items():
        for k, m in enumerate(sorted(ms)):
            mpos[m] = (g * 2.0, (k - (len(ms) - 1) / 2) * 1.6)
    return mpos


def _draw_network(ax, active, reactions, catalysts, food, mols):
    W = production_closure(reactions, food, active)
    mpos = _layered_positions(active, reactions, food, W)
    # reactions
    for ri in active:
        a, b, prod = reactions[ri]
        rx = (mpos[a][0] + mpos[b][0] + mpos[prod][0]) / 3 + 1.0
        ry = (mpos[a][1] + mpos[b][1] + mpos[prod][1]) / 3
        for src in (a, b):
            ax.annotate("", xy=(rx, ry), xytext=mpos[src],
                        arrowprops=dict(arrowstyle="-", color="#9aa0a6", lw=1.0, alpha=0.7))
        ax.annotate("", xy=mpos[prod], xytext=(rx, ry),
                    arrowprops=dict(arrowstyle="-|>", color="#1d9bf0", lw=1.4))
        cat = next((c for c in catalysts[ri] if c in W), None)
        if cat is not None:
            ax.annotate("", xy=(rx, ry), xytext=mpos[cat],
                        arrowprops=dict(arrowstyle="-|>", color="#e0245e", lw=1.0,
                                        ls=(0, (3, 3)), alpha=0.8))
        ax.scatter([rx], [ry], s=22, c="#5f6368", marker="s", zorder=3)
    for m, (x, y) in mpos.items():
        is_food = m in food
        ax.scatter([x], [y], s=560, c="#0d7d27" if is_food else "#f2c200",
                   edgecolors="white", linewidths=1.2, zorder=4)
        ax.text(x, y, mols[m], ha="center", va="center", fontsize=7,
                color="white" if is_food else "black", zorder=5, fontweight="bold")
    ax.set_title(f"a real RAF: {len(active)} reactions close on themselves\n"
                 "green=food  yellow=produced  blue→=production  red⇢=catalysis", fontsize=10)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_facecolor("#0a0a0f")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # 1) phase transition for L=7
    cfg = RAFConfig(max_len=7, food_len=2)
    fs = np.linspace(0, 4.5, 19)
    f, prob, size, dims = phase_transition(cfg, fs, trials=60, seed=1)
    nm, nr = dims
    print(f"L=7: {nm} molecules, {nr} reactions, 6 food")
    print(f"P(RAF) {prob[0]:.2f}->{prob[-1]:.2f}; giant maxRAF size {size[0]:.0f}->{size[-1]:.0f} "
          f"({100*size[-1]/nr:.0f}% of all reactions)")

    # 2) size scaling: how the threshold moves as the molecule set grows exponentially
    scaling = []
    for L in (5, 6, 7):
        c = RAFConfig(max_len=L, food_len=2)
        m2, _, r2, _ = build_polymer_model(c)
        ff, pp, _, _ = phase_transition(c, np.linspace(0, 4.5, 19), trials=60, seed=2)
        fstar = next((a for a, b in zip(ff, pp) if b >= 0.5), float("nan"))
        scaling.append((L, len(m2), ff, pp, fstar))
        print(f"L={L}: {len(m2)} molecules, P(RAF)>=0.5 at f~{fstar:.2f}")

    # 3) a concrete drawable RAF
    cfgd = RAFConfig(max_len=6, food_len=2)
    md, _, rd, fdd = build_polymer_model(cfgd)
    raf = None
    for s in range(60):
        rng = np.random.default_rng(s)
        cat = random_catalysis(len(rd), len(md), 2.7, rng)
        a, _ = max_raf(rd, fdd, cat)
        if 8 <= len(a) <= 20:
            raf = (a, cat); break

    fig = plt.figure(figsize=(16.5, 11))
    fig.suptitle("R62 — Autocatalytic sets (RAF): self-sustaining chemistry at a phase transition",
                 fontsize=14, fontweight="bold")
    ax1 = fig.add_subplot(2, 2, 1)
    ax1.plot(f, prob, "o-", color="#1d9bf0", lw=2)
    ax1.axhline(0.5, color="#9aa0a6", ls=":", lw=1)
    ax1.set_title("P(an autocatalytic set exists) vs catalysis level f")
    ax1.set_xlabel("f  (mean reactions catalysed per molecule)"); ax1.set_ylabel("P(RAF)")
    ax1.set_ylim(-0.03, 1.03); ax1.grid(alpha=0.25)

    ax2 = fig.add_subplot(2, 2, 2)
    ax2.plot(f, size, "o-", color="#e0245e", lw=2)
    ax2.set_title(f"Giant RAF emerges suddenly (size = # reactions, of {nr})")
    ax2.set_xlabel("f"); ax2.set_ylabel("maxRAF size when it exists"); ax2.grid(alpha=0.25)

    ax3 = fig.add_subplot(2, 2, 3)
    for L, nmol, ff, pp, fstar in scaling:
        ax3.plot(ff, pp, "o-", lw=1.8, label=f"L={L}  ({nmol} molecules)  f*≈{fstar:.1f}")
    ax3.set_title("Scaling: molecular diversity grows EXPONENTIALLY,\nthe needed catalysis f* only modestly")
    ax3.set_xlabel("f"); ax3.set_ylabel("P(RAF)"); ax3.legend(fontsize=8); ax3.grid(alpha=0.25)

    ax4 = fig.add_subplot(2, 2, 4)
    if raf is not None:
        _draw_network(ax4, raf[0], rd, raf[1], fdd, md)
    else:
        ax4.text(0.5, 0.5, "no mid-size RAF found", ha="center")
    fig.tight_layout()
    path = OUT / "autocatalytic.png"
    fig.savefig(path, dpi=108, facecolor="white")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
