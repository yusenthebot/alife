# QUICKSTART — watch the ecosystem evolve

For an operator (no coding needed). Each command runs a stage, prints a short
summary, and drops a video + key frames + plots into `runs/<name>/`. Open the
`.mp4` or the `.png` frames to watch.

## One-time setup

```bash
cd ~/alife
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run a stage (each writes to runs/<name>/)

All runs go through `scripts/run.sh`, which uses the project's venv and stays
clear of a sourced ROS2 environment.

```bash
# R1  — 2D flocking emerges (order parameter climbs to ~0.95)
scripts/run.sh scripts/run_boids.py --name flock          # -> runs/flock/flock.mp4

# R2  — natural selection: traits drift under selection across generations
scripts/run.sh scripts/run_evolution.py --name evo        # -> traits.png, trait_hist.png

# R3  — evolved neural-network foraging brains (random vs evolved)
scripts/run.sh scripts/run_evolve.py --name brains        # -> behavior.png, fitness_evolution.png

# R4  — predator-prey co-evolution (arms race)
scripts/run.sh scripts/run_coevo.py --name coevo          # -> arms_race.png, coevo.mp4

# R5  — continuous predator-prey ecology (2D)
scripts/run.sh scripts/run_predprey.py --name ecology     # -> populations.png, phase_plane.png

# R7  — 3D flocking on the GPU (orbiting camera)            *** start here for the visuals ***
scripts/run.sh scripts/run_boids3d.py --name flock3d      # -> flock3d.mp4

# R8  — evolved 3D foragers + living 3D ecosystem
scripts/run.sh scripts/run_evolve3d.py --name foragers3d  # -> eco3d.mp4, fitness3d.png

# R9  — predator-prey in 3D (aerial arms race)
scripts/run.sh scripts/run_coevo3d.py --name hunt3d       # -> hunt3d.mp4, arms_race3d.png

# R10/R11 — the self-sustaining, atmospheric 3D living world  *** the finale ***
scripts/run.sh scripts/run_predprey3d.py --name world3d   # -> world3d.mp4, pop3d.png
```

Heavier runs (the 3D evolution/co-evolution ones) take a few minutes — they
evolve brains first, then render. Watch the printed summary for progress.

## Run the tests

```bash
scripts/test.sh
```

## What you're looking at

- **Cyan** = prey · **red** = predators · **green glowing motes** = food/plants.
- Cones point along each creature's heading; color in flocking views encodes heading.
- The 3D world fades into atmospheric fog; the camera slowly orbits.

See `README.md` for the full story (R1 → R11) and `progress.md` for current state.
