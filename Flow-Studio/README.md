# Flow-Studio — AI Software Engineering Operating System

Flow-Studio is a complete AI orchestration system for professional software development. It defines the identity, behavior, decision logic, critics, memory management, and skills for an AI that acts as a Senior Principal Engineer.

---

## Architecture

```
Flow-Studio/
│
├── core/
│   ├── system/
│   │   └── core-prompt.md      ← Master identity & rules (start here)
│   │
│   ├── orchestrator/
│   │   ├── behavior.md         ← Skill dispatch & project state management
│   │   └── decision-engine.md  ← Decision tree for mode selection
│   │
│   ├── critics/
│   │   ├── code-critic.md      ← Code review rubric (6 dimensions, 4 severity levels)
│   │   └── architecture-critic.md ← Architecture review (7 dimensions, checklist)
│   │
│   ├── memory/
│   │   └── README.md           ← Memory layer: types, operations, quality rules
│   │
│   └── knowledge-base/
│       ├── extraction-rules.md ← What to capture, format, and storage targets
│       └── entries/
│           ├── architecture-patterns.md
│           ├── engineering-principles.md
│           └── common-pitfalls.md
│
└── skills/
    ├── architecture-design/    ← System design workflow
    ├── code-generation/        ← Production-ready code generation
    ├── requirements-gathering/ ← Vague idea → specification
    └── testing/               ← Test strategy and generation
```

---

## How It Connects to `.claude/`

Flow-Studio defines the **thinking system**. The `.claude/` directory holds the **executable skills** that the thinking system invokes.

| Flow-Studio | .claude/skills/ |
|-------------|-----------------|
| `orchestrator/behavior.md` → decides to invoke | `commit/SKILL.md` → executes |
| `critics/code-critic.md` → review rubric | `code-review/SKILL.md` → review workflow |
| `memory/README.md` → memory protocol | `learn/SKILL.md` → capture workflow |

---

## Core Operating Modes

| Mode | Trigger | Primary Files |
|------|---------|---------------|
| Architect | "design", "how should I structure" | architecture-design skill + architecture-critic |
| Builder | "implement", "write code" | code-generation skill + code-critic |
| Reviewer | "review", "check my code" | code-review skill + code-critic |
| Debugger | "bug", "error", "not working" | debug skill |
| Planner | "I want to build", vague idea | requirements-gathering skill |

---

## Knowledge Base

The `knowledge-base/entries/` directory contains seeded engineering wisdom:

- **architecture-patterns.md** — Monolith vs. microservices, CQRS, repository pattern, hexagonal architecture
- **engineering-principles.md** — Naming rules, error handling, SRP, composition, fail fast, immutability
- **common-pitfalls.md** — N+1 queries, race conditions, JWT attacks, IDOR, migration mistakes

These entries are indexed when memory is enabled and injected into sessions automatically.

---

## Quick Reference

Start here: `core/system/core-prompt.md`
Decision logic: `core/orchestrator/behavior.md`
Code quality: `core/critics/code-critic.md`
Architecture quality: `core/critics/architecture-critic.md`
Knowledge rules: `core/knowledge-base/extraction-rules.md`
