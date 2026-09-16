#!/usr/bin/env bash
# Hook: pre-compact
# Triggered: before context window compaction
# Purpose: shape the compaction summary so the facts whose loss causes re-work
#          survive it (charter, *Efficiency*).
#
# What this channel is: a PreCompact hook's stdout is handed to the compaction
# model as additional summary instructions. It is never shown to the agent, so
# it cannot ask the agent to run anything — a /flush before compaction has to be
# the user's or the agent's own call, earlier. Verified against the installed
# product by the 2026-09-16 audit (finding H-001).
echo "Preserve in the summary, verbatim where short: the branch boundary and standing constraints; every decision made and its reason; the code gate's current stage and pass count; open threads and blockers; files touched; and the path of the last session log under ~/.claude/memory."

exit 0
