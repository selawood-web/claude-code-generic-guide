# Session Management Protocol

How to start, run, and end sessions so that knowledge accumulates over time instead of being lost.

---

## The Knowledge Decay Problem

Without intentional session management, every AI session starts from zero:
- Architecture decisions are re-explained
- Bug root causes are re-discovered
- Conventions are re-established
- Context is rebuilt from scratch

The goal of this protocol is to make each session **smarter than the last**.

---

## Session Start Checklist

When starting a new session in this repository:

1. **Load context** (automatic if memory is enabled)
   ```
   /memory   ← review what was remembered from previous sessions
   what do you remember about this project?
   ```

2. **State your goal** for this session explicitly:
   > "Today I want to: [specific goal]"

3. **Review open work** from last session:
   ```
   gh issue list --assignee @me
   git --no-pager log --oneline -10
   git --no-pager stash list
   ```

4. **Check the plan** if one exists:
   ```
   /plan   ← or review plan.md in the session folder
   ```

---

## During a Session: Knowledge Capture Moments

Capture knowledge in real-time, not just at the end. Use these trigger moments:

| Trigger | Action |
|---------|--------|
| "It turns out X..." | `remember: [X] — reason: [why it matters]` |
| A bug is solved | Capture root cause with `learn` skill |
| Architecture decision made | `remember: [decision] — rationale: [why]` |
| Convention established | Write to AGENTS.md or memory |
| Third-party API quirk found | `remember: [API] quirk — [behavior] — tags: #api #[name]` |
| Something took too long to debug | Document the diagnosis path |

---

## Mid-Session: Context Management

### Before context fills up
- Run `/compact [focus]` with a description of what to preserve:
  ```
  /compact focus on the authentication module changes and the decision to use JWT with RS256
  ```
- The focus text helps the LLM preserve the most important context.

### After compaction
- Memory is automatically searched to re-inject relevant context.
- Verify: `what do you remember about [current topic]?`

---

## Session End Protocol

Before closing any productive session:

### Step 1 — Flush memory
```
/flush
```
This generates an LLM-written structured summary: topics covered, decisions made, files changed, tool usage. Indexed for future search.

### Step 2 — Capture significant learnings
For each important discovery or decision:
```
/learn
```
Or use the `learn` skill directly.

### Step 3 — Update project memory
If conventions or architecture were established:
```
remember: [project convention] — [what and why]
```

### Step 4 — Consolidate (weekly or after 5+ sessions)
```
/dream
```
Reorganizes scattered session logs into a coherent, deduplicated knowledge base.

### Step 5 — Commit open work
```
/commit
```
Never leave uncommitted work that would be confusing to re-discover next session.

---

## Resume Protocol

When resuming work after a break:

```bash
# Start Claude Code and resume the last session
claude -c   # continue most recent session for current directory

# Or: resume a specific session
claude --resume <session-id>

# Or: browse sessions
/load   ← in the TUI
```

On resume:
1. Memory is injected automatically.
2. Check what was happening: `what were we working on?`
3. Verify git state: `git --no-pager status && git --no-pager log --oneline -5`

---

## Multi-Session Project Protocol

For projects spanning many sessions:

### Project MEMORY.md
Location: `~/.claude/memory/<project-slug>/MEMORY.md`

Maintain these sections:
```markdown
## Architecture Decisions
[Key design decisions and rationale]

## Conventions
[Naming, structure, patterns agreed upon for this project]

## Current State
[Where the project is now — updated each session]

## Known Issues
[Bugs, technical debt, limitations — updated as discovered]

## Key Commands
[Project-specific commands that are non-obvious]

## Team Agreements
[Decisions made with stakeholders]
```

### Session Log Structure
Each `/flush` creates an entry in:
`~/.claude/memory/<project>/sessions/YYYY-MM-DD.md`

These are searchable: `search memory for "authentication bug"`

---

## Headless / Automation Sessions

When running automated sessions:

```bash
# Create a named session that persists context
claude -p "Run the full test suite and fix any failures" -s "test-fix-$(date +%Y%m%d)"

# Resume it if the task is long-running
claude -p "Continue fixing the remaining failures" -r "test-fix-$(date +%Y%m%d)"
```

For CI/CD automation:
```bash
claude -p "Review this PR for security issues: $(gh pr diff)" \
  --output-format json \
  | jq '.result'
```

---

## Knowledge Quality Over Time

The accumulation of knowledge should follow this progression:

**Week 1**: Project architecture and setup decisions stored.
**Week 2**: First bug patterns and API quirks documented.
**Month 1**: Team conventions are stable and captured.
**Month 3**: Deep domain knowledge is indexed.
**Month 6+**: AI starts sessions with substantial project context — "I know this codebase."

The key metric: **how much time is spent re-explaining context** vs. **doing new work**. This should trend toward zero over time.
