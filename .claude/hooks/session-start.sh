#!/usr/bin/env bash
# Hook: session-start
# Triggered: at the start of every session (startup, resume, clear, compact)
# Purpose: open the session with repo health and memory pointers, per the
#          session protocol's "On session START" checklist.
#
# Portable by design: every check degrades to silence when its subject is
# absent, so this script is safe in any project that copies .claude/ in.
set -uo pipefail

# Repo health: run the validator when the project ships one.
if [ -f "${CLAUDE_PROJECT_DIR:-.}/tools/validate.py" ] && command -v python3 >/dev/null 2>&1; then
  echo "-- repo validation --"
  python3 "${CLAUDE_PROJECT_DIR:-.}/tools/validate.py" || echo "(validator reported findings above — worth fixing early)"
fi

# Memory pointers: surface where the last session left off.
PROJECT_SLUG=$(basename "${CLAUDE_PROJECT_DIR:-$(pwd)}")
SESSIONS_DIR="${HOME}/.claude/memory/${PROJECT_SLUG}/sessions"
if [ -d "$SESSIONS_DIR" ]; then
  LATEST=$(ls -1 "$SESSIONS_DIR"/*.md 2>/dev/null | sort | tail -1)
  if [ -n "${LATEST:-}" ]; then
    echo "-- last session log: ${LATEST} (read it to pick up open threads) --"
  fi
fi
MARKERS="${HOME}/.claude/memory/session-markers.log"
if [ -f "$MARKERS" ]; then
  echo "-- last session end: $(tail -1 "$MARKERS") --"
fi

exit 0
