"""R52 — Digital Genesis Stage 2: computation evolves because it pays.

A hand-written NAND computer out-reproduces an equal-length pure copier purely via
the merit (extra CPU cycles) its computation earns; and from a soup of pure copiers,
NAND computation arises de novo by mutation (though it stays fragile in this minimal
VM — full task-ladder fixation is the EQU round to come).
"""

from __future__ import annotations

import pathlib
import sys
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.digavida import is_replicator  # noqa: E402
from alife.digtasks import (  # noqa: E402
    TASK_DOER,
    compete_compute,
    disasm_t,
    does_task,
    pure_copier,
    run_denovo,
)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r52_digtasks"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    comp = compete_compute(seed=0)
    den = run_denovo(sweeps=8000, mut=0.04, seed=0)

    print(f"task-doer: {disasm_t(TASK_DOER)} | replicates={is_replicator(TASK_DOER)} | "
          f"tasks={sorted(does_task(TASK_DOER))}")
    tot = comp["computers"][-1] + comp["copiers"][-1]
    print(f"competition: computer share {comp['computers'][-1]/tot:.0%}")
    print(f"de-novo task discoveries: {den['cum_tasks']}")

    fig, ax = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle("R52 — Digital Genesis: computation evolves because it pays",
                 fontsize=14, fontweight="bold")

    a = ax[0, 0]
    a.plot(comp["t"], comp["computers"], color="#1b7a3d", lw=2, label="NAND computer (merit ×2)")
    a.plot(comp["t"], comp["copiers"], color="#e0245e", lw=2, label="pure copier (same length)")
    a.set_title("Computation PAYS: the computer out-reproduces the copier")
    a.set_xlabel("scheduler sweep"); a.set_ylabel("organisms"); a.legend(fontsize=9)

    a = ax[0, 1]
    a.plot(den["t"], den["task_frac"], color="#7d3cff", lw=1.5)
    a.set_title("De-novo: NAND computation arises by mutation (fragile, doesn't sweep)")
    a.set_xlabel("scheduler sweep"); a.set_ylabel("fraction of pop computing")

    a = ax[1, 0]
    names = list(den["cum_tasks"].keys()) or ["(none)"]
    vals = [den["cum_tasks"].get(k, 0) for k in names]
    a.bar(names, vals, color="#1d9bf0")
    a.set_title("De-novo task discoveries over the run (from pure copiers)")
    a.set_ylabel("independent discoveries")

    a = ax[1, 1]; a.axis("off")
    txt = ("THE COMPUTING GENOME (verified)\n\n"
           "hand-written NAND computer:\n  "
           + "\n  ".join(textwrap.wrap(disasm_t(TASK_DOER), 46)) + "\n\n"
           f"  self-replicates: {is_replicator(TASK_DOER)}\n"
           f"  performs task: {sorted(does_task(TASK_DOER))}\n\n"
           "engine: a logic task multiplies MERIT, merit buys CPU\n"
           "cycles, so computing replicators reproduce faster.\n"
           "Selection — not design — favors computation.\n\n"
           "honest: de-novo NAND emerges but stays fragile here;\n"
           "the full ladder to EQU needs the larger Avida regime\n"
           "(next rounds).")
    a.text(0.0, 0.98, txt, transform=a.transAxes, va="top", family="monospace", fontsize=8.5)
    a.set_title("Computation that earns its keep")

    fig.tight_layout()
    path = OUT / "digtasks.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
