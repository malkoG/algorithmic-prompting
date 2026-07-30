#!/usr/bin/env bash
# Merges the chosen variant branch into the current branch, then removes
# every variant worktree and branch (winner and losers alike — the winner's
# commits now live on the current branch).
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: resolve-variant.sh <chosen-branch> <all-variant-branch>..." >&2
  exit 1
fi

CHOSEN="$1"
shift
ALL_BRANCHES=("$CHOSEN" "$@")

REPO_ROOT="$(git rev-parse --show-toplevel)"

git -C "$REPO_ROOT" merge --no-edit "$CHOSEN"

for BRANCH in "${ALL_BRANCHES[@]}"; do
  WORKTREE_PATH="$(git -C "$REPO_ROOT" worktree list --porcelain \
    | awk -v b="refs/heads/$BRANCH" '
        /^worktree /{path=$2}
        $0=="branch "b{print path}
      ')"
  if [ -n "$WORKTREE_PATH" ]; then
    git -C "$REPO_ROOT" worktree remove --force "$WORKTREE_PATH"
  fi
  git -C "$REPO_ROOT" branch -D "$BRANCH" 2>/dev/null || true
done

echo "Merged $CHOSEN and cleaned up ${#ALL_BRANCHES[@]} variant worktree(s)."
