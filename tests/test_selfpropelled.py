import numpy as np

from alife.selfpropelled import (
    SPPConfig, run, step, init, morse_force, polarization, milling, classify, PRESETS,
)
from dataclasses import replace


def test_milling_metric_on_controls():
    # tangent ring -> M~1, P~0 ; half-CW-half-CCW -> M~0 (signed); aligned -> P~1
    th = np.linspace(0, 2 * np.pi, 200, endpoint=False)
    pc = np.c_[np.cos(th), np.sin(th)]
    vt = np.c_[-np.sin(th), np.cos(th)]
    assert milling(pc, vt) > 0.95 and polarization(vt) < 0.05
    vmix = vt.copy(); vmix[100:] *= -1
    assert milling(pc, vmix) < 0.1
    assert polarization(np.tile([1.0, 0.0], (100, 1))) > 0.99


def test_morse_force_repels_close_attracts_far():
    cfg = SPPConfig()
    close = morse_force(np.array([[0.0, 0.0], [0.3, 0.0]]), cfg)[0]
    far = morse_force(np.array([[0.0, 0.0], [1.5, 0.0]]), cfg)[0]
    assert close[0][0] < 0          # particle 0 pushed in -x, away from particle 1 at +x
    assert far[0][0] > 0            # particle 0 pulled toward particle 1


def test_mill_state_forms():
    r = run(replace(PRESETS["mill"], N=250, steps=1700, seed=1))
    P, M = r["P"][-30:].mean(), r["M"][-30:].mean()
    assert M > 0.7 and P < 0.3 and classify(P, M) == "mill"


def test_flock_state_forms():
    r = run(replace(PRESETS["flock"], N=250, steps=1700, seed=1))
    P, M = r["P"][-30:].mean(), r["M"][-30:].mean()
    assert P > 0.9 and M < 0.2 and classify(P, M) == "flock"


def test_clump_state_is_slow_and_disordered():
    r = run(replace(PRESETS["clump"], N=250, steps=1500, seed=1))
    P, M = r["P"][-30:].mean(), r["M"][-30:].mean()
    speed = np.linalg.norm(r["v"], axis=1).mean()
    assert speed < 0.7 and P < 0.3 and M < 0.3


def test_alignment_flips_mill_to_flock():
    mill = run(replace(SPPConfig(align=0.0), N=250, steps=1700, seed=2))
    flock = run(replace(SPPConfig(align=2.0), N=250, steps=1700, seed=2))
    assert mill["M"][-30:].mean() > 0.6 and mill["P"][-30:].mean() < 0.3
    assert flock["P"][-30:].mean() > 0.9 and flock["M"][-30:].mean() < 0.3


def test_active_particles_reach_preferred_speed():
    # self-propulsion drives |v| toward sqrt(alpha/beta)
    r = run(replace(PRESETS["mill"], N=200, steps=1500, seed=3))
    v0 = np.sqrt(1.6 / 0.5)
    assert abs(np.linalg.norm(r["v"], axis=1).mean() - v0) < 0.3


def test_reproducible():
    a = run(replace(PRESETS["mill"], N=150, steps=300, seed=7))["x"]
    b = run(replace(PRESETS["mill"], N=150, steps=300, seed=7))["x"]
    assert np.array_equal(a, b)
