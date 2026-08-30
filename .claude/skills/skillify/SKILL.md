---
name: skillify
description: Capture a workflow completed in this session as a new reusable skill in .claude/skills/. Use when the user says "skillify", "make this a skill", "capture this workflow", "save this as a skill", or after finishing a multi-step process the team will repeat.
when-to-use: skillify, make this a skill, capture workflow, new skill, save procedure
argument-hint: "[optional: name for the new skill]"
allowed-tools: powershell, bash
purpose: Capture a completed workflow as a new skill
---

# Skillify Skill — Workflow to Skill

## Purpose
A workflow that worked is an asset; re-deriving it next month is waste. This skill turns the procedure just performed into a skill file the assistant can run next time.

## Steps

### Step 1 — Check it deserves to be a skill
- Will this be repeated? One-off tasks stay in the session log (`/flush`), not the skill catalog.
- Does an existing skill already cover it? `ls .claude/skills/` — extending an existing skill beats creating a near-duplicate.

If either check fails, say so in one line and stop.

### Step 2 — Extract the procedure
From the session, write down:
- The steps actually taken, in order, with the commands that worked
- The decisions made along the way and what drove them
- What went wrong on the first try — the final skill should encode the corrected path, and warn about the trap

### Step 3 — Name it
Kebab-case, verb-first or domain-first, matching the catalog style (`ccgg-code-review`, `ccgg-security-review`). The name is how it will be invoked: `/name`.

### Step 4 — Write the skill file
Create `.claude/skills/<name>/SKILL.md` with the house frontmatter — all five keys:

```markdown
---
name: <name>
description: <What it does. Use when the user says "...", "...", or <situation>.>
when-to-use: <comma-separated trigger phrases>
allowed-tools: powershell, bash
argument-hint: "[what an argument means, or omit the brackets' content]"
purpose: <one-line catalog text for the generated tables>
---

# <Title>

## Purpose
[One or two sentences]

## Steps

### Step 1 — <action>
[Instructions, commands in fenced blocks]
Success: [how to know this step worked]

...
```

Every step gets a success criterion. A step you cannot verify is a step that silently fails.

### Step 5 — Validate
- Frontmatter parses: opens and closes with `---`, all house keys present (including `purpose`, the one-line catalog text). A malformed header does not error — the skill just silently never loads.
- Walk the steps once against the session that produced them: would following this file reproduce the result?

### Step 6 — Register and commit
- New skills load at the next session start — say so, so the user does not expect `/name` to work immediately.
- Run `python3 tools/catalog.py --write` — it regenerates the `AGENTS.md` and `README.md` tables and every stated skill count from the frontmatter. Only the long-form `USER-MANUAL.md` entry is still written by hand.
- Commit it (`/commit`) — a skill that lives only in one checkout helps one person once.
