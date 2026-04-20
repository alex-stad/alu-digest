#!/usr/bin/env bash
# test_local.sh — Local dry-run for the alu-digest pipeline.
#
# USAGE
#   ./scripts/test_local.sh                     # Full run: Claude + pipeline (~$2.25, ~12 min)
#   ./scripts/test_local.sh --render-only FILE  # Re-render an existing JSON (<5 sec, $0)
#
# BEHAVIOUR
#   Always runs with TEST_MODE=true, which makes generate_digest.py:
#     • call Buttondown with status=draft (NOT delivered to subscribers)
#     • skip gh-pages push
#     • write dedup changes to output/dedup_history_test.json (gitignored)
#     • prefix the email subject with "[TEST] "
#
#   When you're happy with the draft, either (a) manually promote it via the
#   Buttondown UI or API (POST /v1/emails/{id}/send-draft), or (b) delete it
#   and let the next scheduled cron produce the real one.
#
# REVIEW
#   Drafts land in https://buttondown.com/emails under the "Drafts" tab.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

# Load BUTTONDOWN_API_KEY from .env if not already in the shell
if [ -z "${BUTTONDOWN_API_KEY:-}" ] && [ -f .env ]; then
  set -a; source .env; set +a
fi
if [ -z "${BUTTONDOWN_API_KEY:-}" ]; then
  echo "ERROR: BUTTONDOWN_API_KEY not set. Put it in .env at the project root." >&2
  exit 1
fi

export TEST_MODE=true

# ── MODE 1: render-only (fast path) ────────────────────────────────────────
if [ "${1:-}" = "--render-only" ]; then
  JSON_FILE="${2:-}"
  if [ -z "${JSON_FILE}" ] || [ ! -f "${JSON_FILE}" ]; then
    echo "Usage: $0 --render-only <path/to/digest.json>" >&2
    exit 1
  fi
  # Extract date slug from filename if it matches digest_YYYY-MM-DD.json,
  # else fall back to today.
  DATE_SLUG=$(basename "${JSON_FILE}" .json | sed -n 's/^digest_\(.*\)$/\1/p')
  [ -z "${DATE_SLUG}" ] && DATE_SLUG=$(date +%Y-%m-%d)
  echo "── Render-only mode (no Claude call) ───────────────────────────"
  echo "  JSON:      ${JSON_FILE}"
  echo "  Date slug: ${DATE_SLUG}"
  echo
  python3 scripts/generate_digest.py \
    --test-mode \
    --json-file "${JSON_FILE}" \
    --date-slug "${DATE_SLUG}"
  exit $?
fi

# ── MODE 2: full pipeline (Claude + render) ────────────────────────────────
if ! command -v claude >/dev/null 2>&1; then
  echo "ERROR: 'claude' CLI not found on PATH. Install via: npm install -g @anthropic-ai/claude-code" >&2
  exit 1
fi

TODAY=$(python3 -c "from datetime import datetime; print(datetime.now().strftime('%A, %d %B %Y'))")
DATE_SLUG=$(python3 -c "from datetime import datetime; print(datetime.now().strftime('%Y-%m-%d'))")

echo "── Full local dry-run ──────────────────────────────────────────"
echo "  Date:      ${TODAY}"
echo "  Date slug: ${DATE_SLUG}"
echo "  Project:   ${PROJECT_ROOT}"
echo "  TEST_MODE: ${TEST_MODE}"
echo
echo "Claude will run the full task_prompt.md pipeline and call the"
echo "pipeline with TEST_MODE already set. Nothing is pushed to gh-pages"
echo "and no email is sent to subscribers — only a Buttondown draft."
echo

claude -p "Today's date is: ${TODAY}. Date slug: ${DATE_SLUG}. The project root is: ${PROJECT_ROOT}. Read the file ${PROJECT_ROOT}/task_prompt.md and execute every step in it (Steps 1 through 9) exactly as described. Replace PROJECT_ROOT with ${PROJECT_ROOT} wherever the instructions mention it." \
  --allowedTools "Bash,Read,Write,WebSearch,Glob,Grep" \
  --max-turns 70 \
  --output-format stream-json \
  --verbose
