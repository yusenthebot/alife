#!/usr/bin/env bash
# Run the test suite in the project venv, isolated from a sourced ROS2 PYTHONPATH
# (which would otherwise autoload a broken launch_testing pytest plugin).
set -euo pipefail
cd "$(dirname "$0")/.."
env -u PYTHONPATH .venv/bin/python -m pytest -q -p no:cacheprovider "$@"
