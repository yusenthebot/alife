# CODEBASE_GUIDE — how the repository is organized

This is the developer's map of the codebase. For *what each round built* and the current state, see
[`progress.md`](progress.md) (the full round-by-round catalog). For an operator's run-by-run tour,
see [`QUICKSTART.md`](QUICKSTART.md).

## Directory layout

```
alife/        one Python module per model + the shared substrate (~121 modules)
tests/        pytest — one tests/test_<topic>.py per model (712 tests)
scripts/      one scripts/run_<topic>.py per model; writes a figure to runs/
runs/         generated figures/videos: runs/r<N>_<topic>/<topic>.png  (gitignored)
requirements.txt   numpy, scipy, matplotlib, pillow, imageio(+ffmpeg), moderngl, pytest
progress.md   durable project record: round-by-round catalog + current state
QUICKSTART.md operator guide (which command shows what)
```

## The per-round module pattern

Every round is a self-contained vertical slice with the same four parts, keyed by a short topic name:

| Part | Path | Role |
|------|------|------|
| Model | `alife/<topic>.py` | the simulation/algorithm — pure functions + small dataclass configs |
| Tests | `tests/test_<topic>.py` | verifies the headline claim + a built-in control; kept fast |
| Driver | `scripts/run_<topic>.py` | runs the model and renders the figure |
| Figure | `runs/r<N>_<topic>/<topic>.png` | the eye-verified result for round N |

To find a model, start from its row in [`progress.md`](progress.md), then open `alife/<topic>.py`.
Models are deliberately decoupled: most depend only on numpy/scipy and (optionally) the shared
substrate below, not on each other.

## Shared substrate

A handful of modules are reused across many rounds rather than being a single round's model:

- **Space & dynamics** — `world.py` (toroidal/bounded 2D: wrap, minimum-image, cross-set distance),
  `world3d.py` (3D arena), `metrics.py` (order parameter, milling, packing, cluster count).
- **Evolution** — `genome.py` (heritable traits + mutation), `ecosystem.py` (energy / feeding /
  reproduction / death / selection), `evolve.py` / `evolve3d.py` (generational GAs).
- **Brains & sensing** — `brain.py` (MLP whose weights are the genome), `sensors.py` (egocentric
  food/neighbor senses).
- **Rendering** — `render.py` (headless Pillow renderer), `render3d.py` (moderngl GPU renderer,
  offscreen, runs headless).
- **GPU compute** — `gpu*.py` (`gpuboids`, `gpuevo`, `gpuecoevo`, `gpurd`, `gpuslime`, `gpulenia`):
  moderngl compute-shader worlds at ~1M agents (SSBO + ping-pong + memory barriers).

## Running and testing

Use the wrappers (they activate the venv, put the repo root on `PYTHONPATH` so `import alife` works,
and drop a sourced ROS2 `PYTHONPATH` if present):

```bash
scripts/run.sh scripts/run_<topic>.py     # run one model, render its figure
scripts/test.sh                           # full suite
scripts/test.sh tests/test_<topic>.py     # one model's tests
```

Equivalently, by hand from the repo root: `env -u PYTHONPATH PYTHONPATH=. .venv/bin/python …`.

## Conventions

- **numpy 2.x**: `ndarray.ptp()` was removed — use `np.ptp(a)`.
- Heavy GA/sim figures (e.g. R91) cache their expensive result to a `runs/.../*.npz` so re-rendering
  the figure is instant; the driver re-evolves only if the cache is missing.
- Models prefer pure functions and frozen dataclass configs; no global mutable state.
- Each round's figure is verified by eye and its headline metric red-teamed before it is recorded.
