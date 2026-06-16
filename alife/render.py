"""Headless renderer: turn swarm state into RGB frames with motion trails.

Pure numpy + Pillow so it runs without a display (the loop renders offscreen
and reads the PNGs back). Boids are drawn as triangles pointing along their
heading and colored by heading angle, so aligned flocks fade to one hue — the
emergence of order is legible at a glance, not just in the metrics.
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from .world import World


def _hsv_to_rgb(h: np.ndarray, s: float, v: float) -> np.ndarray:
    """Vectorized HSV→RGB for an array of hues in [0,1). Returns (N,3) uint8."""
    i = np.floor(h * 6.0).astype(int)
    f = h * 6.0 - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6
    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])
    return (np.stack([r, g, b], axis=1) * 255).astype(np.uint8)


class Renderer:
    def __init__(
        self,
        world: World,
        resolution: int = 900,
        bg: tuple[int, int, int] = (7, 9, 18),
        trail: float = 0.80,
        boid_size: float = 3.2,
    ) -> None:
        self.world = world
        self.scale = resolution / max(world.width, world.height)
        self.w = int(round(world.width * self.scale))
        self.h = int(round(world.height * self.scale))
        self.bg = np.array(bg, dtype=float)
        self.trail = trail
        self.size = boid_size
        self.buf = np.ones((self.h, self.w, 3), dtype=float) * self.bg

    def frame(self, pos: np.ndarray, vel: np.ndarray) -> np.ndarray:
        """Render one frame. Fades the previous buffer to leave comet trails."""
        # Fade toward background (not black) so trails dissolve naturally.
        self.buf = self.buf * self.trail + self.bg * (1.0 - self.trail)
        img = Image.fromarray(self.buf.astype(np.uint8))
        draw = ImageDraw.Draw(img)

        c = pos * self.scale
        speed = np.maximum(np.linalg.norm(vel, axis=1, keepdims=True), 1e-9)
        head = vel / speed
        perp = np.stack([-head[:, 1], head[:, 0]], axis=1)
        s = self.size
        tip = c + head * (s * 1.9)
        back = c - head * (s * 1.0)
        left = back + perp * (s * 0.85)
        right = back - perp * (s * 0.85)

        hue = (np.arctan2(head[:, 1], head[:, 0]) / (2 * np.pi)) % 1.0
        colors = _hsv_to_rgb(hue, s=0.85, v=1.0)

        for k in range(pos.shape[0]):
            draw.polygon(
                [tuple(tip[k]), tuple(left[k]), tuple(right[k])],
                fill=tuple(int(x) for x in colors[k]),
            )

        self.buf = np.asarray(img, dtype=float)
        return self.buf.astype(np.uint8)

    def two_species_frame(self, prey_pos, prey_vel, pred_pos, pred_vel, food) -> np.ndarray:
        """Predator–prey frame: food (green motes), prey (cyan), predators (red,
        larger). Heading-oriented triangles with motion trails."""
        self.buf = self.buf * self.trail + self.bg * (1.0 - self.trail)
        img = Image.fromarray(self.buf.astype(np.uint8))
        draw = ImageDraw.Draw(img)
        if food.shape[0]:
            fc = food * self.scale
            r = max(1.0, self.size * 0.4)
            for k in range(food.shape[0]):
                x, y = float(fc[k, 0]), float(fc[k, 1])
                draw.ellipse([x - r, y - r, x + r, y + r], fill=(35, 110, 50))
        self._draw_agents(draw, prey_pos, prey_vel, (90, 220, 235), self.size)
        self._draw_agents(draw, pred_pos, pred_vel, (240, 60, 60), self.size * 1.7)
        self.buf = np.asarray(img, dtype=float)
        return self.buf.astype(np.uint8)

    def _draw_agents(self, draw, pos, vel, color, size) -> None:
        if pos.shape[0] == 0:
            return
        c = pos * self.scale
        sp = np.maximum(np.linalg.norm(vel, axis=1, keepdims=True), 1e-9)
        head = vel / sp
        perp = np.stack([-head[:, 1], head[:, 0]], axis=1)
        tip = c + head * (size * 1.9)
        back = c - head * (size * 1.0)
        left = back + perp * (size * 0.85)
        right = back - perp * (size * 0.85)
        for k in range(pos.shape[0]):
            draw.polygon([tuple(tip[k]), tuple(left[k]), tuple(right[k])], fill=color)

    def eco_frame(self, pos: np.ndarray, vel: np.ndarray, hue: np.ndarray, food: np.ndarray) -> np.ndarray:
        """Ecosystem frame: food as soft green motes, creatures as triangles whose
        hue encodes a heritable trait — so watching the color mix shift *is*
        watching selection. `hue` is per-creature in [0, 1)."""
        self.buf = self.buf * self.trail + self.bg * (1.0 - self.trail)
        img = Image.fromarray(self.buf.astype(np.uint8))
        draw = ImageDraw.Draw(img)

        if food.shape[0]:
            fc = food * self.scale
            r = max(1.0, self.size * 0.45)
            for k in range(food.shape[0]):
                x, y = float(fc[k, 0]), float(fc[k, 1])
                draw.ellipse([x - r, y - r, x + r, y + r], fill=(40, 120, 55))

        if pos.shape[0]:
            c = pos * self.scale
            speed = np.maximum(np.linalg.norm(vel, axis=1, keepdims=True), 1e-9)
            head = vel / speed
            perp = np.stack([-head[:, 1], head[:, 0]], axis=1)
            s = self.size
            tip = c + head * (s * 1.9)
            back = c - head * (s * 1.0)
            left = back + perp * (s * 0.85)
            right = back - perp * (s * 0.85)
            colors = _hsv_to_rgb(np.clip(hue, 0.0, 0.9999), s=0.9, v=1.0)
            for k in range(pos.shape[0]):
                draw.polygon(
                    [tuple(tip[k]), tuple(left[k]), tuple(right[k])],
                    fill=tuple(int(x) for x in colors[k]),
                )

        self.buf = np.asarray(img, dtype=float)
        return self.buf.astype(np.uint8)
