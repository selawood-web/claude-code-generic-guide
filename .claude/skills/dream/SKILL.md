---
name: dream
description: Consolidate accumulated session logs and scattered memory entries into an organized, deduplicated knowledge base. Use when the user says "dream", "consolidate memory", "clean up memory", "organize what you know", or after five or more sessions without consolidation.
when-to-use: dream, consolidate memory, organize memory, dedupe knowledge, memory cleanup, weekly consolidation
allowed-tools: powershell, bash
argument-hint: "[optional: project slug, defaults to the current repository]"
purpose: Consolidate session logs into the knowledge base
---

# Dream Skill — Memory Consolidation

## Memory Budget
`MEMORY.md` loads at session start, so it is paid for in every session's context.
Target: keep it under ~8 KB / 200 lines. When consolidation would push it over,
move the oldest or least-referenced entries into topic files beside it
(`<topic>.md`, loaded on demand) and leave a one-line index pointer in
`MEMORY.md`. Nothing is deleted — the budget forces structure, not loss.

## Purpose
Session logs accumulate fragments; `MEMORY.md` should hold organized knowledge. This skill merges the fragments into the knowledge base, removes duplication, and flags contradictions — without ever deleting source material.

## Steps

### Step 1 — Inventory
```bash
PROJECT_SLUG=${1:-$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")}
MEM="${HOME}/.claude/memory/${PROJECT_SLUG}"
ls -la "$MEM/sessions/" 2>/dev/null
wc -l "$MEM/MEMORY.md" 2>/dev/null
```
If there are fewer than two session logs, stop: there is nothing worth consolidating yet. Say so in one line.

### Step 2 — Read everything
Read `MEMORY.md` and every file in `sessions/` (skip `sessions/archive/`). Build one working list of facts, decisions, and patterns.

### Step 3 — Merge, don't just append
For the working list:
- **Deduplicate** — when the same fact appears twice, keep the version that carries rationale; discard the bare restatement.
- **Group** by the standard sections: Architecture Decisions, Conventions, Current State, Known Issues, Key Commands, Team Agreements.
- **Contradictions** — when two entries conflict (a decision was reversed, a convention changed), keep the newer one and note the reversal: `(supersedes: [old], changed because [why])`. Never silently drop either side.
- **Staleness** — anything that may no longer be true gets marked `[VERIFY: may have changed since YYYY-MM-DD]`, not deleted.

### Step 4 — Rewrite MEMORY.md
Write the consolidated version to `$MEM/MEMORY.md`. "Current State" describes now, not history — history lives in the session logs.

Success: the file reads as a coherent reference, not a diary.

### Step 5 — Archive the processed logs
```bash
mkdir -p "$MEM/sessions/archive"
mv "$MEM"/sessions/*.md "$MEM/sessions/archive/" 2>/dev/null
```
Nothing is deleted — consolidation must be reversible. Archived logs remain searchable.

### Step 6 — Report
One short report: entries before → after, duplicates merged, contradictions flagged, entries marked for verification. If any `[VERIFY:]` marks were added, list them so the user can confirm or correct now.

## Calibration (run with every dream)
Consolidation is also when oversight gets tuned. Scan `decisions/` records and
the session logs for two signals:
- **Overridden recommendations** — the owner picked differently than proposed.
  Extract what criterion or weight the recommendation got wrong.
- **Unnecessary escalations** — confirmations asked where the owner's answer was
  an obvious "yes, proceed". Extract what made them safe, so similar cases take
  the cheap path next time.

Write what's learned to memory as calibration entries
(`remember: [adjustment] — reason: [the override/escalation that taught it]`).
The inverse holds too: an escalation that *caught* something stays exactly as
strict as it is.

## Cadence
Weekly, or after five or more session logs accumulate. Running it too often wastes effort on nothing; never running it is how memory rots into noise.
