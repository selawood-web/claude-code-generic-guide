---
name: flush
description: Write a structured summary of the current session to the memory log so future sessions can recall it. Use when the user says "flush", "save this session", "write a session summary", before context compaction, or at the end of a productive session.
when-to-use: flush, save session, session summary, before compact, end of session, preserve context
allowed-tools: powershell, bash
argument-hint: "[optional: topics to emphasize in the summary]"
purpose: Structured session summary written to the memory log
---

# Flush Skill — Session Summary to Memory

## Purpose
Persist what happened in this session before it is lost to compaction or session end. This is the write-side of the memory system: `/flush` records, future sessions recall.

## Steps

### Step 1 — Resolve the memory location
```bash
PROJECT_SLUG=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")
MEMORY_DIR="${HOME}/.claude/memory/${PROJECT_SLUG}/sessions"
mkdir -p "$MEMORY_DIR"
```
Success: the directory exists and is writable.

### Step 2 — Gather the session's facts
```bash
git --no-pager log --oneline -10
git --no-pager diff --stat HEAD~5 2>/dev/null || git --no-pager diff --stat
git --no-pager status --short
```
Success: you can list what was changed, committed, and left open.

### Step 3 — Compose the summary
Write from the conversation, not just from git. If the user passed focus topics as an argument, give those topics the most detail. Use exactly these sections:

```markdown
# Session — YYYY-MM-DD

## Goal
[What this session set out to do, one or two sentences]

## What happened
[The narrative in a few bullets: what was built, fixed, decided, or discovered]

## Decisions & rationale
[Each decision with its WHY — a decision without rationale becomes a mystery.
If decision records were created or updated this session, list their `decisions/` paths]

## Files changed
[From git: the meaningful changes, not every path]

## Worth remembering
[Candidates for the learn skill: patterns, quirks, root causes — or "none"]

## Open threads
[Unfinished work, unanswered questions, what the next session should pick up]
```

### Step 4 — Write the log
Append to `${MEMORY_DIR}/$(date +%Y-%m-%d).md`. If the file already has an entry from earlier today, add a new `# Session — YYYY-MM-DD (2)` heading rather than overwriting.

Success: the file exists and contains today's summary. Read it back to confirm.

### Step 5 — Promote durable knowledge
For each item under "Worth remembering", ask: is this a reusable principle or a one-off fact? Reusable principles go to `MEMORY.md` via the `learn` skill now — session logs get archived, `MEMORY.md` is what future sessions read first.

## When to run
- Before `/compact` (the pre-compact hook reminds you)
- At the end of any session that made decisions or discoveries
- Skip for trivial sessions — an empty summary is noise, not memory
