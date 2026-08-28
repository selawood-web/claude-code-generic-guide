---
name: ship
description: Run the whole finish line in one command — validate, commit, push, open the pull request, watch CI to green, and merge. Typing it is the owner's merge authorization. Use when the user says "ship", "ship it", "finish and merge", or wants the complete commit-to-merge cycle done automatically.
when-to-use: ship, ship it, finish and merge, land it, commit push pr merge, run the whole cycle
allowed-tools: powershell, bash
argument-hint: "[optional: no-merge | commit message hint]"
---

# Ship Skill

## Goal
Collapse the finish line into one word. `/ship` takes verified work from the working
tree all the way to merged: gate → commit → push → PR → green CI → merge — reporting
once at the end instead of asking at every step.

**Authorization model:** the charter's invariant stands — main changes only through
a pull request the owner merges. Typing `/ship` *is* the owner's merge instruction
for this cycle. `/ship no-merge` stops after the PR opens (CI still watched).

Related skills (referenced, not duplicated): `commit` writes the message, `pr` opens
the pull request, `debug` handles a red CI, `git-steward` owns the standing branch
rules, `deploy-steward`'s execution obligation still applies to the milestone.

## Process

### Step 1 — Preflight (abort early, loudly)
- There are changes to ship (staged or unstaged); otherwise say so and stop.
- Current branch is a working branch — never main/master (git-steward boundary).
- The quality gate for the change has passed; run the repo's fast checks now
  (validator, lint, tests — whatever this project's gate is). Red gate = nothing
  ships; fix first.
- The branch contains only this session's work. Someone else's commits on it →
  stop and ask.

### Step 2 — Commit
Per the `commit` skill: inspect the diff, conventional message, why in the body.
An argument that isn't `no-merge` is a hint for the message's subject.

### Step 3 — Push
`git push -u origin <branch>` with retry on network failure (backoff 2s/4s/8s/16s).

### Step 4 — Pull request
- Existing open PR for this branch → the push already updated it; refresh its
  title/body if the scope grew.
- No PR → open one per the `pr` skill (structured description, template honored).

### Step 5 — Drive CI to green
Watch the PR's checks. Red → root-cause and fix (`debug`), push, re-check — do not
merge around a failure, do not skip or disable checks. A failure that can't be fixed
this cycle → stop, report exactly what blocks, leave the PR open.

### Step 6 — Merge (unless `no-merge`)
Merge only when ALL hold:
- CI green on the current head
- No merge conflict
- No human review requesting changes (a pending changes-requested review always
  outranks `/ship` — address it first)

Merge with the repo's convention (merge commit titled per house style unless the
repo says otherwise). Then confirm the merge landed.

### Step 7 — Report and reset
One summary: what merged, the merge commit, anything skipped or left open. Restart
the working branch from the updated default branch if more work is coming. If the
session's decision or memory work touched `decisions/`, note it per `/flush` rules.

## Boundaries that never move
- Red CI, conflicts, or a changes-requested review → no merge, no exceptions.
- Never force-push, never bypass the PR, never merge someone else's unreviewed work.
- `/ship` merges one cycle; it is not standing permission for future merges.

## Anti-Patterns to Avoid

| Anti-pattern | Correct approach |
|--------------|-----------------|
| Shipping around a red gate | Red gate = stop; fix, then ship |
| Merging with checks still running | Green on the current head, then merge |
| Treating one `/ship` as blanket merge consent | Each cycle needs its own `/ship` |
| Asking at every step anyway | One command, one final report — that is the point |
| Quietly widening the PR mid-ship | Ship what was asked; new scope is a new cycle |

## Knowledge Extraction
```
remember: [repo] ships via [merge convention], CI gate is [checks] — reason: /ship must match the house rules
```
