---
name: learn
description: Explicitly capture a reusable pattern, decision, or insight to memory so it persists across sessions. Use when the user says "learn!", "remember this", "save this pattern", "this is important", or after discovering something non-obvious.
when-to-use: learn, remember, save pattern, keep this, important discovery, lesson learned
allowed-tools: powershell, bash
argument-hint: "[what to learn/remember]"
---

# Learn Skill — Knowledge Capture

## Purpose
Capture knowledge that would take time to re-discover. This is the skill that makes every future session smarter.

## What is worth capturing?

**High value (always capture)**
- Architecture decisions and the reasoning behind them
- Non-obvious bugs and their root causes
- API quirks and undocumented behaviors
- Performance findings with measurements
- Security patterns specific to this codebase
- Team conventions not in written docs

**Medium value (capture if reusable)**
- Debugging workflows that worked
- Useful command sequences
- Patterns that solved a recurring problem

**Low value (skip)**
- How basic syntax works
- Things documented in official docs
- One-off tasks not likely to repeat

## Steps

### Step 1 — Extract the principle
Don't just record what happened. Extract the **reusable rule**:

❌ "Fixed the auth bug by adding a null check on user.id"
✅ "Always validate JWT payload fields individually — JWT decode never throws for missing claims, it just returns undefined"

### Step 2 — Categorize and tag
Categories: `Architecture`, `Code Pattern`, `Debugging`, `Security`, `Performance`, `Tooling`, `Workflow`, `Conventions`

Tags: technology names, domain areas (e.g., `#auth`, `#database`, `#typescript`, `#react`)

### Step 3 — Write to memory

**Project-specific knowledge:**
```
remember: [concise fact with context] — tags: #category #tech
```

**Global pattern (applies across projects):**
```
remember globally: [principle] — tags: #category
```

**After a productive session:**
```
/flush
```
This generates a structured LLM summary of the session and saves it to the session log.

**After many sessions accumulate:**
```
/dream
```
Consolidates scattered memory entries into an organized knowledge base.

### Step 4 — Verify it was saved
```
what do you remember about [topic]?
```

## Format for memory entries

```markdown
## [Category]

### [Topic]
**Principle**: [The reusable rule in one sentence]
**Context**: [Where/when this applies]
**Evidence**: [What led to this discovery]
**Tags**: #tag1 #tag2

---
```

## Session knowledge harvest
At the end of every significant session, run through these prompts:
1. "What would I need to know to restart this work from scratch?"
2. "What surprised me today?"
3. "What would I do differently next time?"
4. "What conventions were established that the next engineer needs to know?"
