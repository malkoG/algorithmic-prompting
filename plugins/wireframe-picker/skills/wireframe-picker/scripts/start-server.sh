#!/usr/bin/env bash
# Starts the wireframe-picker pick-server. Runs in the foreground by design —
# launch it with your Bash tool's background/async mode so it survives across
# turns (e.g. `run_in_background: true`). Prints the server-started JSON line
# to stdout as soon as the server is listening.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec node "$SCRIPT_DIR/pick-server.cjs" "$@"
