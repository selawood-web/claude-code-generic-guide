#!/usr/bin/env bash
# Hook: context-guard (UserPromptExpansion, UserPromptSubmit)
# Registered by: .claude/settings.json, on both events, no matcher.
# Purpose: catch the costliest pattern measured so far — heavy work started on
#          top of a long session. Every step re-reads the whole context, so the
#          orchestration of a /ccgg-audit run on a ~415k-token session
#          (healthvault-dt, 2026-09-28: 249 steps) cost about 2.5x the eleven
#          subagents it launched. No hook can run /flush, /compact or /clear
#          itself, so the guard stops and names the steps instead.
#
#   UserPromptExpansion — a typed command listed in HEAVY, on a context over
#     CCGG_HEAVY_MAX_TOKENS (default 100000), is blocked once with exit 2. The
#     reason on stderr is shown to the user; the model never sees it. The fix
#     it names is /flush, /clear, then the command again: these commands need
#     nothing from the conversation, so /clear starts them at a fresh session's
#     size, where /compact would still carry a summary and spend a full-context
#     pass writing it. Typing the same command again in the same session runs
#     it — the block is a checkpoint, never a wall.
#   UserPromptSubmit — any prompt on a context over CCGG_CONTEXT_WARN_TOKENS
#     (default 300000) gets one systemMessage line, shown to the user only,
#     once per 100k step so the same warning is not repeated every turn.
#
# Context size is the last main-thread assistant turn's input, cache-read and
# cache-creation tokens in the transcript; a compact boundary after that turn
# means the context was just rebuilt, so nothing is measured. Anything missing
# or unreadable degrades to silence (exit 0): the guard never blocks on a guess.
# CCGG_CONTEXT_GUARD=off disables it entirely.
set -uo pipefail

[ "${CCGG_CONTEXT_GUARD:-}" = "off" ] && exit 0

# Commands that fan out into subagents or run for many steps. Kept to the ones
# that need nothing from the conversation they are typed into.
HEAVY=" ccgg-audit gbb product-brief dream "

# This runs on every prompt, and on Windows every process it starts costs tens
# of milliseconds, so parsing stays in bash builtins: one grep and one tail per
# prompt, none at all for a command that is not heavy.
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

json_str hook_event_name; event=$REPLY
json_str transcript_path; transcript=$REPLY
# JSON escapes a Windows path's backslashes; forward slashes work in Git Bash.
transcript="${transcript//\\\\//}"
json_str session_id; session="${REPLY//[^A-Za-z0-9-]/}"
[ -n "$transcript" ] && [ -n "$session" ] || exit 0

cmd=""
if [ "$event" = "UserPromptExpansion" ]; then
  json_str command_name; cmd="${REPLY#/}"
  [ -n "$cmd" ] || exit 0
  case "$HEAVY" in *" $cmd "*) ;; *) exit 0 ;; esac
fi

context_tokens "$transcript"
[ -n "$tokens" ] || exit 0
kilo=$((tokens / 1000))

state="${TMPDIR:-/tmp}/ccgg-context-guard-${UID:-user}"
[ -d "$state" ] || mkdir -p "$state" 2>/dev/null || exit 0

case "$event" in
  UserPromptExpansion)
    num_or "${CCGG_HEAVY_MAX_TOKENS:-}" 100000; max=$REPLY
    [ "$tokens" -gt "$max" ] || exit 0
    marker="$state/$session.$cmd"
    if [ -e "$marker" ]; then exit 0; fi
    : > "$marker" 2>/dev/null || exit 0
    cat >&2 <<EOF
Context guard: this session already holds ~${kilo}k tokens, and /$cmd re-reads all of it on every step it takes.
Start it clean instead:
  1. /flush  - save what this session decided
  2. /clear  - start a fresh context
  3. /$cmd again
Type /$cmd again to run it here anyway.
EOF
    exit 2
    ;;
  UserPromptSubmit)
    num_or "${CCGG_CONTEXT_WARN_TOKENS:-}" 300000; warn=$REPLY
    [ "$tokens" -gt "$warn" ] || exit 0
    step=$((tokens / 100000))
    marker="$state/$session.warn"
    last=""
    [ -r "$marker" ] && read -r last < "$marker"
    [ "$last" = "$step" ] && exit 0
    echo "$step" > "$marker" 2>/dev/null || exit 0
    printf '{"systemMessage":"Context guard: this session holds ~%sk tokens and every turn re-reads all of it. Task finished? /flush, then /clear. Mid-task? /compact."}\n' "$kilo"
    exit 0
    ;;
esac
exit 0
