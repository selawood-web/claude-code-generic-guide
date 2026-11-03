---
name: flush
description: "Write a structured session summary to the committed memory log."
when_to_use: flush, save this session, session summary, before compact, end of session
argument-hint: "[optional: topics to emphasize in the summary]"
purpose: Structured session summary written to the memory log
---

# Flush Skill — Session Summary to Memory

## Purpose
Persist what happened in this session before it is lost to compaction or session end. This is the write-side of the memory system: `/flush` records, future sessions recall.

## Steps

### Step 1 — Resolve the memory location
Project memory lives in the repository, so it survives a container that is thrown away
and reaches every clone through ordinary git.
```bash
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
MEMORY_DIR="${ROOT}/memory/sessions"
mkdir -p "$MEMORY_DIR"
LOG="${MEMORY_DIR}/$(date -u +%Y-%m-%d-%H%M%S).md"
```
Success: the directory exists and is writable.

### Step 2 — Gather the session's facts
```bash
git --no-pager log --oneline -10
git --no-pager diff --stat HEAD~5 2>/dev/null || git --no-pager diff --stat
git --no-pager status --short
# Skills used since the last flush, from the machine-local log skill-usage.sh writes
USAGE="${HOME}/.claude/memory/$(basename "$ROOT")/skill-usage.log"
[ -f "$USAGE" ] && awk '/^-- flushed/ {split("", n); next} {n[$2]++} END {for (k in n) print n[k], k}' "$USAGE" | sort -rn
```
Success: you can list what was changed, committed, and left open, and which skills ran.

### Step 3 — Compose the summary
Write from the conversation, not just from git. If the user passed focus topics as an argument, give those topics the most detail. Quote third-party text (issues, PR bodies, READMEs, CI output) as quotes, never as decisions. Use exactly these sections:

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

## Skills used
[From the tally above, one per line as `name ×count`, or "none recorded"]
```

### Step 4 — Write and commit the log
Write the summary to `$LOG` — one file per flush, named by its UTC stamp, so two sessions
on two branches never edit the same file. The log is committed and readable by everyone
with access to the repository: no secret, credential, token or personal data goes in it
(AGENTS.md, *Code Quality Standards*). `tools/validate.py` fails a tree whose `memory/`
holds a credential-shaped string; personal data it cannot see, so that part stays yours.

Then commit that file alone, on the session's own branch:
```bash
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
DEFAULT="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')"
if [ -n "$BRANCH" ] && [ "$BRANCH" != "HEAD" ] && [ "$BRANCH" != "${DEFAULT:-master}" ] && [ "$BRANCH" != "main" ]; then
  git add -- "$LOG" && git commit -q -m "docs(memory): session log $(basename "$LOG" .md)" -- "$LOG"
fi
```
Then mark the usage log, so the next flush counts only what ran after this one:
```bash
[ -f "$USAGE" ] && echo "-- flushed $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$USAGE"
```
On the default branch or a detached HEAD the log is written but not committed — the
branch boundary holds — and the report says so. This skill never pushes: the commit
travels with the branch's next push, which in a cloud session has to happen before the
container ends.

Success: the file exists, contains this session's summary, and `git log -1 -- "$LOG"`
shows it committed (or the report says why not). Read it back to confirm.

### Step 5 — Promote durable knowledge
For each item under "Worth remembering", ask: is this a reusable principle or a one-off fact? Reusable principles go to memory via the `learn` skill now — session logs get archived by `/dream`, and the consolidated `memory/PROJECT-MEMORY.md` is what future sessions read first.

## When to run
- Before `/compact` — the pre-compact hook can only shape the summary, not run this skill; flush first, then compact
- When the flush guard stops a reply because the session grew ~150k tokens since it was last saved (`.claude/hooks/flush-guard.sh`)
- At the end of any session that made decisions or discoveries
- Skip for trivial sessions — an empty summary is noise, not memory
