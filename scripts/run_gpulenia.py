"""R60 — Lenia: continuous-CA "creatures" on the GPU.

From smooth random soup, a ring-kernel + bell-growth rule self-organises into soft,
life-like blobs that persist and move — Lenia, run at scale on the GPU substrate.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from alife.gpulenia import LeniaConfig, run  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "r60_gpulenia"


def _show(a, fld, title):
    a.imshow(fld, cmap="magma", interpolation="bilinear", vmin=0, vmax=1)
    a.set_title(title); a.set_xticks([]); a.set_yticks([])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = LeniaConfig(size=512)
    r = run(cfg, steps=500, seed=1, record_every=60)
    snaps = r["snaps"]; keys = sorted(snaps)
    m = r["mass"]
    print(f"Lenia 512^2 mu={cfg.mu} sigma={cfg.sigma}: {int(r['steps_per_s'])} steps/s")
    print(f"mass fraction {m[0,1]/(cfg.size**2):.3f} -> {m[-1,1]/(cfg.size**2):.3f}; std {m[0,2]:.2f} -> {m[-1,2]:.2f}")

    fig, ax = plt.subplots(2, 2, figsize=(12.5, 12.5))
    fig.suptitle("R60 — Lenia: continuous-CA creatures self-organize on the GPU",
                 fontsize=14, fontweight="bold")
    _show(ax[0, 0], snaps[keys[0]], f"t={keys[0]}: smooth random soup")
    _show(ax[0, 1], snaps[keys[len(keys) // 3]], f"t={keys[len(keys)//3]}: structures condense")
    _show(ax[1, 0], snaps[keys[-1]], f"t={keys[-1]}: persistent Lenia creatures")
    a = ax[1, 1]
    a.plot(m[:, 0], m[:, 1] / (cfg.size ** 2), color="#1d9bf0", lw=2, label="mass fraction")
    a.plot(m[:, 0], m[:, 2], color="#e0245e", lw=2, label="structure (std)")
    a.set_title("Self-organization: mass settles, structure persists")
    a.set_xlabel("step"); a.set_ylabel("value"); a.legend(fontsize=9); a.set_ylim(0, None)

    fig.tight_layout()
    path = OUT / "gpulenia.png"
    fig.savefig(path, dpi=110)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
