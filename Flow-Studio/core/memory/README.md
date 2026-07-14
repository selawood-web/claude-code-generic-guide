# Memory Layer

## Purpose
Responsible for long-term and short-term knowledge retention across sessions.

## Memory Types

| Type | Scope | Location | Contents |
|------|-------|----------|----------|
| **Global** | All projects | `~/.claude/memory/MEMORY.md` | Universal engineering principles, personal preferences |
| **Workspace** | Current project | `~/.claude/memory/<project>/MEMORY.md` | Project architecture, conventions, discovered patterns |
| **Session** | Single session | `~/.claude/memory/<project>/sessions/` | Session summaries, debugging logs |

## Memory Operations

### Write (explicit)
```
remember: [fact] — tags: #category
remember globally: [universal principle] — tags: #category
```

### Write (automatic)
- Session end: auto-save metadata summary
- Pre-compaction: `/flush` triggered by hook
- Manual: `/flush` for rich LLM-generated summary

### Read (automatic)
- First turn injection: relevant memory is loaded at session start
- After compaction: memory searched again to recover lost context

### Read (explicit)
```
what do you remember about [topic]?
search memory for [keyword]
/memory   ← browse all memory files
```

### Consolidate
```
/dream    ← reorganizes scattered memory into coherent topics
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
