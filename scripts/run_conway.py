"""R46 — Conway's Game of Life: the Gosper glider gun and random soup.

Shows the gun emitting an endless stream of gliders (unbounded growth) and a
random soup decaying into a stable 'ash' of still lifes and oscillators.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.conway import glider_gun, random_soup, run  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r46_conway"
CMAP = mcolors.ListedColormap(["#0b0b16", "#39d353"])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    gun = run(glider_gun((120, 120)), 240, record_every=60)
    soup = run(random_soup((140, 140), 0.30, seed=0), 320, record_every=80)

    print(f"gun population {gun['population'][0]} -> {gun['population'][-1]} (emitting gliders)")
    print(f"soup population {soup['population'][0]} -> {soup['population'][-1]} (decayed to ash)")

    fig, ax = plt.subplots(2, 2, figsize=(13, 12))
    fig.suptitle("R46 — Conway's Game of Life: complexity from three rules",
                 fontsize=14, fontweight="bold")

    a = ax[0, 0]
    a.plot(gun["population"], color="#39d353", lw=2)
    a.set_title("Gosper gun: unbounded growth (a glider every 30 gens)")
    a.set_xlabel("generation"); a.set_ylabel("live cells")

    a = ax[0, 1]
    a.imshow(gun["final"], cmap=CMAP, interpolation="nearest")
    a.set_title("The gun and its diagonal stream of gliders")
    a.set_xticks([]); a.set_yticks([])

    a = ax[1, 0]
    a.plot(soup["population"], color="#39d353", lw=2)
    a.set_title("Random soup: decays to a stable ash")
    a.set_xlabel("generation"); a.set_ylabel("live cells")

    a = ax[1, 1]
    a.imshow(soup["final"], cmap=CMAP, interpolation="nearest")
    a.set_title("The ash: still lifes, blinkers, the odd glider")
    a.set_xticks([]); a.set_yticks([])

    fig.tight_layout()
    path = OUT / "conway.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
