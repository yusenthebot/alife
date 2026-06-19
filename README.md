# alife — an evolving artificial-life ecosystem

A growing library of artificial-life and complex-systems models, built from zero in autonomous
**evolving rounds**. The project started at the simplest possible swarm — blind Boids flocking —
and has climbed ~120 rounds since: genetic selection, neural-network brains, predator–prey arms
races, energy/reproduction, 3D ecosystems you watch evolve, GPU worlds of a million agents, the
origin of life, network science, self-organized criticality, reaction–diffusion and excitable
media, major evolutionary transitions, active matter that evolves its own locomotion, fluid
dynamics with evolved swimmers, random-matrix ecology, and developmental pattern formation
(somitogenesis, growing-domain Turing, phyllotaxis, snow-crystal growth).

Each round clears the current bar, researches the frontier, then raises it — and **every result is
really run**: frames rendered, screenshots inspected, metrics plotted and red-teamed, never faked.
Each model is one self-contained Python module with its own tests and a reproducible figure.

- **Full round-by-round catalog and current state:** [`progress.md`](progress.md)
- **How the codebase is organized:** [`CODEBASE_GUIDE.md`](CODEBASE_GUIDE.md)
- **Operator's walkthrough (which command shows what):** [`QUICKSTART.md`](QUICKSTART.md)

## Architecture

```
   ┌──────────────────────────────────────────────────────────────┐
   │  Evolving-rounds methodology                                   │
   │  each round:  clear the bar → research the frontier → raise it │
   │  every result really run, screenshot-/data-verified, not faked │
   └───────────────────────────────┬──────────────────────────────┘
                                    │  + 1 self-contained model per round
   ┌──────────────────────────────────────────────────────────────┐
   │  MODEL CATALOG    alife/<topic>.py    (~121 models, R1 → Rn)   │
   │  flocking · selection · neural brains · predator–prey · 3D     │
   │  ecosystems · open-endedness · evolving bodies · origin-of-    │
   │  life · networks · criticality · reaction–diffusion /          │
   │  excitable media · major transitions · evolved active matter   │
   └──────┬─────────────────────────┬──────────────────────┬───────┘
          │ built on                │ measured by           │ driven by
   ┌──────▼───────────┐   ┌─────────▼────────┐   ┌──────────▼──────────┐
   │ SUBSTRATE        │   │ ANALYSIS         │   │ DRIVERS + OUTPUT    │
   │ world · genome   │   │ metrics.py       │   │ scripts/run_<topic> │
   │ brain · sensors  │   │ per-model        │   │   → runs/r<N>_<x>/  │
   │ particlelife     │   │ metrics &        │   │      *.png figures  │
   │ CA grids ·       │   │ red-team checks  │   │ tests/test_<topic>  │
   │ networks         │   │                  │   │   (712 pytest)      │
   │ numpy · scipy ·  │   └──────────────────┘   └─────────────────────┘
   │ moderngl GPU     │
   └──────────────────┘
```

A single shared substrate (toroidal/3D space, genomes, neural brains, sensors, cellular-automaton
grids, particle systems, graphs, and a moderngl GPU-compute path) underpins every model. Each round
adds `alife/<topic>.py` plus `tests/test_<topic>.py` and `scripts/run_<topic>.py`, which writes a
figure to `runs/r<N>_<topic>/`. See [`CODEBASE_GUIDE.md`](CODEBASE_GUIDE.md) for the full layout.

## Setup

Requires Python 3.12. Pure CPU runs out of the box; the GPU models need an OpenGL 4.6 context
(any modern GPU; tested on an RTX 5080).

```bash
git clone https://github.com/yusenthebot/alife.git
cd alife
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Dependencies (`requirements.txt`): numpy, scipy, matplotlib, pillow, imageio, imageio-ffmpeg,
moderngl, pytest.

## Run it

Use the `scripts/run.sh` wrapper — it runs inside the venv and sets the path so `import alife`
works (and isolates from a sourced ROS2 `PYTHONPATH`, if any):

```bash
scripts/run.sh scripts/run_boids.py          # R1   — emergent flocking
scripts/run.sh scripts/run_evolve.py         # R3   — evolved neural-network brains
scripts/run.sh scripts/run_excitable.py      # R88  — excitable-media spiral waves
scripts/run.sh scripts/run_chimera.py        # R115 — chimera states (order + chaos at once)
scripts/run.sh scripts/run_phyllotaxis.py    # R118 — the golden angle of sunflowers
scripts/run.sh scripts/run_snowflake.py      # R119 — six-fold snow-crystal growth
```

Each script prints a short summary and writes its figure (and any video/frames) to `runs/<name>/`
(gitignored). Open the `.png`/`.mp4` to see the result. There is one `scripts/run_<topic>.py` per
model — browse them, or see [`QUICKSTART.md`](QUICKSTART.md) for a guided tour.

Run the test suite:

```bash
scripts/test.sh                              # full suite (712 tests)
scripts/test.sh tests/test_excitable.py      # a single model
```

## License

MIT.
