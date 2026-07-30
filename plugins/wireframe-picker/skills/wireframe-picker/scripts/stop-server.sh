#!/usr/bin/env bash
# Stops a running pick-server given its state_dir (from the server-started
# JSON) or the session dir containing it.
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: stop-server.sh <state_dir|session_dir>" >&2
  exit 1
fi

TARGET="$1"
STATE_DIR="$TARGET"
if [ -f "$TARGET/state/server-info" ]; then
  STATE_DIR="$TARGET/state"
fi

INFO_FILE="$STATE_DIR/server-info"
if [ ! -f "$INFO_FILE" ]; then
  echo "No server-info found at $INFO_FILE" >&2
  exit 1
fi

PID="$(node -e "console.log(JSON.parse(require('fs').readFileSync('$INFO_FILE','utf8')).pid)")"

if kill -0 "$PID" 2>/dev/null; then
  kill -TERM "$PID"
  for _ in $(seq 1 20); do
    kill -0 "$PID" 2>/dev/null || break
    sleep 0.1
  done
  if kill -0 "$PID" 2>/dev/null; then
    kill -KILL "$PID" 2>/dev/null || true
  fi
  echo "Stopped pick-server (pid $PID)."
else
  echo "pick-server (pid $PID) was not running."
fi
