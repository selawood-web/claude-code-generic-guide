# Memory Layer

## Purpose
Responsible for long-term and short-term knowledge retention across sessions.

## Memory Types

| Type | Scope | Location | Contents |
|------|-------|----------|----------|
| **Global** | All projects | `~/.claude/CLAUDE.md` | Universal engineering principles, personal preferences |
| **Auto memory** | Current project | `~/.claude/projects/<project>/memory/` | Notes Claude writes itself; `MEMORY.md` index loaded every session |
| **Session logs** | Session history | `~/.claude/memory/<project>/sessions/` | Summaries written by `/flush`, consolidated by `/dream` |

## Memory Operations

### Write (explicit)
```
remember: [fact] — tags: #category
remember globally: [universal principle] — tags: #category
```

### Write (automatic)
- Auto memory: Claude saves notes itself during the session ("Saved 2 memories")
- Pre-compaction: the PreCompact hook reminds to run `/flush`
- Manual: `/flush` for a rich structured session summary

### Read (automatic)
- Session start: `~/.claude/CLAUDE.md`, the project `CLAUDE.md`, and the
  auto-memory `MEMORY.md` index are loaded
- After compaction: the project-root `CLAUDE.md` is re-injected; topic files
  are re-read on demand

### Read (explicit)
```
what do you remember about [topic]?
search memory for [keyword]
/memory   ← browse all memory files
```

### Consolidate
```
/dream    ← reorganizes scattered session logs into coherent topics
```

## Memory Quality Rules

**Good memory entries:**
- Specific and actionable
- Contain the rationale, not just the fact
- Tagged for searchability
- Written as durable statements (not "today we decided X" but "X is the convention because Y")

**Bad memory entries:**
- Vague ("we use React")
- Without context (the fact without the why)
- Outdated but not marked as such
- Sensitive data (credentials, PII)

## Staleness Management
When memory content may be outdated:
- Mark it: `[VERIFY: this may have changed since <date>]`
- Update or delete when verified
- Use `/dream` to consolidate and remove duplicate/stale entries

## Extraction rules
See canonical `../knowledge-base/extraction-rules.md`.
