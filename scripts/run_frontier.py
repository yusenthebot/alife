"""R58 — the frontier gallery: Digital Genesis + the GPU substrate (R51-R57).

Tiles the headline figures of the project's two newest frontiers — the Avida-style
evolution of self-replicating programs, and the million-scale GPU substrate
(morphogenesis, slime mould, flocking, evolution) — into one poster, complementing
the R23 (R1-R22) and R40 (R25-R46) galleries.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "runs" / "r58_frontier"

PANELS = [
    ("r51_digavida/digavida.png", "R51 · Digital Genesis: self-replicating programs"),
    ("r52_digtasks/digtasks.png", "R52 · computation evolves (it pays)"),
    ("r53_digphylo/digphylo.png", "R53 · the digital tree of life (coalescence)"),
    ("r54_gpurd/gpurd.png", "R54 · GPU substrate: 1M-cell morphogenesis"),
    ("r55_gpuslime/gpuslime.png", "R55 · GPU Physarum: 1M slime-mold agents"),
    ("r56_gpuboids/gpuboids.png", "R56 · a million boids (GPU Vicsek)"),
    ("r57_gpuevo/gpuevo.png", "R57 · natural selection at a million genomes"),
]

COLS = 2
CELL_W, CELL_H = 760, 600
PAD, LABEL_H = 12, 34
BG, FG = (14, 14, 22), (235, 235, 245)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    present = [(p, t) for p, t in PANELS if (ROOT / "runs" / p).exists()]
    missing = [p for p, _ in PANELS if not (ROOT / "runs" / p).exists()]
    if missing:
        print(f"WARNING missing: {missing}")
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
        poster.paste(img, (x + (CELL_W - img.width) // 2, y + LABEL_H))
        draw.text((x + 4, y + 9), title, fill=FG)
    path = OUT / "frontier.png"
    poster.save(path)
    print(f"tiled {len(present)} panels -> {path}  ({W}x{H})")


if __name__ == "__main__":
    main()
