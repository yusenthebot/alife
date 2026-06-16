#!/usr/bin/env bash
# Run a simulation entry point in the project venv, isolated from ROS2 PYTHONPATH.
# Example: scripts/run.sh scripts/run_boids.py --n 700 --steps 450 --name demo
set -euo pipefail
cd "$(dirname "$0")/.."
env -u PYTHONPATH .venv/bin/python "$@"
