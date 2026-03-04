#!/usr/bin/env bash
# batch_trigger_workflows.sh
# Trigger the "Call Worktree Update" workflow for all course repos.
#
# Usage:
#   export GITHUB_TOKEN="ghp_..."   # PAT with `actions:write` scope
#   bash batch_trigger_workflows.sh [--dry-run] [--delay SECONDS]
#
# Options:
#   --dry-run    Print curl commands without executing them
#   --delay N    Seconds between API calls (default: 2, to avoid rate-limiting)

set -euo pipefail

ORG="HITSZ-OpenAuto"
REPOS_LIST="$(cd "$(dirname "$0")/.." && pwd)/repos_list.txt"
WORKFLOW_FILE="trigger-workflow.yml"  # Name matches .github/workflows/ in each repo
DELAY=2
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --delay) DELAY="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "ERROR: GITHUB_TOKEN environment variable not set." >&2
  echo "  export GITHUB_TOKEN='ghp_...'" >&2
  exit 1
fi

if [[ ! -f "$REPOS_LIST" ]]; then
  echo "ERROR: repos_list.txt not found at $REPOS_LIST" >&2
  exit 1
fi

total=0
success=0
skipped=0
failed=0

while IFS= read -r repo; do
  # Skip blank lines and comments
  [[ -z "$repo" || "$repo" == \#* ]] && continue

  # Skip non-course repos
  [[ "$repo" == "course-template" ]] && { ((skipped++)); continue; }

  total=$((total + 1))
  url="https://api.github.com/repos/${ORG}/${repo}/actions/workflows/${WORKFLOW_FILE}/dispatches"

  if $DRY_RUN; then
    echo "[DRY-RUN] POST $url (ref=main)"
    continue
  fi

  echo -n "[$total] Triggering ${repo}... "
  http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    "$url" \
    -d '{"ref":"main"}')

  if [[ "$http_code" == "204" ]]; then
    echo "OK (204)"
    success=$((success + 1))
  else
    echo "FAILED (HTTP $http_code)"
    failed=$((failed + 1))
  fi

  sleep "$DELAY"
done < "$REPOS_LIST"

echo ""
echo "=== Summary ==="
echo "Total:   $total"
echo "Success: $success"
echo "Failed:  $failed"
echo "Skipped: $skipped"
