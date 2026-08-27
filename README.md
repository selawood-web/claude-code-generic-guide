# Generic AI Development Infrastructure

A complete, generic infrastructure for software development with AI coding assistants (Claude Code, GitHub Copilot CLI, and compatible tools). Designed to make every session smarter than the last through persistent knowledge, structured workflows, and professional engineering standards.

---

## See It In Action

→ **[demo/WALKTHROUGH.md](demo/WALKTHROUGH.md)** — A full session walkthrough: debugging a JWT auth bug using `/debug`, `/code-review`, `/commit`, and `/learn`, from bug report to committed fix in ~17 minutes.

---

## What This Is

A **plug-in infrastructure layer** you drop into any project to get:
- A senior principal engineer mindset embedded in your AI assistant
- 17 production-ready skill workflows (commit, PR, code review, architecture, code generation, memory capture, etc.)
- Automatic knowledge capture across sessions — context that accumulates over time
- Self-criticism and quality gates built into every workflow
- A seeded knowledge base with architecture patterns, engineering principles, and common pitfalls

---

## Quick Start

### 1. Drop AGENTS.md and CLAUDE.md into your project root
```bash
cp AGENTS.md CLAUDE.md /path/to/your-project/
```
This gives your AI assistant professional engineering behavior. Both files are
needed: Claude Code reads `CLAUDE.md` (which imports `@AGENTS.md`), while other
assistants read `AGENTS.md` directly — without the `CLAUDE.md` bridge, Claude
Code never loads the rules at all.

### 2. Copy the .claude/ directory
```bash
cp -r .claude/ /path/to/your-project/.claude/
```
This installs all 17 skill workflows, their critic and strategy references, and the hook wiring (`settings.json`).

### 3. Memory needs no enabling
Claude Code's auto memory is on by default: Claude keeps per-project notes at
`~/.claude/projects/<project>/memory/` and loads the `MEMORY.md` index there at
the start of every session. Curated instructions load from `CLAUDE.md` (which
imports `AGENTS.md` here) and from `~/.claude/CLAUDE.md`. On top of that, this
repo's `/flush` and `/dream` skills maintain the session-log layer. Nothing to
switch on.

### 4. Seed your global memory
```bash
# Append the global memory seed to your user-level instructions
cat MEMORY.md >> ~/.claude/CLAUDE.md
```
`~/.claude/CLAUDE.md` is loaded at the start of every session in every project,
so this pre-loads engineering wisdom everywhere.

### 5. Use the session protocol
Read `session-protocol.md` to understand how to start, manage, and end sessions to maximize knowledge retention.

### 6. Adopt the working charter
```bash
cp WORKING-CHARTER.md /path/to/your-project/WORKING-CHARTER.md
```
`WORKING-CHARTER.md` is the standing agreement for every session: the pre-execution checks, how answers are phrased, when to ask instead of decide, the skill vetting rule, and the four-stage quality gate that wakes only for real code changes. Fill in its **Standing Constraints** section per project.

---

## Repository Structure

```
claude-code-generic-guide/
│
├── AGENTS.md                    ← Master AI behavior rules (copy to your project)
├── CLAUDE.md                    ← Import bridge: how Claude Code loads AGENTS.md
├── MEMORY.md                    ← Global memory seed template
├── session-protocol.md          ← How to manage sessions for knowledge persistence
├── WORKING-CHARTER.md           ← Standing operating agreement: how the AI thinks, talks, and gates code
│
├── .claude/                     ← AI tooling configuration
│   ├── config.toml              ← Illustrative settings reference (Claude Code reads settings.json)
│   ├── settings.json            ← Hook registration (SessionStart, PreCompact, SessionEnd)
│   ├── skills/                  ← 17 reusable skill workflows
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
│   │   ├── security-review/     ← Security audit
│   │   ├── code-generation/     ← Production-ready code generation
│   │   ├── flush/               ← Session summary to memory log
│   │   ├── dream/               ← Memory consolidation
│   │   └── skillify/            ← Workflow capture as new skill
│   └── hooks/                   ← Session lifecycle hooks
│
├── knowledge-base/              ← Seeded engineering wisdom (patterns, principles, pitfalls)
├── tools/                       ← validate.py — the repo's CI quality gate
├── .github/workflows/           ← CI: runs the validator on every PR
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
| `code-generation` | `/code-generation` | Production-ready implementation with critic pass |
| `flush` | `/flush` | Structured session summary written to the memory log |
| `dream` | `/dream` | Consolidate session logs into the knowledge base |
| `skillify` | `/skillify` | Capture a completed workflow as a new skill |
| `reconcile-docs` | `/reconcile-docs` | One home per rule: merge duplicated statements across docs |

---

## Knowledge Persistence System

The knowledge system has three layers:

### 1. Automatic (built-in)
- Auto memory: Claude writes and recalls per-project notes in `~/.claude/projects/<project>/memory/`; the index loads every session
- `CLAUDE.md` (importing `AGENTS.md`) and `~/.claude/CLAUDE.md` load every session
- Pre-compaction and session-end hooks fire via `.claude/settings.json`

### 2. Semi-automatic (you trigger it)
- `/flush` — write an LLM-generated session summary before compacting or closing
- `/dream` — consolidate scattered session logs into organized topics (run weekly)
- `learn` skill — capture a specific pattern or decision

### 3. Manual (curated)
- `MEMORY.md` in the repo — the seed you append to `~/.claude/CLAUDE.md`
- `~/.claude/CLAUDE.md` — global engineering principles, loaded every session
- Knowledge base entries in `knowledge-base/entries/`

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

Full 22-chapter documentation in `/docs/` — a snapshot mirror (see the provenance note in `docs/index.md`); for current product behavior the canonical source is https://code.claude.com/docs:
- Sessions, memory, skills, agents, MCP servers, plugins, hooks, and more
- See `docs/index.md` for the full table of contents

---

## Philosophy

> Every session should be smarter than the last.

This infrastructure is built around one principle: **knowledge should compound**. Each debugging session, architecture decision, and discovered pattern is an asset. The goal is to make the AI's context richer over time — so that by month 3, it starts sessions knowing the project's architecture, conventions, and history, rather than starting from scratch every time.

