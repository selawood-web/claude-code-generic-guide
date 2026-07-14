# Generic AI Development Infrastructure

A complete, generic infrastructure for software development with AI coding assistants (Claude Code, GitHub Copilot CLI, and compatible tools). Designed to make every session smarter than the last through persistent knowledge, structured workflows, and professional engineering standards.

---

## What This Is

A **plug-in infrastructure layer** you drop into any project to get:
- A senior principal engineer mindset embedded in your AI assistant
- 12 production-ready skill workflows (commit, PR, code review, architecture, etc.)
- Automatic knowledge capture across sessions — context that accumulates over time
- Self-criticism and quality gates built into every workflow
- A seeded knowledge base with architecture patterns, engineering principles, and common pitfalls

---

## Quick Start

### 1. Drop AGENTS.md into your project root
```bash
cp AGENTS.md /path/to/your-project/AGENTS.md
```
This immediately gives your AI assistant professional engineering behavior.

### 2. Copy the .claude/ directory
```bash
cp -r .claude/ /path/to/your-project/.claude/
```
This installs all 12 skill workflows.

### 3. Enable memory (one-time setup)
```toml
# ~/.claude/config.toml
[memory]
enabled = true
```
Or start with: `claude --experimental-memory`

### 4. Seed your global memory
```bash
# Copy the global memory template
cp MEMORY.md ~/.claude/memory/MEMORY.md
```
This pre-loads engineering wisdom into every future session.

### 5. Use the session protocol
Read `session-protocol.md` to understand how to start, manage, and end sessions to maximize knowledge retention.

---

## Repository Structure

```
claude-code-generic-guide/
│
├── AGENTS.md                    ← Master AI behavior rules (copy to your project)
├── MEMORY.md                    ← Global memory seed template
├── session-protocol.md          ← How to manage sessions for knowledge persistence
│
├── .claude/                     ← AI tooling configuration
│   ├── config.toml              ← Memory, skills, and compaction settings
│   ├── skills/                  ← 12 reusable skill workflows
│   │   ├── commit/              ← Conventional commits
│   │   ├── pr/                  ← Pull request creation
│   │   ├── code-review/         ← Systematic code review
│   │   ├── architecture/        ← System architecture design
│   │   ├── requirements/        ← Requirements gathering
│   │   ├── testing/             ← Test suite generation
│   │   ├── debug/               ← Systematic debugging
│   │   ├── refactor/            ← Safe refactoring
│   │   ├── learn/               ← Knowledge capture
│   │   ├── standup/             ← Session summaries
│   │   ├── deploy/              ← Deployment workflow
│   │   └── security-review/     ← Security audit
│   └── hooks/                   ← Session lifecycle hooks
│
├── Flow-Studio/                 ← Complete AI orchestration system
│   ├── core/
│   │   ├── system/              ← Core system prompt (Workflow Studio)
│   │   ├── orchestrator/        ← Decision engine and behavior rules
│   │   ├── critics/             ← Code and architecture critics
│   │   ├── memory/              ← Memory layer documentation
│   │   └── knowledge-base/      ← Knowledge extraction rules + seeded entries
│   └── skills/                  ← Flow-Studio skill definitions
│
└── docs/                        ← Full Claude Code / Copilot CLI reference (22 chapters)
    ├── 01-getting-started.md
    ├── ...
    └── 22-permissions-and-safety.md
```

---

## Available Skills

| Skill | Invoke | Purpose |
|-------|--------|---------|
| `commit` | `/commit` | Conventional commits with staged diff review |
| `pr` | `/pr` | PR creation with structured description |
| `code-review` | `/code-review` | Multi-dimension review with severity levels |
| `architecture` | `/architecture` | System design with trade-off analysis |
| `requirements` | `/requirements` | Vague idea → actionable spec |
| `testing` | `/testing` | Test suite generation (unit/integration/E2E) |
| `debug` | `/debug` | Systematic root cause analysis |
| `refactor` | `/refactor` | Safe refactoring with regression safety |
| `learn` | `/learn` | Explicit knowledge capture to memory |
| `standup` | `/standup` | Session summary / daily report |
| `deploy` | `/deploy` | Deployment with pre-flight checklist |
| `security-review` | `/security-review` | OWASP-based security audit |

---

## Knowledge Persistence System

The knowledge system has three layers:

### 1. Automatic (built-in)
- Session metadata saved at session end
- Memory injected at session start
- Pre-compaction flush triggered by hook

### 2. Semi-automatic (you trigger it)
- `/flush` — write an LLM-generated session summary before compacting or closing
- `/dream` — consolidate scattered session logs into organized topics (run weekly)
- `learn` skill — capture a specific pattern or decision

### 3. Manual (curated)
- `MEMORY.md` in the repo — project conventions and decisions
- `~/.claude/memory/MEMORY.md` — global engineering principles
- Knowledge base entries in `Flow-Studio/core/knowledge-base/entries/`

---

## Customizing for Your Project

### Project conventions (in AGENTS.md)
Edit the "Project Conventions" section of `AGENTS.md` with your actual stack:
```markdown
## Project Conventions
- Language: TypeScript (strict mode)
- Framework: Next.js 14
- Database: PostgreSQL via Prisma
- Tests: Vitest
- Branch: feature/<ticket-id>-description
```

### Adding skills
Create `.claude/skills/<name>/SKILL.md` with YAML frontmatter:
```markdown
---
name: my-workflow
description: [trigger description for auto-invocation]
---
# Steps
...
```

### Capturing learnings
After any significant session:
```
/flush           ← save session summary
/learn           ← capture key patterns
/dream           ← consolidate (weekly)
```

---

## Claude Code / Copilot CLI Reference

Full 22-chapter documentation in `/docs/`:
- Sessions, memory, skills, agents, MCP servers, plugins, hooks, and more
- See `docs/index.md` for the full table of contents

---

## Philosophy

> Every session should be smarter than the last.

This infrastructure is built around one principle: **knowledge should compound**. Each debugging session, architecture decision, and discovered pattern is an asset. The goal is to make the AI's context richer over time — so that by month 3, it starts sessions knowing the project's architecture, conventions, and history, rather than starting from scratch every time.

