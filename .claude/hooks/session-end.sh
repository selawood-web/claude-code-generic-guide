#!/usr/bin/env bash
# Hook: session-end
# Triggered: at the end of every session
# Purpose: record that the session ended, for the next session to read

# This hook prints nothing for the model, and could not: SessionEnd stdout goes
# to the debug log, never to the context (tools/audit_vocab.json,
# hook_stdout_reaches_model). What it does is write a timestamped marker;
# session-start.sh reads that file back and surfaces the timestamp only — never
# the sentence after it, which is for a human reading the log. A reminder the
# model should see belongs in session-start.sh as a fixed string (finding H-001).

SESSION_DIR="${HOME}/.claude/sessions"
MEMORY_DIR="${HOME}/.claude/memory"
HOOK_LOG="${HOME}/.claude/hooks/session-end.log"

# date -Iseconds is GNU-only; this format works on BSD/macOS date too
STAMP="$(date +%Y-%m-%dT%H:%M:%S%z)"

# Create both target directories before writing — neither exists by default
mkdir -p "$(dirname "$HOOK_LOG")" "$MEMORY_DIR"

echo "[$STAMP] session-end hook triggered" >> "$HOOK_LOG"

# Write a session-end marker so the next session knows to check memory
echo "[$STAMP] Session ended. Run /memory to review captured knowledge." >> "${MEMORY_DIR}/session-markers.log"

exit 0
