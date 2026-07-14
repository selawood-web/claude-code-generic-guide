---
name: standup
description: Generate a concise standup report or session summary from recent work. Use when the user asks for a "standup", "daily summary", "what did we do", "session recap", or "progress report".
when-to-use: standup, daily summary, session recap, what did we do, progress report, what happened
allowed-tools: powershell, bash
argument-hint: "[optional: time range or focus area]"
---

# Standup / Session Summary Skill

## Purpose
Produce a clear, concise report of what was done, the current state, and what comes next.

## Steps

### Step 1 — Gather session data
```
# Recent git activity
git --no-pager log --oneline --since="24 hours ago"
git --no-pager diff --stat HEAD~5..HEAD

# Open PRs
gh pr list --author @me

# Issues closed
gh issue list --state closed --limit 10
```

### Step 2 — Check the chronicle (if available)
```
/chronicle
```
This retrieves the session history for a richer summary.

### Step 3 — Write the standup

**Format:**

```markdown
## Standup — [Date]

### ✅ Done
- [What was completed]
- [What was merged/deployed]

### 🔄 In Progress
- [What is currently underway]
- [Blockers if any]

### 🔜 Next
- [What's coming next]
- [Decisions needed from others]

### 💡 Notes
- [Anything the team needs to know]
- [Risks or dependencies surfaced]
```

### Step 4 — Extract session learnings
Before closing the report, ask:
- Were any new patterns or decisions made? → Use `learn` skill to capture them.
- Is there a good time to run `/flush`? → Do it now if yes.

## Standup quality checks
- [ ] Done items are specific and verifiable (not "worked on X")
- [ ] In-progress items have a clear next action
- [ ] Blockers are named precisely (not "waiting on things")
- [ ] Total length: under 10 bullet points for a normal day
