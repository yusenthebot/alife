#!/usr/bin/env bash
# Run a simulation entry point in the project venv, isolated from ROS2 PYTHONPATH.
# Example: scripts/run.sh scripts/run_boids.py --n 700 --steps 450 --name demo
set -euo pipefail
cd "$(dirname "$0")/.."
# MEMORY GUARD (host is 64 GB, shared with other sessions/loops): cap virtual memory so a runaway
# allocation — e.g. an O(N^2) dense pairwise array (N_agents x N_targets x 3) — fails with a
# catchable MemoryError instead of OOM-killing the host and taking down other processes. CPU/numpy
# sims need <1 GB; 24 GB is a generous ceiling. Override with ALIFE_MEM_GB for a deliberate big run.
ulimit -v $(( ${ALIFE_MEM_GB:-24} * 1024 * 1024 )) 2>/dev/null || true
# -u drops a sourced ROS2 PYTHONPATH; PYTHONPATH=. then puts the repo root on the
# path so `import alife` works whether we run `-m`, `-c`, or a scripts/*.py file.
env -u PYTHONPATH PYTHONPATH=. .venv/bin/python "$@"
