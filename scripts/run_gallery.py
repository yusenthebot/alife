#!/usr/bin/env python
"""Round 23 — the gallery: the whole evolutionary journey in one poster.

Tiles the headline frame from every rung (R1 -> R22) into a single labelled
montage, assembled from the runs/ artifacts of the standard demo names.

Generate the inputs first (or reuse existing runs/), then:
  python scripts/run_gallery.py --name gallery
Output: runs/<name>/gallery.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
PANELS = [
    ("r1_demo/frame_end.png", "R1 · flocking emerges (phi 0.08->0.92)"),
    ("r2_evo/traits.png", "R2 · natural selection (trait trajectories)"),
    ("r3_evolve/behavior.png", "R3 · evolved NN foraging brains"),
    ("r4_coevo/coevo_start.png", "R4 · predator-prey co-evolution"),
    ("r5_predprey/populations.png", "R5 · predator-prey ecology"),
    ("r7_flock3d/flock3d_end.png", "R7 · 3D flocking (GPU)"),
    ("r8_evolve3d/eco3d_mid.png", "R8 · evolution in 3D"),
    ("r9_coevo3d/hunt3d_start.png", "R9 · predator-prey in 3D"),
    ("r11_world3d/world3d_mid.png", "R11 · atmospheric living world"),
    ("r13_swarm3d/swarm3d_mid.png", "R13 · vast swarm (12k agents)"),
    ("r14_bigworld/bigworld_mid.png", "R14 · large-scale world (10k)"),
    ("r15_cycles/cycles.png", "R15 · sustained pred-prey cycles"),
    ("r16_speciation/speciation.png", "R16 · speciation (1 -> 2 species)"),
    ("r17_signals/signals.png", "R17 · evolved communication"),
    ("r18_evolvability/evolvability.png", "R18 · evolution of evolvability"),
    ("r19_cooperation/cooperation.png", "R19 · cooperation (Hamilton)"),
    ("r20_aging/aging.png", "R20 · evolution of aging"),
    ("r21_multicell/multicell.png", "R21 · multicellularity (transition)"),
    ("r22_redqueen/redqueen.png", "R22 · Red Queen coevolution"),
]
TILE_W, TILE_H, LABEL_H, PAD, COLS = 480, 300, 26, 6, 4
BG = (10, 12, 20)


def fit(img: Image.Image, w: int, h: int) -> Image.Image:
    img = img.convert("RGB")
    img.thumbnail((w, h), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), BG)
    canvas.paste(img, ((w - img.width) // 2, (h - img.height) // 2))
    return canvas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", type=str, default="gallery")
    args = ap.parse_args()
    out = ROOT / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)

    rows = (len(PANELS) + COLS - 1) // COLS
    cell_w, cell_h = TILE_W + 2 * PAD, TILE_H + LABEL_H + 2 * PAD
    title_h = 70
    W, H = COLS * cell_w, title_h + rows * cell_h
    poster = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(poster)
    draw.text((PAD * 2, 20), "alife - an evolving artificial-life ecosystem  ·  R1 -> R22  ·  the journey",
              fill=(235, 240, 255))

    for i, (rel, label) in enumerate(PANELS):
        r, c = divmod(i, COLS)
        x0, y0 = c * cell_w + PAD, title_h + r * cell_h + PAD
        p = ROOT / "runs" / rel
        if p.exists():
            poster.paste(fit(Image.open(p), TILE_W, TILE_H), (x0, y0))
        else:
            draw.rectangle([x0, y0, x0 + TILE_W, y0 + TILE_H], outline=(60, 60, 70))
        draw.text((x0 + 2, y0 + TILE_H + 5), label, fill=(200, 210, 230))

    poster.save(out / "gallery.png")
    print(f"gallery: {len(PANELS)} panels, {W}x{H} -> {out/'gallery.png'}")


if __name__ == "__main__":
    main()
