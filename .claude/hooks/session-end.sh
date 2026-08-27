#!/usr/bin/env bash
# Hook: session-end
# Triggered: at the end of every session
# Purpose: Ensure knowledge is persisted before the session closes

# This hook reminds the AI to flush memory at session end.
# It writes a marker that the AI can read at next session start.

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
