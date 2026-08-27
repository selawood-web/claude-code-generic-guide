#!/usr/bin/env bash
# Hook: pre-compact
# Triggered: before context window compaction
# Purpose: Flush memory before important conversation history is discarded

# This hook signals the AI to save memory before compaction happens.
echo "pre-compact: run /flush to preserve session knowledge before compaction"

exit 0
