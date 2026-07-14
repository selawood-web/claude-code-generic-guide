# Knowledge Extraction & Storage Rules

## What to Extract

Extract when ANY of these are true:
- A non-obvious architectural decision was made
- A bug took significant time to diagnose — extract the root cause pattern
- A technology limitation was discovered that isn't in the docs
- A convention was established (naming, structure, pattern)
- A "this is how we do it here" pattern emerged
- A performance finding was measured (not assumed)

## What NOT to Extract
- Basic syntax or well-documented framework usage
- One-off facts specific to a single task with no future relevance
- Sensitive data (credentials, PII, internal system names without context)

## Extraction Format

```markdown
## [Category]

### [Topic Title]
**Principle**: [The reusable rule in one sentence]
**Context**: [When and where this applies]
**Rationale**: [Why this decision/pattern — the reasoning, not just the fact]
**Example**: [Optional: brief code or pseudocode illustration]
**Tags**: #[technology] #[domain] #[category]

---
```

### Categories
- `Architecture` — structural and design decisions
- `Code Pattern` — reusable implementation patterns
- `Debugging` — bug classes and diagnosis approaches
- `Security` — security patterns and vulnerability classes
- `Performance` — measured optimizations
- `Tooling` — dev tools, build, CI/CD
- `Conventions` — team/project agreements
- `Domain` — business domain knowledge

## Storage Targets

| Target | What goes here |
|--------|---------------|
| `~/.claude/memory/MEMORY.md` | Universal principles applicable across all projects |
| `~/.claude/memory/<project>/MEMORY.md` | Project-specific decisions, conventions, findings |
| Session logs (via `/flush`) | Full session context for future retrieval |

## Extraction Trigger Phrases
The AI should proactively extract when it hears:
- "we decided to..."
- "the reason is..."
- "it turns out that..."
- "the trick is..."
- "never do X because..."
- "always use Y when..."
- "remember to..."

