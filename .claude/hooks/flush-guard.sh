#!/usr/bin/env bash
# Hook: flush-guard (Stop)
# Registered by: .claude/settings.json, no matcher.
# Purpose: make the session log the default instead of something remembered.
#          /flush was the only write path into project memory, and it ran only
#          when someone thought of it — in this repository's own cloud sessions
#          nothing was ever written (decisions/2026-11-03-repo-tracked-memory.md).
#
# Stop fires each time the main agent finishes a reply (never for a subagent:
# that is SubagentStop), under `claude -p` too — measured on CLI 2.1.317, where
# exit 2 continued the run and the next firing carried stop_hook_active true.
# The headless audit loads user settings only (tools/audit_headless.py,
# ISOLATION), so this hook never runs inside an audit. Once per session, when the context has grown past
# CCGG_FLUSH_MIN_TOKENS (default 150000) and memory/sessions/ holds no log
# dated today (UTC), it exits 2: the product hands the fixed text on stderr to
# Claude as its reason to continue, so the turn goes on to run /flush. Every
# other case exits 0 silently, and so does anything missing or unreadable — the
# guard never blocks on a guess. stop_hook_active (already continuing because
# of a stop hook) always passes, so it cannot loop. CCGG_FLUSH_GUARD=off
# disables it entirely.
#
# Nothing from the transcript or the tree reaches stderr: the message is a
# fixed string plus a number this script computed.
set -uo pipefail

[ "${CCGG_FLUSH_GUARD:-}" = "off" ] && exit 0

IFS= read -r -d '' INPUT || true

# First string value of a top-level key in the hook's machine-written JSON.
json_str() {
  local re="\"$1\"[[:space:]]*:[[:space:]]*\"([^\"]*)\""
  if [[ $INPUT =~ $re ]]; then REPLY="${BASH_REMATCH[1]}"; else REPLY=""; fi
}

# First number value of a key in a line.
json_num() { # $1 = key, $2 = line
  local re="\"$1\":([0-9]+)"
  if [[ $2 =~ $re ]]; then REPLY="${BASH_REMATCH[1]}"; else REPLY=0; fi
}

# An env override when it is a plain number, the default otherwise.
num_or() {
  case "$1" in ''|*[!0-9]*) REPLY="$2" ;; *) REPLY="$1" ;; esac
}

# Kept byte-identical to context_tokens in context-guard.sh — a separate script
# so update.sh registers it in installed projects on its own; the copy is held
# in place by tools/test_flush_guard.py.
# Tokens the model read on the last main-thread turn into $tokens, or empty.
context_tokens() {
  local t="$1" hits i line
  tokens=""
  [ -r "$t" ] || return 0
  # Structural matches only: inside a JSON string these quotes are escaped, so
  # quoted text in a tool result cannot pose as a turn.
  mapfile -t hits < <(grep -E '"type":"assistant"|"subtype":"compact_boundary"' "$t" 2>/dev/null | tail -n 20)
  for ((i = ${#hits[@]} - 1; i >= 0; i--)); do
    line="${hits[i]}"
    case "$line" in
      *'"subtype":"compact_boundary"'*) return 0 ;;   # context just rebuilt
      *'"isSidechain":true'*) continue ;;
      *'"cache_read_input_tokens"'*)
        json_num input_tokens "$line"; tokens=$REPLY
        json_num cache_read_input_tokens "$line"; tokens=$((tokens + REPLY))
        json_num cache_creation_input_tokens "$line"; tokens=$((tokens + REPLY))
        return 0 ;;
    esac
  done
}

json_str hook_event_name; [ "$REPLY" = "Stop" ] || exit 0
[[ $INPUT =~ \"stop_hook_active\"[[:space:]]*:[[:space:]]*true ]] && exit 0
json_str transcript_path; transcript="${REPLY//\\\\//}"
json_str session_id; session="${REPLY//[^A-Za-z0-9-]/}"
[ -n "$transcript" ] && [ -n "$session" ] || exit 0

context_tokens "$transcript"
[ -n "$tokens" ] || exit 0
num_or "${CCGG_FLUSH_MIN_TOKENS:-}" 150000; min=$REPLY
[ "$tokens" -gt "$min" ] || exit 0

# A log from today means this session, or one just before it, already flushed.
SESSIONS="${CLAUDE_PROJECT_DIR:-.}/memory/sessions"
TODAY="$(date -u +%Y-%m-%d)"
for f in "$SESSIONS/$TODAY"-*.md; do
  [ -e "$f" ] && exit 0
done

state="${TMPDIR:-/tmp}/ccgg-context-guard-${UID:-user}"
[ -d "$state" ] || mkdir -p "$state" 2>/dev/null || exit 0
marker="$state/$session.flush"
[ -e "$marker" ] && exit 0
: > "$marker" 2>/dev/null || exit 0

cat >&2 <<EOF
Flush guard: this session holds ~$((tokens / 1000))k tokens and nothing from it is in memory/sessions/ yet. Before ending this reply, run /flush so the session's decisions and open threads survive it, then finish. This check fires once per session; CCGG_FLUSH_GUARD=off disables it.
EOF
exit 2
