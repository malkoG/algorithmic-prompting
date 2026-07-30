#!/usr/bin/env bash
# Screenshots one rendered variant with Playwright. Wraps `npx playwright
# screenshot` so callers don't need it as a project dependency — npx fetches
# it on demand (run `npx playwright install chromium` once per machine).
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: capture-screenshot.sh <url> <output.png> [--wait-for-timeout ms] [--full-page]" >&2
  exit 1
fi

URL="$1"
OUTPUT="$2"
shift 2

mkdir -p "$(dirname "$OUTPUT")"

npx --yes playwright screenshot \
  --wait-for-timeout 500 \
  --viewport-size 1280,800 \
  "$@" \
  "$URL" "$OUTPUT"
