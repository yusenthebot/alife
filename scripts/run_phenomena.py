"""R40 — the phenomena wall: a montage of the modern rungs (R25 -> R39).

The R23 gallery captured the R1->R22 journey. This poster tiles the figures from
the later rounds — sexual selection, the memory win, the open-endedness trilogy,
evolving morphology, the in-situ living-world capstone and its extensions, and the
game-theory phenomena — into a single wall, assembled from the runs/ artifacts.

Generate the per-round figures first (or reuse existing runs/), then:
  python scripts/run_phenomena.py
Output: runs/r40_phenomena/phenomena.png
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "runs" / "r40_phenomena"

PANELS = [
    ("r25_sexsel/sexsel.png", "R25 · sexual selection (Fisherian runaway)"),
    ("r26_memory/memory.png", "R26 · the memory win (RNN vs reactive)"),
    ("r28_openended/openended.png", "R28 · open-endedness (MAP-Elites QD)"),
    ("r29_navqd/navqd.png", "R29 · open-ended navigation (QD)"),
    ("r30_noveltymaze/noveltymaze.png", "R30 · novelty search beats objective"),
    ("r31_morphevo/morphevo.png", "R31 · evolving morphology (body+gait)"),
    ("r33_ecosim/ecosim.png", "R33 · in-situ foraging evolution (capstone)"),
    ("r34_predeco/predeco.png", "R34 · in-situ predator-prey"),
    ("r35_ecoseasons/ecoseasons.png", "R35 · evolution in a changing world"),
    ("r37_sexevo/sexevo.png", "R37 · evolution of sex (Muller's ratchet)"),
    ("r38_spatialcoop/spatialcoop.png", "R38 · spatial reciprocity (cooperation)"),
    ("r39_rps/rps.png", "R39 · rock-paper-scissors (biodiversity)"),
]

COLS = 3
CELL_W, CELL_H = 640, 500
PAD, LABEL_H = 10, 30
BG = (16, 16, 26)
FG = (235, 235, 245)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    present = [(p, t) for p, t in PANELS if (ROOT / "runs" / p).exists()]
    missing = [p for p, _ in PANELS if not (ROOT / "runs" / p).exists()]
    if missing:
        print(f"WARNING: {len(missing)} panel(s) missing, skipping: {missing}")
    rows = (len(present) + COLS - 1) // COLS
    W = COLS * CELL_W + (COLS + 1) * PAD
    H = rows * (CELL_H + LABEL_H) + (rows + 1) * PAD
    poster = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(poster)
    for i, (rel, title) in enumerate(present):
        r, c = divmod(i, COLS)
        x = PAD + c * (CELL_W + PAD)
        y = PAD + r * (CELL_H + LABEL_H + PAD)
        img = Image.open(ROOT / "runs" / rel).convert("RGB")
        img.thumbnail((CELL_W, CELL_H))
        ox = x + (CELL_W - img.width) // 2
        poster.paste(img, (ox, y + LABEL_H))
        draw.text((x + 4, y + 8), title, fill=FG)
    path = OUT / "phenomena.png"
    poster.save(path)
    print(f"tiled {len(present)} panels -> {path}  ({W}x{H})")


if __name__ == "__main__":
    main()
