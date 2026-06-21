#!/usr/bin/env bash
# GENESIS unattended daemon tick (R174) — the literal cron/systemd entrypoint.
#
# Start the world ONCE and leave it running: point a cron line / systemd timer at this script and every
# firing runs ONE idempotent tick — resume the on-disk world from $GENESIS_STATE, climb one segment in the
# SUSTAINED regime (large tree cap -> the open-ended climb keeps developing tick after tick, not saturating
# in tick 1), and refresh $GENESIS_STATE/live_panel.png. Process death between ticks is invisible (proved
# R169-R172): the next firing resumes the same civilization. Override the defaults via the env vars below.
#
#   crontab:   */10 * * * *  cd ~/alife && scripts/genesis_daemon_tick.sh >> ~/alife/runs/genesis_daemon.log 2>&1
#
set -euo pipefail
cd "$(dirname "$0")/.."

GENESIS_STATE="${GENESIS_STATE:-runs/genesis_world}"   # the one persistent on-disk world (start once)
GENESIS_SEED="${GENESIS_SEED:-0}"
GENESIS_SEG="${GENESIS_SEG:-60}"                        # steps climbed per tick
GENESIS_K="${GENESIS_K:-20000}"                         # tree memory cap (large -> sustained open-ended climb)

exec scripts/run.sh scripts/run_genesis_r174.py tick "$GENESIS_STATE" "$GENESIS_SEED" "$GENESIS_SEG" "$GENESIS_K"
