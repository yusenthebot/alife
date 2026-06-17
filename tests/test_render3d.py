"""GPU 3D renderer smoke test. Skips gracefully if no GL context is available
(e.g. a headless CI box without a GPU), since the rest of the suite is pure CPU.
"""

from __future__ import annotations

import numpy as np
import pytest

from alife.world3d import World3D


def _renderer(world):
    try:
        from alife.render3d import Renderer3D
        return Renderer3D(world, width=320, height=240)
    except Exception as e:  # noqa: BLE001 - GL/EGL unavailable
        pytest.skip(f"no GL context: {e}")


def test_render_produces_frame_with_agents():
    world = World3D(size=80.0)
    r = _renderer(world)
    rng = np.random.default_rng(0)
    pos = rng.uniform(20, 60, size=(120, 3))
    vel = rng.normal(size=(120, 3))
    color = np.tile([1.0, 0.3, 0.3], (120, 1))
    frame = r.render(pos, vel, color, cam_angle=0.5)
    assert frame.shape == (240, 320, 3)
    assert frame.dtype == np.uint8
    # agents (reddish) should add bright pixels above the dark background
    assert frame.max() > 120, "expected rendered agents to be visible"
    assert (frame[:, :, 0] > 80).sum() > 50, "expected red agent pixels"


def test_matrix_helpers_shapes():
    from alife.render3d import look_at, perspective
    assert perspective(45, 1.3, 1, 100).shape == (4, 4)
    assert look_at(np.array([0.0, 0, 5]), np.zeros(3), np.array([0.0, 0, 1])).shape == (4, 4)
