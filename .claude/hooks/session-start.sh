#!/usr/bin/env bash
# Hook: session-start
# Triggered: at the start of every session (startup, resume, clear, compact)
# Purpose: open the session with repo health and memory pointers, per the
#          session protocol's "On session START" checklist.
#
# Portable by design: every check degrades to silence when its subject is
# absent, so this script is safe in any project that copies .claude/ in.
#
# Everything this hook prints reaches the model as context. So it prints fixed
# strings, timestamps, and names that pass a character allow-list — never a
# configured URL, an environment value, a file's contents, or a validator
# finding verbatim. A planted value has no path from disk into the prompt here.
set -uo pipefail

# Live update: sync CCGG-owned files (skills, hooks, agents, validator) from the
# guide clone at CCGG_HOME, so every session starts on the guide revision the
# project pinned. Skills also refresh mid-session on next invocation.
#
# Trust boundary: whatever update.sh finds in that clone runs here with the
# user's permissions, on every session start, resume, clear, and compact — and
# under `claude -p` with no trust dialog at all. So update.sh runs only when
#   - CCGG_HOME and its update.sh are owned by this user (a pre-planted
#     directory at a shared path such as /tmp fails this),
#   - the clone's origin is CCGG_REPO when CCGG_REPO is set,
#   - the clone's HEAD is at CCGG_REF when CCGG_REF is set — a tag, a branch,
#     or a 40-hex commit; the commit form is the only one nobody can move.
# A clone from CCGG_REPO is made only at CCGG_REF. Failures are printed, never
# hidden: a silent sync failure looks exactly like a compromised one.
ccgg_is_sha() { case "$1" in *[!0-9a-f]*|"") return 1 ;; esac; [ "${#1}" -eq 40 ]; }
ccgg_owned() { [ -O "$1" ] && [ -O "$1/update.sh" ]; }
ccgg_origin_ok() { # $1 = clone, $2 = expected URL ("" = not configured)
  [ -z "$2" ] && return 0
  [ "$(git -C "$1" remote get-url origin 2>/dev/null)" = "$2" ]
}
ccgg_at_ref() { # $1 = clone, $2 = ref name or commit
  head="$(git -C "$1" rev-parse HEAD 2>/dev/null)" || return 1
  if ccgg_is_sha "$2"; then want="$2"; else
    want="$(git -C "$1" rev-parse --verify -q "refs/ccgg/pin" 2>/dev/null \
         || git -C "$1" rev-parse --verify -q "$2^{commit}" 2>/dev/null)" || return 1
  fi
  [ -n "$head" ] && [ "$head" = "$want" ]
}
ccgg_clone() { # $1 = repo URL, $2 = ref name or commit, $3 = destination
  git init -q "$3" \
    && git -C "$3" remote add origin "$1" \
    && git -C "$3" fetch -q --depth 1 origin "$2" \
    && git -C "$3" update-ref refs/ccgg/pin FETCH_HEAD \
    && git -C "$3" checkout -q --detach refs/ccgg/pin \
    && return 0
  rm -rf "$3"
  return 1
}
if [ -n "${CCGG_HOME:-}" ]; then
  CCGG_HOME="${CCGG_HOME/#\~/$HOME}" # settings.json env values are not shell-expanded
  if [ ! -e "$CCGG_HOME" ] && [ -n "${CCGG_REPO:-}" ] && command -v git >/dev/null 2>&1; then
    if [ -n "${CCGG_REF:-}" ]; then
      ccgg_clone "$CCGG_REPO" "$CCGG_REF" "$CCGG_HOME" >/dev/null 2>&1 \
        || echo "-- ccgg: clone of CCGG_REPO at CCGG_REF failed; live sync skipped --"
    else
      echo "-- ccgg: CCGG_REPO is set without CCGG_REF; refusing an unpinned clone — set CCGG_REF to a tag, branch, or commit --"
    fi
  fi
  if [ -x "${CCGG_HOME}/update.sh" ]; then
    if ! ccgg_owned "$CCGG_HOME"; then
      echo "-- ccgg: CCGG_HOME is not owned by this user; live sync skipped --"
    elif ! ccgg_origin_ok "$CCGG_HOME" "${CCGG_REPO:-}"; then
      echo "-- ccgg: CCGG_HOME's origin is not CCGG_REPO; live sync skipped --"
    elif [ -n "${CCGG_REF:-}" ] && ! ccgg_at_ref "$CCGG_HOME" "$CCGG_REF"; then
      echo "-- ccgg: CCGG_HOME is not at CCGG_REF; live sync skipped --"
    else
      "${CCGG_HOME}/update.sh" --quiet "${CLAUDE_PROJECT_DIR:-.}" || echo "-- ccgg: update.sh failed --"
    fi
  fi
fi

# Repo health: run the validator when the project ships one. Only its verdict
# line is printed — findings quote file content, and file content is not
# something this hook forwards to the model.
if [ -f "${CLAUDE_PROJECT_DIR:-.}/tools/validate.py" ] && command -v python3 >/dev/null 2>&1; then
  echo "-- repo validation --"
  VERDICT="$(python3 "${CLAUDE_PROJECT_DIR:-.}/tools/validate.py" 2>&1)"
  RC=$?
  echo "${VERDICT%%$'\n'*}"
  if [ "$RC" -ne 0 ]; then
    echo "(run python3 tools/validate.py for the findings — worth fixing early)"
  fi
fi

# Memory pointers: surface where the last session left off. The log name is
# the date /flush wrote it under; anything else in that directory is not named.
PROJECT_SLUG=$(basename "${CLAUDE_PROJECT_DIR:-$(pwd)}")
SESSIONS_DIR="${HOME}/.claude/memory/${PROJECT_SLUG}/sessions"
if [ -d "$SESSIONS_DIR" ]; then
  LATEST=$(ls -1 "$SESSIONS_DIR" 2>/dev/null | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$' | sort | tail -1)
  if [ -n "${LATEST:-}" ]; then
    echo "-- last session log: ${LATEST} in ~/.claude/memory/<project>/sessions/ (read it to pick up open threads) --"
  fi
fi
MARKERS="${HOME}/.claude/memory/session-markers.log"
if [ -f "$MARKERS" ]; then
  STAMP="$(tail -1 "$MARKERS" | sed -n 's/^\(\[[0-9TZ:+-]*\]\).*/\1/p')"
  if [ -n "${STAMP:-}" ]; then
    echo "-- last session end: ${STAMP} --"
  fi
fi

# Open decisions: surface records still awaiting confirmation — tracked files
# only, named only when the name is plain.
DECISIONS_DIR="${CLAUDE_PROJECT_DIR:-.}/decisions"
if [ -d "$DECISIONS_DIR" ] && command -v git >/dev/null 2>&1; then
  OPEN=""
  while IFS= read -r rec; do
    [ -n "$rec" ] || continue
    name="$(basename "$rec")"
    printf '%s' "$name" | grep -qE '^[A-Za-z0-9._-]+\.md$' || continue
    if grep -q '\*\*Status:\*\* proposed' "${CLAUDE_PROJECT_DIR:-.}/$rec" 2>/dev/null; then
      OPEN="${OPEN}decisions/${name}"$'\n'
    fi
  done < <(git -C "${CLAUDE_PROJECT_DIR:-.}" ls-files -- 'decisions/*.md' 2>/dev/null)
  if [ -n "${OPEN:-}" ]; then
    echo "-- open decisions (status: proposed) --"
    printf '%s' "$OPEN"
  fi
fi

exit 0
