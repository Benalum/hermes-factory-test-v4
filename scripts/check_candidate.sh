#!/usr/bin/env bash
set -euo pipefail

command -v git >/dev/null || { echo "ERROR: git required" >&2; exit 1; }
command -v gh >/dev/null || { echo "ERROR: gh required" >&2; exit 1; }

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "ERROR: not in a git repository" >&2
  exit 1
}
cd "$ROOT"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: working tree is dirty; candidate identity is not trustworthy." >&2
  git status --short >&2
  exit 1
fi

BRANCH="$(git branch --show-current)"
[[ -n "$BRANCH" ]] || { echo "ERROR: detached HEAD is not an active delivery branch" >&2; exit 1; }
[[ "$BRANCH" != "main" ]] || { echo "ERROR: delivery candidate must not be main" >&2; exit 1; }

HEAD_SHA="$(git rev-parse HEAD)"
git fetch origin --prune --quiet

git show-ref --verify --quiet "refs/remotes/origin/$BRANCH" || {
  echo "ERROR: origin/$BRANCH does not exist" >&2
  exit 1
}
REMOTE_SHA="$(git rev-parse "origin/$BRANCH")"

PR_STATE="$(gh pr view "$BRANCH" --json state --jq .state)"
PR_BASE="$(gh pr view "$BRANCH" --json baseRefName --jq .baseRefName)"
PR_HEAD_BRANCH="$(gh pr view "$BRANCH" --json headRefName --jq .headRefName)"
PR_HEAD_SHA="$(gh pr view "$BRANCH" --json headRefOid --jq .headRefOid)"
PR_URL="$(gh pr view "$BRANCH" --json url --jq .url)"

[[ "$PR_STATE" == "OPEN" ]] || {
  echo "ERROR: delivery PR is not open (state=$PR_STATE)" >&2
  exit 1
}
[[ "$PR_BASE" == "main" ]] || {
  echo "ERROR: delivery PR base is $PR_BASE, expected main" >&2
  exit 1
}
[[ "$PR_HEAD_BRANCH" == "$BRANCH" ]] || {
  echo "ERROR: PR head branch $PR_HEAD_BRANCH != local branch $BRANCH" >&2
  exit 1
}
[[ "$HEAD_SHA" == "$REMOTE_SHA" ]] || {
  echo "ERROR: local HEAD $HEAD_SHA != origin/$BRANCH $REMOTE_SHA" >&2
  exit 1
}
[[ "$HEAD_SHA" == "$PR_HEAD_SHA" ]] || {
  echo "ERROR: local HEAD $HEAD_SHA != PR HEAD $PR_HEAD_SHA" >&2
  exit 1
}

printf 'candidate_ok=true\nbranch=%s\nhead_sha=%s\npr_url=%s\n' \
  "$BRANCH" "$HEAD_SHA" "$PR_URL"
