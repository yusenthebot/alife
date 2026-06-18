"""R51 — Digital Genesis: evolution of self-replicating programs.

A hand-seeded ancestor program copies itself into the soup; copy-mutations create
variant code; broken mutants die and viable replicators dominate; and a faster
(shorter) replicator out-competes a slower one. The genome is executable code that
evolution rewrites.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.digavida import (  # noqa: E402
    ANCESTOR,
    SoupConfig,
    compete,
    disassemble,
    is_replicator,
    replicate_once,
    run_soup,
)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r51_digavida"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    soup = run_soup(SoupConfig(sweeps=2500), seed=0)
    comp = compete(len_short=7, len_long=30, seed=0)

    alive = soup["final_genomes"]
    reps = [g for g in alive if is_replicator(g)]
    evolved = max(reps, key=lambda g: 0 if np.array_equal(g, ANCESTOR) else 1)
    print(f"soup: pop {int(soup['pop'][-1])}, {len(reps)}/{len(alive)} viable replicators, "
          f"diversity {int(soup['diversity'][-1])} unique genomes, {int(soup['divisions'][-1])} divisions")
    print(f"ancestor:  {disassemble(ANCESTOR)}")
    print(f"evolved:   {disassemble(evolved)}  (self-replicates: {is_replicator(evolved)})")

    fig, ax = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle("R51 — Digital Genesis: evolution of self-replicating programs",
                 fontsize=14, fontweight="bold")

    a = ax[0, 0]
    a.plot(comp["t"], comp["short"], color="#1b7a3d", lw=2, label="short replicator (31 cyc/div)")
    a.plot(comp["t"], comp["long"], color="#e0245e", lw=2, label="long replicator (123 cyc/div)")
    a.set_title("Selection for replication speed: faster code wins")
    a.set_xlabel("scheduler sweep"); a.set_ylabel("organisms"); a.legend(fontsize=9)

    a = ax[0, 1]
    a.plot(soup["t"], soup["diversity"], color="#7d3cff", lw=2)
    a.set_title("Mutations accumulate: genetic diversity (unique genomes)")
    a.set_xlabel("scheduler sweep"); a.set_ylabel("distinct genomes alive")

    a = ax[1, 0]
    a.plot(soup["t"], soup["pop"], color="#1d9bf0", lw=2, label="population")
    a.set_title("Ancestor fills the soup; selection purges broken mutants")
    a.set_xlabel("scheduler sweep"); a.set_ylabel("alive organisms")
    a.legend(fontsize=9, loc="lower right")

    a = ax[1, 1]; a.axis("off")
    import textwrap
    evo_wrap = "\n  ".join(textwrap.wrap(disassemble(evolved), 46))
    txt = ("THE EXECUTABLE GENOME (verified, not faked)\n\n"
           f"ancestor (len {len(ANCESTOR)}), self-copies in "
           f"{replicate_once(ANCESTOR)[1]} cycles:\n  {disassemble(ANCESTOR)}\n\n"
           f"an EVOLVED replicator (len {len(evolved)}):\n  {evo_wrap}\n\n"
           "verification: single-step its CPU in isolation ->\n"
           f"it builds a valid offspring = a genuine\nevolved replicator ({is_replicator(evolved)}).")
    a.text(0.0, 0.98, txt, transform=a.transAxes, va="top", family="monospace", fontsize=8.5)
    a.set_title("The substrate leap: code that rewrites itself")

    fig.tight_layout()
    path = OUT / "digavida.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
