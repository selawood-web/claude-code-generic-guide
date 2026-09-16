#!/usr/bin/env bash
# Hook: session-start
# Triggered: at the start of every session (startup, resume, clear, compact)
# Purpose: open the session with repo health and memory pointers, per the
#          session protocol's "On session START" checklist.
#
# Portable by design: every check degrades to silence when its subject is
# absent, so this script is safe in any project that copies .claude/ in.
set -uo pipefail

# Live update: sync CCGG-owned files (skills, hooks, agents, validator) from the
# guide clone at CCGG_HOME, so every session starts on the guide revision the
# project pinned. Skills also refresh mid-session on next invocation.
#
# Trust boundary: whatever update.sh finds in that clone runs here with the
# user's permissions, on every session start, resume, clear, and compact — and
# under `claude -p` with no trust dialog at all. So a clone from CCGG_REPO is
# made only at CCGG_REF (a tag or branch you control), and update.sh runs only
# while the clone's HEAD is at that ref. A clone that already exists without a
# pin (your own working checkout) is synced as-is. Failures are printed, never
# hidden: a silent sync failure looks exactly like a compromised one.
ccgg_at_ref() { # $1 = clone, $2 = ref name
  head="$(git -C "$1" rev-parse HEAD 2>/dev/null)" || return 1
  want="$(git -C "$1" rev-parse --verify -q "refs/ccgg/pin" 2>/dev/null \
       || git -C "$1" rev-parse --verify -q "$2^{commit}" 2>/dev/null)" || return 1
  [ -n "$head" ] && [ "$head" = "$want" ]
}
if [ -n "${CCGG_HOME:-}" ]; then
  if [ ! -d "$CCGG_HOME" ] && [ -n "${CCGG_REPO:-}" ] && command -v git >/dev/null 2>&1; then
    if [ -n "${CCGG_REF:-}" ]; then
      git clone --depth 1 -q --branch "$CCGG_REF" "$CCGG_REPO" "$CCGG_HOME" \
        || echo "-- ccgg: clone of $CCGG_REPO at $CCGG_REF failed; live sync skipped --"
    else
      echo "-- ccgg: CCGG_REPO is set without CCGG_REF; refusing an unpinned clone — set CCGG_REF to a tag or branch --"
    fi
  fi
  if [ -x "${CCGG_HOME}/update.sh" ]; then
    if [ -n "${CCGG_REF:-}" ] && ! ccgg_at_ref "$CCGG_HOME" "$CCGG_REF"; then
      echo "-- ccgg: $CCGG_HOME is not at $CCGG_REF; live sync skipped --"
    else
      "${CCGG_HOME}/update.sh" --quiet "${CLAUDE_PROJECT_DIR:-.}" || echo "-- ccgg: update.sh failed --"
    fi
  fi
fi

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

# Open decisions: surface records still awaiting confirmation.
DECISIONS_DIR="${CLAUDE_PROJECT_DIR:-.}/decisions"
if [ -d "$DECISIONS_DIR" ]; then
  OPEN=$(grep -l '\*\*Status:\*\* proposed' "$DECISIONS_DIR"/*.md 2>/dev/null || true)
  if [ -n "${OPEN:-}" ]; then
    echo "-- open decisions (status: proposed) --"
    echo "$OPEN"
  fi
fi

exit 0
