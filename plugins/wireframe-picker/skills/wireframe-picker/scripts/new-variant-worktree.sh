#!/usr/bin/env bash
# Creates one isolated worktree + branch for a single wireframe variant, so
# parallel subagents can each edit the same route/component without
# colliding. Prints a single JSON line with the branch and worktree path.
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: new-variant-worktree.sh <variant-id> [<base-branch>]" >&2
  exit 1
fi

VARIANT_ID="$1"
BASE="${2:-HEAD}"

REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_NAME="$(basename "$REPO_ROOT")"
BRANCH="wireframe/$VARIANT_ID"
WORKTREE_PATH="$(dirname "$REPO_ROOT")/${REPO_NAME}-wireframe-${VARIANT_ID}"

git -C "$REPO_ROOT" worktree add -b "$BRANCH" "$WORKTREE_PATH" "$BASE" >&2

node -e "console.log(JSON.stringify({variant: process.argv[1], branch: process.argv[2], path: process.argv[3]}))" \
  "$VARIANT_ID" "$BRANCH" "$WORKTREE_PATH"
